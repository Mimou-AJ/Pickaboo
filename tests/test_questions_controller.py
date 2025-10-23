import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import status

from src.questions.controller import router
from src.questions.models import SuggestedQuestion


@pytest.fixture
def mock_question_service():
    """Mock QuestionService for controller tests"""
    return Mock()


@pytest.fixture
def sample_questions_response():
    """Sample response from question service"""
    return [
        {
            "id": uuid4(),
            "question": "Does he prefer indoor or outdoor activities?",
            "choices": ["Indoor activities", "Outdoor activities", "Both equally"]
        },
        {
            "id": uuid4(),
            "question": "Is he more practical or creative?",
            "choices": ["Practical", "Creative", "Balanced mix"]
        }
    ]


@pytest.mark.skip(reason="Controller tests require PostgreSQL for UUID support - SQLite doesn't support UUID columns")
class TestQuestionsController:
    
    @patch('src.questions.controller.get_question_service')
    def test_get_next_question_success(
        self, mock_get_service, mock_question_service, 
        sample_questions_response, client
    ):
        """Test successful retrieval of next questions"""
        # Setup mocks
        mock_get_service.return_value = mock_question_service
        mock_question_service.get_questions.return_value = sample_questions_response
        
        persona_id = uuid4()
        
        # Make request
        response = client.get(f"/personas/{persona_id}/questions")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data) == 2
        
        # Verify first question structure
        first_question = data[0]
        assert "id" in first_question
        assert first_question["question"] == "Does he prefer indoor or outdoor activities?"
        assert first_question["choices"] == ["Indoor activities", "Outdoor activities", "Both equally"]
        
        # Verify second question structure
        second_question = data[1]
        assert "id" in second_question
        assert first_question["question"] == "Does he prefer indoor or outdoor activities?"
        assert second_question["choices"] == ["Practical", "Creative", "Balanced mix"]
        
        # Verify service was called correctly
        mock_question_service.get_questions.assert_called_once_with(persona_id)

    @patch('src.questions.controller.get_question_service')
    def test_get_next_question_empty_response(
        self, mock_get_service, mock_question_service, 
        client
    ):
        """Test when service returns no questions"""
        # Setup mocks
        mock_get_service.return_value = mock_question_service
        mock_question_service.get_questions.return_value = []
        
        persona_id = uuid4()
        
        # Make request
        response = client.get(f"/personas/{persona_id}/questions")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    @patch('src.questions.controller.get_question_service')
    def test_get_next_question_invalid_persona_id(
        self, mock_get_service, mock_question_service, 
        client
    ):
        """Test with invalid persona ID format"""
        # Setup mocks
        mock_get_service.return_value = mock_question_service
        
        # Make request with invalid UUID
        response = client.get("/personas/invalid-uuid/questions")
        
        # Should return 422 for invalid UUID format
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('src.questions.controller.get_question_service')
    def test_get_next_question_service_exception(
        self, mock_get_service, mock_question_service, 
        client
    ):
        """Test when service raises an exception"""
        # Setup mocks
        mock_get_service.return_value = mock_question_service
        mock_question_service.get_questions.side_effect = Exception("Database error")
        
        persona_id = uuid4()
        
        # Make request
        response = client.get(f"/personas/{persona_id}/questions")
        
        # Should return 500 for internal server error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_suggested_question_model_validation(self):
        """Test SuggestedQuestion pydantic model validation"""
        # Valid data
        valid_data = {
            "id": uuid4(),
            "question": "What's his favorite hobby?",
            "choices": ["Reading", "Gaming", "Sports"]
        }
        
        question = SuggestedQuestion(**valid_data)
        assert question.id == valid_data["id"]
        assert question.question == valid_data["question"]
        assert question.choices == valid_data["choices"]

    def test_suggested_question_model_missing_fields(self):
        """Test SuggestedQuestion validation with missing fields"""
        with pytest.raises(ValueError):
            SuggestedQuestion(id=uuid4())  # Missing question and choices
        
        with pytest.raises(ValueError):
            SuggestedQuestion(
                id=uuid4(),
                question="Test question"
                # Missing choices
            )

    def test_suggested_question_model_invalid_types(self):
        """Test SuggestedQuestion validation with invalid field types"""
        with pytest.raises(ValueError):
            SuggestedQuestion(
                id="not-a-uuid",  # Should be UUID
                question="Test question",
                choices=["Choice 1", "Choice 2"]
            )
        
        with pytest.raises(ValueError):
            SuggestedQuestion(
                id=uuid4(),
                question=123,  # Should be string
                choices=["Choice 1", "Choice 2"]
            )
        
        with pytest.raises(ValueError):
            SuggestedQuestion(
                id=uuid4(),
                question="Test question",
                choices="not-a-list"  # Should be list
            )