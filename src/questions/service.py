from ..database.core import DbSession
from ..build_persona.entity import Persona
from .entity import Question, Answer
from .models import QuestionResponse, AnswerResponse, BulkAnswerRequest, BulkAnswerResponse
import uuid
from typing import List, Dict
import asyncio

from ..questions_agent.detective import gift_detective, get_initial_system_prompt, get_followup_prompt
from ..questions_agent.models import GiftDependencies
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart
from pydantic_ai import ModelMessagesTypeAdapter
from ..messages.repository import MessageRepository


class QuestionService:
    def __init__(self, session):
        self.session = session
        self.message_repo = MessageRepository(session)

    def get_questions(self, persona_id: uuid.UUID) -> List[Dict]:
        persona = self.session.query(Persona).filter(Persona.id == persona_id).one()

        # Format budget for display
        budget_display = None
        if persona.budget:
            budget_map = {
                "under_25": "Under 25€",
                "25-50": "25-50€",
                "50-100": "50-100€",
                "over_100": "Over 100€"
            }
            budget_display = budget_map.get(persona.budget.value, persona.budget.value)

        # Load message history using the repository
        message_history = asyncio.run(self.message_repo.load_all_messages(persona_id))

        deps = GiftDependencies(
            age=persona.age,
            gender=persona.gender.value if persona.gender else "unknown",
            occasion=persona.occasion.value,
            relationship=persona.relationship.value,
            budget=budget_display,
        )

        # Use different prompts based on whether we have message history
        if message_history:
            # Follow-up questions: history already contains context, just ask for more questions
            prompt = get_followup_prompt()
        else:
            # Initial questions: include full system prompt with profile
            prompt = get_initial_system_prompt(deps)

        # Use native Pydantic AI message_history parameter
        result = asyncio.run(
            gift_detective.run(prompt, deps=deps, message_history=message_history)
        )

        # Store the new messages (both request and response)
        asyncio.run(self.message_repo.store_messages(
            persona_id, 
            result.new_messages_json()
        ))

        # Save each question to DB and return structured items with choices
        items: List[Dict] = []
        for q in result.output.questions:
            # q.question is the text, q.choices is List[str]
            question = Question(
                persona_id=persona_id,
                question_text=q.question,
                choices=q.choices,  # Save the choices as JSON
            )
            self.session.add(question)
            self.session.commit()
            self.session.refresh(question)

            items.append({
                "id": question.id,
                "question": question.question_text,
                "choices": q.choices,
            })

        return items

    def get_next_question(self, persona_id: uuid.UUID) -> List[Dict]:
        """Backward-compatible alias for get_questions."""
        return self.get_questions(persona_id)

    def submit_bulk_answers(self, request: BulkAnswerRequest) -> BulkAnswerResponse:
        """Submit multiple answers for different questions in one operation"""
        submitted_answers = []
        user_messages: List[ModelMessage] = []
        
        for answer_item in request.answers:
            # Verify the question exists
            question = self.session.query(Question).filter(Question.id == answer_item.question_id).first()
            if not question:
                continue  # Skip invalid question IDs
            
            # Get the selected choice text
            selected_text = answer_item.answer_choice
            
            # Create message pair for history (agent asked, user answered)
            user_messages.append(
                ModelRequest(parts=[UserPromptPart(content=question.question_text)])
            )
            user_messages.append(
                ModelResponse(parts=[TextPart(content=selected_text)])
            )
            
            # Create and save the answer
            answer = Answer(
                question_id=answer_item.question_id,
                selected_choice_text=selected_text
            )
            self.session.add(answer)
            self.session.commit()
            self.session.refresh(answer)
            
            submitted_answers.append(AnswerResponse(
                id=answer.id,
                selected_choice=answer.selected_choice_text
            ))
        
        # Store the user's answers in message history
        if user_messages:
            # Get persona_id from the first question
            first_question = self.session.query(Question).filter(
                Question.id == request.answers[0].question_id
            ).first()
            if first_question:
                asyncio.run(self.message_repo.store_messages(
                    first_question.persona_id,
                    ModelMessagesTypeAdapter.dump_json(user_messages)
                ))
        
        return BulkAnswerResponse(
            submitted_count=len(submitted_answers),
            answers=submitted_answers
        )
    
def get_question_service(session: DbSession) -> QuestionService:
    return QuestionService(session)
