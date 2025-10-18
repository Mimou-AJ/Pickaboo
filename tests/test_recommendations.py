import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from src.recommendations.service import RecommendationService
from src.recommendations.models import RecommendationRequest, PersonaProfile, QuestionInsight
from src.build_persona.entity import Persona, Gender, Occasion, Relationship
from src.questions.entity import Question, Answer
from src.questions.answer_choice import AnswerChoice

class TestRecommendationService:
    """Test the recommendation service functionality"""
    
    @pytest.fixture
    def mock_session(self):
        return Mock()
    
    @pytest.fixture
    def service(self, mock_session):
        return RecommendationService(mock_session)
    
    @pytest.fixture
    def sample_persona(self):
        persona = Mock(spec=Persona)
        persona.id = uuid4()
        persona.name = "Alex"
        persona.age = 25
        persona.gender = Gender.male
        persona.occasion = Occasion.birthday
        persona.relationship = Relationship.friend
        return persona
    
    @pytest.fixture
    def sample_questions_answers(self):
        """Sample questions with answers"""
        q1 = Mock(spec=Question)
        q1.question_text = "What type of activities do you enjoy?"
        q1.choices = ["Gaming", "Sports", "Reading"]
        
        a1 = Mock(spec=Answer)
        a1.selected_choice_text = "Gaming"
        a1.answer_choice = AnswerChoice.yes
        
        q2 = Mock(spec=Question)
        q2.question_text = "What's your preferred style?"
        q2.choices = ["Casual", "Formal", "Trendy"]
        
        a2 = Mock(spec=Answer)
        a2.selected_choice_text = "Casual"
        a2.answer_choice = AnswerChoice.probably
        
        return [(q1, a1), (q2, a2)]
    
    def test_build_persona_profile(self, service, mock_session, sample_persona, sample_questions_answers):
        """Test building complete persona profile"""
        # Mock database queries
        mock_session.query.return_value.filter.return_value.first.return_value = sample_persona
        mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = sample_questions_answers
        
        # Build profile
        profile = service._build_persona_profile(sample_persona.id)
        
        # Verify profile structure
        assert isinstance(profile, PersonaProfile)
        assert profile.age == 25
        assert profile.gender == "male"
        assert profile.occasion == "birthday"
        assert profile.relationship == "friend"
        
        # Verify question insights
        assert len(profile.question_insights) == 2
        
        first_insight = profile.question_insights[0]
        assert first_insight.question == "What type of activities do you enjoy?"
        assert first_insight.selected_choice == "Gaming"
        assert first_insight.available_choices == ["Gaming", "Sports", "Reading"]
        assert first_insight.insight_category == "interests"
        
        second_insight = profile.question_insights[1]
        assert second_insight.question == "What's your preferred style?"
        assert second_insight.selected_choice == "Casual"
        assert second_insight.available_choices == ["Casual", "Formal", "Trendy"]
        assert second_insight.insight_category == "style"
    
    def test_categorize_question(self, service):
        """Test question categorization logic"""
        
        assert service._categorize_question("What hobby do you enjoy most?") == "interests"
        assert service._categorize_question("What's your fashion style?") == "style"
        assert service._categorize_question("What type of food do you like?") == "lifestyle"
        assert service._categorize_question("What music do you listen to?") == "entertainment"
        assert service._categorize_question("Where do you like to travel?") == "travel"
        assert service._categorize_question("What's your favorite color?") == "preferences"
    
    def test_calculate_confidence_level(self, service):
        """Test confidence level calculation"""
        from src.recommendations.models import GiftRecommendation
        
        # High confidence recommendations
        high_conf_recs = [
            Mock(spec=GiftRecommendation, confidence_score=0.9),
            Mock(spec=GiftRecommendation, confidence_score=0.8),
            Mock(spec=GiftRecommendation, confidence_score=0.85)
        ]
        
        # Test with good data coverage (5 insights)
        confidence = service._calculate_confidence_level(high_conf_recs, 5)
        assert confidence == "high"
        
        # Test with medium confidence scores
        med_conf_recs = [
            Mock(spec=GiftRecommendation, confidence_score=0.7),
            Mock(spec=GiftRecommendation, confidence_score=0.6),
            Mock(spec=GiftRecommendation, confidence_score=0.65)
        ]
        
        confidence = service._calculate_confidence_level(med_conf_recs, 3)
        assert confidence == "medium"
        
        # Test with low confidence or little data
        low_conf_recs = [
            Mock(spec=GiftRecommendation, confidence_score=0.4),
            Mock(spec=GiftRecommendation, confidence_score=0.3)
        ]
        
        confidence = service._calculate_confidence_level(low_conf_recs, 1)
        assert confidence == "low"
    
    def test_build_recipient_summary(self, service):
        """Test recipient summary generation"""
        
        insights = [
            Mock(question="What activities do you enjoy?", selected_choice="Gaming", insight_category="interests"),
            Mock(question="What's your style?", selected_choice="Casual", insight_category="style"),
            Mock(question="What food do you like?", selected_choice="Italian", insight_category="lifestyle")
        ]
        
        profile = Mock(spec=PersonaProfile)
        profile.age = 25
        profile.gender = "male"
        profile.question_insights = insights
        
        summary = service._build_recipient_summary(profile)
        
        assert "The recipient is a 25-year-old male" in summary
        assert "Gaming" in summary
        assert "Casual" in summary
        assert "Italian" in summary

class TestRecommendationModels:
    """Test the recommendation data models"""
    
    def test_persona_profile_creation(self):
        """Test creating PersonaProfile with all fields"""
        
        insights = [
            QuestionInsight(
                question="What do you like?",
                selected_choice="Gaming",
                available_choices=["Gaming", "Sports", "Reading"],
                insight_category="interests"
            )
        ]
        
        profile = PersonaProfile(
            persona_id=uuid4(),
            age=30,
            gender="female",
            occasion="birthday",
            relationship="friend",
            question_insights=insights
        )
        

        assert len(profile.question_insights) == 1
        assert profile.question_insights[0].selected_choice == "Gaming"
    
    def test_recommendation_request_defaults(self):
        """Test RecommendationRequest default values"""
        
        request = RecommendationRequest(persona_id=uuid4())
        
        assert request.max_recommendations == 5
        assert request.include_reasoning == True