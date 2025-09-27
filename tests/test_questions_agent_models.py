import pytest
from unittest.mock import Mock
from pydantic import ValidationError

from src.questions_agent.models import GiftDependencies, GiftQuestions


class TestGiftDependencies:
    """Test the GiftDependencies model used for agent input"""
    
    def test_valid_gift_dependencies(self):
        """Test creating GiftDependencies with valid data"""
        deps = GiftDependencies(
            age=25,
            gender="male",
            occasion="birthday",
            relationship="friend"
        )
        
        assert deps.age == 25
        assert deps.gender == "male"
        assert deps.occasion == "birthday"
        assert deps.relationship == "friend"

    def test_gift_dependencies_age_validation(self):
        """Test age validation in GiftDependencies"""
        # Valid ages
        deps1 = GiftDependencies(age=1, gender="male", occasion="birthday", relationship="friend")
        assert deps1.age == 1
        
        deps2 = GiftDependencies(age=100, gender="female", occasion="christmas", relationship="parent")
        assert deps2.age == 100
        
        # Invalid age types should be caught by pydantic
        with pytest.raises(ValidationError):
            GiftDependencies(age="twenty-five", gender="male", occasion="birthday", relationship="friend")

    def test_gift_dependencies_required_fields(self):
        """Test that all fields are required"""
        with pytest.raises(ValidationError):
            GiftDependencies(age=25)  # Missing other fields
        
        with pytest.raises(ValidationError):
            GiftDependencies(gender="male", occasion="birthday", relationship="friend")  # Missing age

    def test_gift_dependencies_empty_strings(self):
        """Test handling of empty string values"""
        # Empty strings should be allowed for gender (unknown case)
        deps = GiftDependencies(
            age=25,
            gender="",
            occasion="birthday",
            relationship="friend"
        )
        assert deps.gender == ""


class TestGiftQuestions:
    """Test the GiftQuestions model used for agent output"""
    
    def test_valid_gift_questions(self):
        """Test creating GiftQuestions with valid structure"""
        from src.questions_agent.models import GiftQuestions
        
        # Create actual question items
        question_item_1 = GiftQuestions.QuestionItem(
            question="Does he prefer practical gifts?",
            choices=["Yes", "No", "Sometimes"]
        )
        
        question_item_2 = GiftQuestions.QuestionItem(
            question="Is he into technology?",
            choices=["Very much", "Somewhat", "Not really"]
        )
        
        gift_questions = GiftQuestions(
            questions=[question_item_1, question_item_2],
            detective_comment="These questions help narrow down gift preferences."
        )
        
        assert len(gift_questions.questions) == 2
        assert gift_questions.detective_comment == "These questions help narrow down gift preferences."

    def test_empty_questions_list(self):
        """Test GiftQuestions with empty questions list"""
        gift_questions = GiftQuestions(
            questions=[],
            detective_comment="No specific questions needed."
        )
        
        assert len(gift_questions.questions) == 0
        assert gift_questions.detective_comment == "No specific questions needed."

    def test_gift_questions_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValidationError):
            GiftQuestions(questions=[])  # Missing detective_comment
        
        with pytest.raises(ValidationError):
            GiftQuestions(detective_comment="Test comment")  # Missing questions


class TestQuestionItem:
    """Test the nested QuestionItem model"""
    
    def test_valid_question_item(self):
        """Test creating a valid QuestionItem"""
        from src.questions_agent.models import GiftQuestions
        
        question_item = GiftQuestions.QuestionItem(
            question="Does he enjoy outdoor activities?",
            choices=["Yes, loves them", "Occasionally", "Prefers indoor"]
        )
        
        assert question_item.question == "Does he enjoy outdoor activities?"
        assert len(question_item.choices) == 3
        assert question_item.choices[0] == "Yes, loves them"

    def test_question_item_alias_support(self):
        """Test that QuestionItem accepts 'queation' as alias for 'question'"""
        from src.questions_agent.models import GiftQuestions
        
        # Should accept both 'question' and 'queation'
        question_item = GiftQuestions.QuestionItem(
            queation="Does he like books?",  # Using the alias
            choices=["Fiction", "Non-fiction", "Not really"]
        )
        
        # Should be accessible as 'question' regardless of input key
        assert question_item.question == "Does he like books?"

    def test_choices_validation_and_cleaning(self):
        """Test the choices field validation and cleaning"""
        from src.questions_agent.models import GiftQuestions
        
        # Test with various inputs that should be cleaned
        question_item = GiftQuestions.QuestionItem(
            question="Test question?",
            choices=[
                "Choice one.",  # Has trailing period
                "Choice two!",  # Has trailing exclamation
                "Choice three",  # Clean
                "choice one.",  # Duplicate (different case)
                "",  # Empty string
                "Choice four?",  # Has trailing question mark
                "Choice five"  # Extra choice beyond 3
            ]
        )
        
        # Should have exactly 3 choices, cleaned and deduplicated
        assert len(question_item.choices) == 3
        
        # Should remove trailing punctuation
        choices = question_item.choices
        assert all("." not in choice[-1:] if choice else True for choice in choices)
        assert all("!" not in choice[-1:] if choice else True for choice in choices)
        assert all("?" not in choice[-1:] if choice else True for choice in choices)

    def test_choices_padding_with_defaults(self):
        """Test that choices are padded to 3 with defaults if needed"""
        from src.questions_agent.models import GiftQuestions
        
        # Provide only 1 choice
        question_item = GiftQuestions.QuestionItem(
            question="Test question?",
            choices=["Only choice"]
        )
        
        # Should be padded to 3 choices
        assert len(question_item.choices) == 3
        assert "Only choice" in question_item.choices
        
        # Should include default options
        defaults_present = any(default in question_item.choices for default in ["Yes", "Maybe", "No"])
        assert defaults_present

    def test_choices_non_list_input(self):
        """Test choices validation with non-list input"""
        from src.questions_agent.models import GiftQuestions
        
        # Non-list input should default to ["Yes", "Maybe", "No"]
        question_item = GiftQuestions.QuestionItem(
            question="Test question?",
            choices="not a list"
        )
        
        assert len(question_item.choices) == 3
        assert question_item.choices == ["Yes", "Maybe", "No"]

    def test_empty_choices_list(self):
        """Test choices validation with empty list"""
        from src.questions_agent.models import GiftQuestions
        
        question_item = GiftQuestions.QuestionItem(
            question="Test question?",
            choices=[]
        )
        
        # Should default to ["Yes", "Maybe", "No"]
        assert len(question_item.choices) == 3
        assert question_item.choices == ["Yes", "Maybe", "No"]

    def test_choices_with_non_string_items(self):
        """Test choices validation with non-string items in list"""
        from src.questions_agent.models import GiftQuestions
        
        question_item = GiftQuestions.QuestionItem(
            question="Test question?",
            choices=["Valid choice", 123, None, "Another valid choice"]
        )
        
        # Should filter out non-string items and pad with defaults
        assert len(question_item.choices) == 3
        assert "Valid choice" in question_item.choices
        assert "Another valid choice" in question_item.choices