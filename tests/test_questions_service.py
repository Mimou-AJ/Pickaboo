import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from sqlalchemy.orm import Session

from src.questions.service import QuestionService
from src.questions.entity import Question
from src.build_persona.entity import Persona, Occasion, Gender, Relationship
from src.questions_agent.models import GiftDependencies, GiftQuestions


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session"""
    return Mock(spec=Session)


@pytest.fixture
def sample_persona():
    """Sample persona for testing"""
    persona = Mock(spec=Persona)
    persona.id = uuid4()
    persona.age = 25
    persona.gender = Gender.male
    persona.occasion = Occasion.birthday
    persona.relationship = Relationship.friend
    return persona


@pytest.fixture
def sample_agent_response():
    """Sample response from the gift detective agent"""
    from src.questions_agent.models import GiftQuestions
    
    # Create mock question items
    question_item_1 = Mock()
    question_item_1.question = "Does he prefer practical gifts or fun experiences?"
    question_item_1.choices = ["Practical gifts", "Fun experiences", "Both equally"]
    
    question_item_2 = Mock()
    question_item_2.question = "Is he into tech gadgets or outdoor activities?"
    question_item_2.choices = ["Tech gadgets", "Outdoor activities", "Neither really"]
    
    # Create mock agent response
    response = Mock()
    response.output = Mock(spec=GiftQuestions)
    response.output.questions = [question_item_1, question_item_2]
    response.output.detective_comment = "These questions target his lifestyle preferences."
    
    return response


class TestQuestionService:
    def test_init(self, mock_session):
        """Test service initialization"""
        service = QuestionService(mock_session)
        assert service.session == mock_session

    @patch('src.questions.service.asyncio.run')
    @patch('src.questions.service.gift_detective.run')
    def test_get_next_question_saves_and_returns_questions(
        self, mock_agent_run, mock_asyncio_run, mock_session, sample_persona, sample_agent_response
    ):
        """Test that get_next_question saves questions to DB and returns structured response"""
        # Setup mocks
        mock_session.query.return_value.filter.return_value.one.return_value = sample_persona
        mock_asyncio_run.return_value = sample_agent_response
        
        # Mock question creation and DB operations
        saved_questions = []
        def mock_add(question):
            question.id = uuid4()  # Simulate DB generating ID
            saved_questions.append(question)
        
        mock_session.add.side_effect = mock_add
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Execute
        service = QuestionService(mock_session)
        result = service.get_next_question(sample_persona.id)
        
        # Verify agent was called with correct dependencies
        mock_asyncio_run.assert_called_once()
        
        # Verify questions were saved to DB
        assert len(saved_questions) == 2
        assert saved_questions[0].persona_id == sample_persona.id
        assert saved_questions[0].question_text == "Does he prefer practical gifts or fun experiences?"
        assert saved_questions[1].question_text == "Is he into tech gadgets or outdoor activities?"
        
        # Verify DB operations
        assert mock_session.add.call_count == 2
        assert mock_session.commit.call_count == 2
        assert mock_session.refresh.call_count == 2
        
        # Verify returned structure
        assert len(result) == 2
        
        first_item = result[0]
        assert "id" in first_item
        assert first_item["question"] == "Does he prefer practical gifts or fun experiences?"
        assert first_item["choices"] == ["Practical gifts", "Fun experiences", "Both equally"]
        
        second_item = result[1]
        assert "id" in second_item
        assert second_item["question"] == "Is he into tech gadgets or outdoor activities?"
        assert second_item["choices"] == ["Tech gadgets", "Outdoor activities", "Neither really"]

    def test_get_next_question_with_no_gender(self, mock_session, sample_agent_response):
        """Test handling persona with no gender specified"""
        # Setup persona without gender
        persona = Mock(spec=Persona)
        persona.id = uuid4()
        persona.age = 30
        persona.gender = None
        persona.occasion = Occasion.christmas
        persona.relationship = Relationship.parent
        
        mock_session.query.return_value.filter.return_value.one.return_value = persona
        
        with patch('src.questions.service.asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = sample_agent_response
            
            # Mock DB operations
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None
            
            service = QuestionService(mock_session)
            result = service.get_next_question(persona.id)
            
            # Should handle None gender gracefully
            assert len(result) == 2

    @patch('src.questions.service.asyncio.run')
    def test_agent_dependency_mapping(self, mock_asyncio_run, mock_session, sample_agent_response):
        """Test that persona attributes are correctly mapped to agent dependencies"""
        persona = Mock(spec=Persona)
        persona.id = uuid4()
        persona.age = 35
        persona.gender = Gender.female
        persona.occasion = Occasion.wedding
        persona.relationship = Relationship.colleague
        
        mock_session.query.return_value.filter.return_value.one.return_value = persona
        mock_asyncio_run.return_value = sample_agent_response
        
        # Mock DB operations
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        service = QuestionService(mock_session)
        
        with patch('src.questions.service.gift_detective.run') as mock_agent:
            mock_agent.return_value = sample_agent_response
            
            service.get_next_question(persona.id)
            
            # Verify agent was called with correct mapped dependencies
            mock_agent.assert_called_once()
            args, kwargs = mock_agent.call_args
            
            assert "deps" in kwargs
            deps = kwargs["deps"]
            assert isinstance(deps, GiftDependencies)
            assert deps.age == 35
            assert deps.gender == "female"
            assert deps.occasion == "wedding"
            assert deps.relationship == "colleague"

    def test_empty_agent_response(self, mock_session, sample_persona):
        """Test handling when agent returns no questions"""
        # Setup empty agent response
        empty_response = Mock()
        empty_response.output = Mock(spec=GiftQuestions)
        empty_response.output.questions = []
        
        mock_session.query.return_value.filter.return_value.one.return_value = sample_persona
        
        with patch('src.questions.service.asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = empty_response
            
            service = QuestionService(mock_session)
            result = service.get_next_question(sample_persona.id)
            
            assert result == []
            mock_session.add.assert_not_called()
            mock_session.commit.assert_not_called()