import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import status

from src.questions.models import BulkAnswerRequest, QuestionAnswerItem


@pytest.fixture
def mock_question_service():
    """Mock QuestionService for controller tests"""
    return Mock()


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    user = Mock()
    user.id = uuid4()
    user.email = "test@example.com"
    return user


@pytest.fixture
def sample_bulk_request():
    """Sample bulk answer request"""
    return {
        "answers": [
            {
                "question_id": str(uuid4()),
                "answer_choice": "yes"
            },
            {
                "question_id": str(uuid4()),
                "answer_choice": "probably"
            },
            {
                "question_id": str(uuid4()),
                "answer_choice": "probably_not"
            },
            {
                "question_id": str(uuid4()),
                "answer_choice": "no"
            },
            {
                "question_id": str(uuid4()),
                "answer_choice": "yes"
            }
        ]
    }


@pytest.fixture
def sample_bulk_response():
    """Sample bulk answer response from service"""
    return {
        "submitted_count": 5,
        "answers": [
            {"id": str(uuid4()), "answer_choice": "yes"},
            {"id": str(uuid4()), "answer_choice": "probably"},
            {"id": str(uuid4()), "answer_choice": "probably_not"},
            {"id": str(uuid4()), "answer_choice": "no"},
            {"id": str(uuid4()), "answer_choice": "yes"}
        ]
    }


class TestBulkAnswerController:
    """Test the bulk answer submission controller endpoint"""
    
    @patch('src.questions.controller.get_current_user')
    @patch('src.questions.controller.get_question_service')
    def test_submit_bulk_answers_success(
        self, mock_get_service, mock_get_user, mock_question_service, 
        mock_current_user, sample_bulk_request, sample_bulk_response, client
    ):
        """Test successful bulk answer submission"""
        # Setup mocks
        mock_get_service.return_value = mock_question_service
        mock_get_user.return_value = mock_current_user
        mock_question_service.submit_bulk_answers.return_value = sample_bulk_response
        
        # Make request
        response = client.post("/questions/answers", json=sample_bulk_request)
        
        # Verify response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["submitted_count"] == 5
        assert len(data["answers"]) == 5
        
        # Verify all answers have IDs and correct choices
        expected_choices = ["yes", "probably", "probably_not", "no", "yes"]
        for i, answer in enumerate(data["answers"]):
            assert "id" in answer
            assert answer["answer_choice"] == expected_choices[i]
        
        # Verify service was called correctly
        mock_question_service.submit_bulk_answers.assert_called_once()
        call_args = mock_question_service.submit_bulk_answers.call_args[0][0]
        assert len(call_args.answers) == 5

    @patch('src.questions.controller.get_current_user')
    @patch('src.questions.controller.get_question_service')
    def test_submit_single_answer_via_bulk_endpoint(
        self, mock_get_service, mock_get_user, mock_question_service, 
        mock_current_user, client
    ):
        """Test submitting a single answer via the bulk endpoint"""
        # Setup single answer request
        single_request = {
            "answers": [
                {
                    "question_id": str(uuid4()),
                    "answer_choice": "probably"
                }
            ]
        }
        
        single_response = {
            "submitted_count": 1,
            "answers": [
                {"id": str(uuid4()), "answer_choice": "probably"}
            ]
        }
        
        # Setup mocks
        mock_get_service.return_value = mock_question_service
        mock_get_user.return_value = mock_current_user
        mock_question_service.submit_bulk_answers.return_value = single_response
        
        # Make request
        response = client.post("/questions/answers", json=single_request)
        
        # Verify response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["submitted_count"] == 1
        assert len(data["answers"]) == 1
        assert data["answers"][0]["answer_choice"] == "probably"

    @patch('src.questions.controller.get_current_user')
    @patch('src.questions.controller.get_question_service')
    def test_submit_empty_answers_list(
        self, mock_get_service, mock_get_user, mock_question_service, 
        mock_current_user, client
    ):
        """Test submitting empty answers list"""
        empty_request = {"answers": []}
        empty_response = {"submitted_count": 0, "answers": []}
        
        # Setup mocks
        mock_get_service.return_value = mock_question_service
        mock_get_user.return_value = mock_current_user
        mock_question_service.submit_bulk_answers.return_value = empty_response
        
        # Make request
        response = client.post("/questions/answers", json=empty_request)
        
        # Verify response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["submitted_count"] == 0
        assert len(data["answers"]) == 0

    def test_submit_answers_invalid_json(self, client):
        """Test submitting invalid JSON structure"""
        invalid_request = {
            "wrong_field": "wrong_value"
        }
        
        response = client.post("/questions/answers", json=invalid_request)
        
        # Should return 422 for validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_submit_answers_invalid_answer_choice(self, client):
        """Test submitting invalid answer choice"""
        invalid_request = {
            "answers": [
                {
                    "question_id": str(uuid4()),
                    "answer_choice": "invalid_choice"
                }
            ]
        }
        
        response = client.post("/questions/answers", json=invalid_request)
        
        # Should return 422 for validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_submit_answers_invalid_uuid(self, client):
        """Test submitting invalid question ID format"""
        invalid_request = {
            "answers": [
                {
                    "question_id": "not-a-uuid",
                    "answer_choice": "yes"
                }
            ]
        }
        
        response = client.post("/questions/answers", json=invalid_request)
        
        # Should return 422 for validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_submit_answers_unauthenticated(self, client):
        """Test bulk answer submission without authentication"""
        request_data = {
            "answers": [
                {
                    "question_id": str(uuid4()),
                    "answer_choice": "yes"
                }
            ]
        }
        
        # Make request without auth headers
        response = client.post("/questions/answers", json=request_data)
        
        # Should return 401 or 403 for authentication error
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @patch('src.questions.controller.get_current_user')
    @patch('src.questions.controller.get_question_service')
    def test_submit_answers_service_exception(
        self, mock_get_service, mock_get_user, mock_question_service, 
        mock_current_user, sample_bulk_request, client
    ):
        """Test handling service exceptions during bulk submission"""
        # Setup mocks to raise exception
        mock_get_service.return_value = mock_question_service
        mock_get_user.return_value = mock_current_user
        mock_question_service.submit_bulk_answers.side_effect = Exception("Database error")
        
        # Make request
        response = client.post("/questions/answers", json=sample_bulk_request)
        
        # Should return 500 for internal server error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestAnswerTextValidation:
    """Test answer text validation in different scenarios"""
    
    def test_all_valid_answer_choices(self):
        """Test that various answer choice texts work in requests"""
        valid_choices = ["Yes", "Probably", "Probably not", "No", "Maybe", "Definitely"]
        
        for choice in valid_choices:
            item = QuestionAnswerItem(
                question_id=uuid4(),
                answer_choice=choice
            )
            assert item.answer_choice == choice

    def test_answer_choice_case_sensitivity(self):
        """Test answer choice validation is case sensitive"""
        with pytest.raises(ValueError):
            QuestionAnswerItem(
                question_id=uuid4(),
                answer_choice="YES"  # Should be lowercase "yes"
            )

    def test_bulk_request_with_mixed_choices(self):
        """Test bulk request with all different answer choices"""
        items = [
            QuestionAnswerItem(question_id=uuid4(), answer_choice="yes"),
            QuestionAnswerItem(question_id=uuid4(), answer_choice="probably"),
            QuestionAnswerItem(question_id=uuid4(), answer_choice="probably_not"),
            QuestionAnswerItem(question_id=uuid4(), answer_choice="no"),
            QuestionAnswerItem(question_id=uuid4(), answer_choice="yes")
        ]
        
        request = BulkAnswerRequest(answers=items)
        
        assert len(request.answers) == 5
        choices = [item.answer_choice for item in request.answers]
        assert "yes" in choices
        assert "probably" in choices
        assert "probably_not" in choices
        assert "no" in choices


class TestEndpointIntegration:
    """Integration tests for the complete workflow"""
    
    @patch('src.questions.controller.get_current_user')
    @patch('src.questions.controller.get_question_service')
    def test_complete_question_answer_workflow(
        self, mock_get_service, mock_get_user, mock_question_service, 
        mock_current_user, client
    ):
        """Test the complete workflow: get questions -> submit answers"""
        persona_id = uuid4()
        
        # Mock questions response
        questions_response = [
            {
                "id": str(uuid4()),
                "question": "Does he prefer indoor activities?",
                "choices": ["Yes", "No", "Sometimes"]
            },
            {
                "id": str(uuid4()),
                "question": "Is he tech-savvy?",
                "choices": ["Very much", "Somewhat", "Not really"]
            }
        ]
        
        # Mock answer response
        answer_response = {
            "submitted_count": 2,
            "answers": [
                {"id": str(uuid4()), "answer_choice": "yes"},
                {"id": str(uuid4()), "answer_choice": "probably"}
            ]
        }
        
        # Setup mocks
        mock_get_service.return_value = mock_question_service
        mock_get_user.return_value = mock_current_user
        mock_question_service.get_next_question.return_value = questions_response
        mock_question_service.submit_bulk_answers.return_value = answer_response
        
        # Step 1: Get questions
        questions_resp = client.get(f"/personas/{persona_id}/questions/next")
        assert questions_resp.status_code == status.HTTP_200_OK
        questions_data = questions_resp.json()
        assert len(questions_data) == 2
        
        # Step 2: Submit answers using question IDs
        answer_request = {
            "answers": [
                {
                    "question_id": questions_data[0]["id"],
                    "answer_choice": "yes"
                },
                {
                    "question_id": questions_data[1]["id"],
                    "answer_choice": "probably"
                }
            ]
        }
        
        answers_resp = client.post("/questions/answers", json=answer_request)
        assert answers_resp.status_code == status.HTTP_201_CREATED
        answers_data = answers_resp.json()
        
        assert answers_data["submitted_count"] == 2
        assert len(answers_data["answers"]) == 2
        
        # Verify all answers have IDs for future reference
        for answer in answers_data["answers"]:
            assert "id" in answer
            assert answer["answer_choice"] in ["yes", "probably"]