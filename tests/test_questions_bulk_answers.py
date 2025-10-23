import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from fastapi import HTTPException

from src.questions.service import QuestionService
from src.questions.models import BulkAnswerRequest, QuestionAnswerItem, AnswerResponse
from src.questions.entity import Question, Answer


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session"""
    return Mock()


@pytest.fixture
def sample_questions():
    """Sample questions for testing bulk answers"""
    questions = []
    for i in range(5):
        question = Mock()
        question.id = uuid4()
        question.question_text = f"Sample question {i+1}?"
        questions.append(question)
    return questions


class TestBulkAnswerSubmission:
    
    def test_submit_bulk_answers_success(self, mock_session, sample_questions):
        """Test successful submission of multiple answers"""
        # Setup mock session to return questions when queried
        def mock_query_filter_first(question_id):
            # Return the matching question or None
            for q in sample_questions:
                if str(q.id) == str(question_id):
                    return q
            return None
        
        mock_session.query.return_value.filter.return_value.first.side_effect = lambda: mock_query_filter_first(mock_session.query.return_value.filter.call_args[0][0] == Question.id)
        
        # Create bulk answer request
        answer_items = []
        for i, question in enumerate(sample_questions):
            answer_items.append(QuestionAnswerItem(
                question_id=question.id,
                answer_choice="Yes" if i % 2 == 0 else "No"
            ))
        
        bulk_request = BulkAnswerRequest(answers=answer_items)
        
        # Mock the session operations
        saved_answers = []
        def mock_add(answer):
            answer.id = uuid4()  # Simulate DB generating ID
            saved_answers.append(answer)
        
        mock_session.add.side_effect = mock_add
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Mock query to return questions
        def mock_query_side_effect(*args):
            mock_query = Mock()
            mock_filter = Mock()
            
            def mock_filter_side_effect(*filter_args):
                # Return the question if it exists in our sample
                for q in sample_questions:
                    if hasattr(filter_args[0], 'right') and filter_args[0].right.value == q.id:
                        mock_filter.first.return_value = q
                        return mock_filter
                mock_filter.first.return_value = None
                return mock_filter
            
            mock_query.filter.side_effect = mock_filter_side_effect
            return mock_query
        
        mock_session.query.side_effect = mock_query_side_effect
        
        # Execute
        service = QuestionService(mock_session)
        result = service.submit_bulk_answers(bulk_request)
        
        # Verify response
        assert result.submitted_count == len(sample_questions)
        assert len(result.answers) == len(sample_questions)
        
        # Verify all answers have IDs and correct choices
        for i, answer_response in enumerate(result.answers):
            assert answer_response.id is not None
            expected_choice = "Yes" if i % 2 == 0 else "No"
            assert answer_response.selected_choice == expected_choice

    def test_submit_bulk_answers_with_invalid_questions(self, mock_session):
        """Test bulk submission with some invalid question IDs"""
        # Setup - only first question exists
        valid_question_id = uuid4()
        invalid_question_id = uuid4()
        
        valid_question = Mock()
        valid_question.id = valid_question_id
        
        def mock_query_side_effect(*args):
            mock_query = Mock()
            mock_filter = Mock()
            
            def mock_filter_side_effect(*filter_args):
                # Only return the valid question
                if hasattr(filter_args[0], 'right') and filter_args[0].right.value == valid_question_id:
                    mock_filter.first.return_value = valid_question
                else:
                    mock_filter.first.return_value = None
                return mock_filter
            
            mock_query.filter.side_effect = mock_filter_side_effect
            return mock_query
        
        mock_session.query.side_effect = mock_query_side_effect
        
        # Create request with valid and invalid question IDs
        answer_items = [
            QuestionAnswerItem(question_id=valid_question_id, answer_choice="Yes"),
            QuestionAnswerItem(question_id=invalid_question_id, answer_choice="No")
        ]
        bulk_request = BulkAnswerRequest(answers=answer_items)
        
        # Mock session operations
        def mock_add(answer):
            answer.id = uuid4()
        
        mock_session.add.side_effect = mock_add
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Execute
        service = QuestionService(mock_session)
        result = service.submit_bulk_answers(bulk_request)
        
        # Should only process valid question
        assert result.submitted_count == 1
        assert len(result.answers) == 1
        assert result.answers[0].selected_choice == "Yes"

    def test_submit_bulk_answers_empty_request(self, mock_session):
        """Test bulk submission with empty answers list"""
        bulk_request = BulkAnswerRequest(answers=[])
        
        service = QuestionService(mock_session)
        result = service.submit_bulk_answers(bulk_request)
        
        assert result.submitted_count == 0
        assert len(result.answers) == 0
        mock_session.add.assert_not_called()

    




class TestAnswerModels:
    """Test the new answer-related models"""
    
    def test_question_answer_item_validation(self):
        """Test QuestionAnswerItem model validation"""
        item = QuestionAnswerItem(
            question_id=uuid4(),
            answer_choice="Probably not"
        )
        
        assert item.question_id is not None
        assert item.answer_choice == "Probably not"

    def test_bulk_answer_request_validation(self):
        """Test BulkAnswerRequest model validation"""
        items = [
            QuestionAnswerItem(question_id=uuid4(), answer_choice="Yes"),
            QuestionAnswerItem(question_id=uuid4(), answer_choice="No")
        ]
        
        request = BulkAnswerRequest(answers=items)
        
        assert len(request.answers) == 2
        assert all(isinstance(item, QuestionAnswerItem) for item in request.answers)

    def test_bulk_answer_request_empty_list(self):
        """Test BulkAnswerRequest with empty answers list"""
        request = BulkAnswerRequest(answers=[])
        
        assert len(request.answers) == 0

    def test_bulk_answer_response_structure(self):
        """Test BulkAnswerResponse model structure"""
        from src.questions.models import BulkAnswerResponse
        
        answers = [
            AnswerResponse(id=uuid4(), selected_choice="Yes"),
            AnswerResponse(id=uuid4(), selected_choice="No")
        ]
        
        response = BulkAnswerResponse(
            submitted_count=2,
            answers=answers
        )
        
        assert response.submitted_count == 2
        assert len(response.answers) == 2
        assert all(isinstance(answer, AnswerResponse) for answer in response.answers)