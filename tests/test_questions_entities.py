import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from src.questions.entity import Question, Answer


class TestQuestionEntity:
    """Test the Question SQLAlchemy model"""
    
    def test_question_creation(self):
        """Test creating a Question instance"""
        persona_id = uuid4()
        question_text = "Does he prefer books or movies?"
        
        question = Question(
            persona_id=persona_id,
            question_text=question_text
        )
        
        assert question.persona_id == persona_id
        assert question.question_text == question_text
        assert question.id is None  # Not set until saved to DB
        assert question.created_at is None  # Not set until saved to DB

    def test_question_repr(self):
        """Test Question string representation"""
        question = Question(
            persona_id=uuid4(),
            question_text="What's his favorite hobby?"
        )
        
        repr_str = repr(question)
        assert "Question" in repr_str
        assert "What's his favorite hobby?" in repr_str


class TestAnswerEntity:
    """Test the Answer SQLAlchemy model"""
    
    def test_answer_creation(self):
        """Test creating an Answer instance"""
        question_id = uuid4()
        selected_text = "Yes, definitely"
        
        answer = Answer(
            question_id=question_id,
            selected_choice_text=selected_text
        )
        
        assert answer.question_id == question_id
        assert answer.selected_choice_text == selected_text
        assert answer.id is None  # Not set until saved to DB
        assert answer.created_at is None  # Not set until saved to DB

    def test_answer_repr(self):
        """Test Answer string representation"""
        answer = Answer(
            question_id=uuid4(),
            selected_choice_text="Probably"
        )
        
        repr_str = repr(answer)
        assert "Answer" in repr_str

    def test_different_answer_texts(self):
        """Test various answer choice texts"""
        choices = ["Indoor activities", "Gaming", "Reading books", "Tech gadgets"]
        
        for choice_text in choices:
            answer = Answer(
                question_id=uuid4(),
                selected_choice_text=choice_text
            )
            assert answer.selected_choice_text == choice_text


@pytest.mark.skip(reason="SQLite doesn't support PostgreSQL UUID columns - use PostgreSQL for integration tests")
class TestDatabaseIntegration:
    """Integration tests with actual database operations"""
    
    def test_question_database_operations(self, db_session):
        """Test saving and retrieving questions from database"""
        from src.build_persona.entity import Persona, Occasion, Gender, Relationship
        
        # Create a persona (without user)
        persona = Persona(
            occasion=Occasion.birthday,
            age=25,
            gender=Gender.male,
            relationship=Relationship.friend
        )
        db_session.add(persona)
        db_session.commit()
        db_session.refresh(persona)
        
        # Create and save a question
        question = Question(
            persona_id=persona.id,
            question_text="Does he prefer indoor or outdoor activities?"
        )
        db_session.add(question)
        db_session.commit()
        db_session.refresh(question)
        
        # Verify question was saved
        assert question.id is not None
        assert question.created_at is not None
        assert question.persona_id == persona.id
        assert question.question_text == "Does he prefer indoor or outdoor activities?"
        
        # Retrieve question from database
        retrieved_question = db_session.query(Question).filter(Question.id == question.id).first()
        assert retrieved_question is not None
        assert retrieved_question.question_text == question.question_text

    def test_answer_database_operations(self, db_session):
        """Test saving and retrieving answers from database"""
        from src.build_persona.entity import Persona, Occasion, Gender, Relationship
        
        # Create persona (without user)
        persona = Persona(
            occasion=Occasion.christmas,
            age=30,
            gender=Gender.female,
            relationship=Relationship.partner
        )
        db_session.add(persona)
        db_session.commit()
        db_session.refresh(persona)
        
        # Create and save question
        question = Question(
            persona_id=persona.id,
            question_text="Does she like jewelry?"
        )
        db_session.add(question)
        db_session.commit()
        db_session.refresh(question)
        
        # Create and save answer
        answer = Answer(
            question_id=question.id,
            selected_choice_text="Probably"
        )
        db_session.add(answer)
        db_session.commit()
        db_session.refresh(answer)
        
        # Verify answer was saved
        assert answer.id is not None
        assert answer.created_at is not None
        assert answer.question_id == question.id
        assert answer.selected_choice_text == "Probably"
        
        # Retrieve answer from database
        retrieved_answer = db_session.query(Answer).filter(Answer.id == answer.id).first()
        assert retrieved_answer is not None
        assert retrieved_answer.selected_choice_text == "Probably"

    def test_question_persona_relationship(self, db_session):
        """Test the relationship between questions and personas"""
        from src.build_persona.entity import Persona, Occasion, Gender, Relationship
        
        # Create persona (without user)
        persona = Persona(
            occasion=Occasion.graduation,
            age=22,
            relationship=Relationship.sibling
        )
        db_session.add(persona)
        db_session.commit()
        db_session.refresh(persona)
        
        # Create multiple questions for the persona
        questions = [
            Question(persona_id=persona.id, question_text="Question 1"),
            Question(persona_id=persona.id, question_text="Question 2"),
            Question(persona_id=persona.id, question_text="Question 3")
        ]
        
        for question in questions:
            db_session.add(question)
        
        db_session.commit()
        
        # Retrieve all questions for the persona
        persona_questions = db_session.query(Question).filter(Question.persona_id == persona.id).all()
        
        assert len(persona_questions) == 3
        question_texts = [q.question_text for q in persona_questions]
        assert "Question 1" in question_texts
        assert "Question 2" in question_texts
        assert "Question 3" in question_texts