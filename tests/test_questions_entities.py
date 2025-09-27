import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from src.questions.entity import Question, Answer
from src.questions.answer_choice import AnswerChoice


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
        answer_choice = AnswerChoice.yes
        
        answer = Answer(
            question_id=question_id,
            answer_choice=answer_choice
        )
        
        assert answer.question_id == question_id
        assert answer.answer_choice == answer_choice
        assert answer.id is None  # Not set until saved to DB
        assert answer.created_at is None  # Not set until saved to DB

    def test_answer_repr(self):
        """Test Answer string representation"""
        answer = Answer(
            question_id=uuid4(),
            answer_choice=AnswerChoice.probably
        )
        
        repr_str = repr(answer)
        assert "Answer" in repr_str
        assert "probably" in repr_str

    def test_all_answer_choices(self):
        """Test all available answer choices"""
        choices = [AnswerChoice.yes, AnswerChoice.probably, AnswerChoice.probably_not, AnswerChoice.no]
        
        for choice in choices:
            answer = Answer(
                question_id=uuid4(),
                answer_choice=choice
            )
            assert answer.answer_choice == choice


class TestAnswerChoice:
    """Test the AnswerChoice enum"""
    
    def test_answer_choice_values(self):
        """Test that AnswerChoice has the expected values"""
        assert AnswerChoice.yes.value == "yes"
        assert AnswerChoice.probably.value == "probably"
        assert AnswerChoice.probably_not.value == "probably_not"
        assert AnswerChoice.no.value == "no"

    def test_answer_choice_string_behavior(self):
        """Test that AnswerChoice behaves as a string enum"""
        # Should be able to compare with strings
        assert AnswerChoice.yes == "yes"
        assert AnswerChoice.probably == "probably"
        assert AnswerChoice.probably_not == "probably_not"
        assert AnswerChoice.no == "no"

    def test_answer_choice_iteration(self):
        """Test iterating over AnswerChoice values"""
        choices = list(AnswerChoice)
        expected = [AnswerChoice.yes, AnswerChoice.probably, AnswerChoice.probably_not, AnswerChoice.no]
        
        assert len(choices) == 4
        assert all(choice in expected for choice in choices)


@pytest.mark.skip(reason="SQLite doesn't support PostgreSQL UUID columns - use PostgreSQL for integration tests")
class TestDatabaseIntegration:
    """Integration tests with actual database operations"""
    
    def test_question_database_operations(self, db_session):
        """Test saving and retrieving questions from database"""
        from src.build_persona.entity import Persona, Occasion, Gender, Relationship
        from src.entities.user import User
        
        # Create a user first
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="fake_hash"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create a persona
        persona = Persona(
            user_id=user.id,
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
        from src.entities.user import User
        
        # Create user and persona (setup)
        user = User(
            email="test2@example.com",
            first_name="Test",
            last_name="User2",
            password_hash="fake_hash"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        persona = Persona(
            user_id=user.id,
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
            answer_choice=AnswerChoice.probably
        )
        db_session.add(answer)
        db_session.commit()
        db_session.refresh(answer)
        
        # Verify answer was saved
        assert answer.id is not None
        assert answer.created_at is not None
        assert answer.question_id == question.id
        assert answer.answer_choice == AnswerChoice.probably
        
        # Retrieve answer from database
        retrieved_answer = db_session.query(Answer).filter(Answer.id == answer.id).first()
        assert retrieved_answer is not None
        assert retrieved_answer.answer_choice == AnswerChoice.probably

    def test_question_persona_relationship(self, db_session):
        """Test the relationship between questions and personas"""
        from src.build_persona.entity import Persona, Occasion, Gender, Relationship
        from src.entities.user import User
        
        # Setup user and persona
        user = User(
            email="test3@example.com",
            first_name="Test",
            last_name="User3",
            password_hash="fake_hash"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        persona = Persona(
            user_id=user.id,
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