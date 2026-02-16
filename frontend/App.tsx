import React, { useState } from 'react';
import { JinnyMascot } from './components/JinnyMascot';

// --- Teaser Screen (Entry point) ---
const TeaserScreen: React.FC<{ onStart: () => void; animation: string }> = ({ onStart, animation }) => {
  return (
    <div className={`flex flex-col items-center justify-center text-center p-8 w-full h-full ${animation}`}>
      <div className="flex-grow flex items-center justify-center">
        <JinnyMascot size="large" />
      </div>
      <div className="flex-shrink-0 w-full pb-8">
        <h1 className="font-figtree text-4xl md:text-5xl font-extrabold text-off-white mb-4">
          The perfect gift is just a wish away.
        </h1>
        <p className="font-satoshi text-lg md:text-xl text-off-white/80 mb-10 max-w-md mx-auto">
          Let your personal gift genie, Jinny, find it for you.
        </p>
        <button
          onClick={onStart}
          className="font-satoshi font-bold text-lg text-off-white bg-jinny-pink rounded-2xl px-10 py-4 shadow-lg shadow-jinny-pink/30 transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-jinny-pink/50 focus:outline-none focus:ring-4 focus:ring-jinny-pink focus:ring-opacity-50"
        >
          Start Your Wish
        </button>
      </div>
    </div>
  );
};

// --- Question Definition ---
interface Question {
  id: string;
  text: string;
  type: 'options' | 'slider';
  options?: string[];
  sliderConfig?: { min: number; max: number; defaultValue: number };
}

const initialQuestions: Question[] = [
  {
    id: 'relationship',
    text: "Wonderful! Let's begin. For whom is this gift?",
    type: 'options',
    options: ['Partner', 'Family', 'Friend', 'Colleague'],
  },
  {
    id: 'gender',
    text: "Got it. What is their gender?",
    type: 'options',
    options: ['Female', 'Male', 'Other'],
  },
  {
    id: 'age',
    text: "And roughly how old are they?",
    type: 'slider',
    sliderConfig: { min: 1, max: 100, defaultValue: 30 },
  },
  {
    id: 'budget',
    text: "What is your budget for this gift?",
    type: 'options',
    options: ['Under 25€', '25-50€', '50-100€', 'Over 100€'],
  },
];

// --- Age Slider Component ---
const AgeSlider: React.FC<{
  sliderConfig: { min: number; max: number; defaultValue: number };
  onConfirm: (age: number) => void;
}> = ({ sliderConfig, onConfirm }) => {
  const [age, setAge] = useState(sliderConfig.defaultValue);

  return (
    <div className="flex flex-col items-center gap-8 w-full max-w-sm animate-bubble-pop" style={{ animationDelay: '0.5s' }}>
      <div className="w-32 h-32 bg-midnight-blue/40 border-2 border-off-white/30 rounded-full flex items-center justify-center">
        <span className="font-figtree text-5xl font-bold text-off-white">{age}</span>
      </div>
      <input
        type="range"
        min={sliderConfig.min}
        max={sliderConfig.max}
        value={age}
        onChange={(e) => setAge(parseInt(e.target.value, 10))}
        className="w-full h-2 rounded-lg appearance-none cursor-pointer custom-slider"
      />
      <button
        onClick={() => onConfirm(age)}
        className="font-satoshi font-bold text-lg text-off-white bg-jinny-pink rounded-2xl px-10 py-4 shadow-lg shadow-jinny-pink/30 transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-jinny-pink/50 focus:outline-none focus:ring-4 focus:ring-jinny-pink focus:ring-opacity-50"
      >
        Next
      </button>
    </div>
  );
};


// --- Dynamic Question Screen ---
const QuestionScreen: React.FC<{
  question: Question;
  onAnswer: (questionId: string, answer: string) => void;
  animation: string;
}> = ({ question, onAnswer, animation }) => {
  return (
    <div className={`flex flex-col justify-center p-6 w-full h-full ${animation}`}>
      {/* Jinny and Chat Bubble */}
      <div className="flex items-start space-x-4 mb-8 animate-bubble-pop" style={{ animationDelay: '0.2s' }}>
        <JinnyMascot size="small" />
        <div className="relative mt-2 bg-off-white text-midnight-blue p-4 rounded-2xl rounded-bl-lg max-w-[calc(100%-80px)] shadow-lg">
          <p className="font-satoshi font-medium text-lg">{question.text}</p>
          <div className="absolute top-4 -left-2 w-0 h-0 border-r-8 border-r-off-white border-t-8 border-t-transparent border-b-8 border-b-transparent"></div>
        </div>
      </div>
      
      {/* Answer Inputs */}
      <div className="flex flex-col items-center gap-4 w-full">
        {question.type === 'slider' && question.sliderConfig ? (
          <AgeSlider
            sliderConfig={question.sliderConfig}
            onConfirm={(age) => onAnswer(question.id, age.toString())}
          />
        ) : (
          question.options?.map((option, index) => (
            <button
              key={option}
              onClick={() => onAnswer(question.id, option)}
              className="font-satoshi font-bold text-lg text-center text-off-white bg-midnight-blue/40 border-2 border-off-white/30 rounded-2xl w-full max-w-sm px-6 py-4 shadow-lg transition-all duration-300 hover:scale-105 hover:bg-jinny-pink hover:border-jinny-pink focus:outline-none focus:ring-4 focus:ring-jinny-pink focus:ring-opacity-50 animate-bubble-pop"
              style={{ animationDelay: `${0.5 + index * 0.1}s` }}
            >
              {option}
            </button>
          ))
        )}
      </div>
    </div>
  );
};


interface Recommendation {
  title: string;
  description: string;
  price_range: string;
  reasoning: string;
  confidence_score: number;
  image_url?: string;
  purchase_links?: string[];
}

const RecommendationScreen: React.FC<{ recommendations: Recommendation[]; animation: string }> = ({ recommendations, animation }) => {
  return (
    <div className={`p-6 w-full h-full overflow-y-auto ${animation}`}>
      <div className="text-center mb-8">
        <JinnyMascot size="small" />
        <h2 className="font-figtree text-3xl font-bold text-off-white mt-4">I found these perfect gifts!</h2>
      </div>
      <div className="grid grid-cols-1 gap-6 pb-8">
        {recommendations.map((rec, index) => (
          <div 
            key={index} 
            className="bg-off-white text-midnight-blue p-6 rounded-2xl shadow-xl animate-bubble-pop flex flex-col items-center"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            {/* Image (if available) */}
            {rec.image_url && (
              <div className="w-full h-48 mb-4 overflow-hidden rounded-xl bg-gray-100 flex items-center justify-center">
                <img 
                  src={rec.image_url} 
                  alt={rec.title} 
                  className="w-full h-full object-contain hover:scale-105 transition-transform duration-300"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                  }}
                />
              </div>
            )}

            <div className="w-full flex justify-between items-start mb-2">
              <h3 className="font-figtree text-xl font-bold">
                {/* Title as Link (if available) */}
                {rec.purchase_links && rec.purchase_links.length > 0 ? (
                  <a 
                    href={rec.purchase_links[0]} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="hover:text-jinny-pink transition-colors duration-200"
                  >
                    {rec.title}
                  </a>
                ) : (
                  rec.title
                )}
              </h3>
              <span className="bg-jinny-pink text-off-white text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap ml-2">
                {rec.price_range}
              </span>
            </div>
            <p className="font-satoshi text-midnight-blue/80 mb-4 text-left w-full">{rec.description}</p>
            <div className="bg-royal-blue/10 p-4 rounded-xl w-full">
              <p className="font-satoshi text-sm italic text-royal-blue">
                ✨ {rec.reasoning}
              </p>
            </div>
            {/* Call to Action Button (if link available) */}
            {rec.purchase_links && rec.purchase_links.length > 0 && (
              <a 
                href={rec.purchase_links[0]} 
                target="_blank" 
                rel="noopener noreferrer"
                className="mt-4 w-full text-center font-satoshi font-bold text-md text-off-white bg-royal-blue rounded-xl px-4 py-3 shadow-md transition-all duration-300 hover:bg-jinny-pink"
              >
                View Product
              </a>
            )}
          </div>
        ))}
      </div>
      <div className="text-center pb-8">
        <button
          onClick={() => window.location.reload()}
          className="font-satoshi font-bold text-lg text-off-white bg-royal-blue border-2 border-off-white/30 rounded-2xl px-10 py-4 shadow-lg transition-all duration-300 hover:scale-105 hover:bg-jinny-pink focus:outline-none"
        >
          Start New Wish
        </button>
      </div>
    </div>
  );
};


const DecisionScreen: React.FC<{ onMore: () => void; onShow: () => void; animation: string }> = ({ onMore, onShow, animation }) => {
  return (
    <div className={`flex flex-col items-center justify-center text-center p-8 w-full h-full ${animation}`}>
      <div className="flex-grow flex items-center justify-center">
        <JinnyMascot size="large" />
      </div>
      <div className="flex-shrink-0 w-full pb-8">
        <h1 className="font-figtree text-3xl md:text-4xl font-extrabold text-off-white mb-4">
          I have some ideas!
        </h1>
        <p className="font-satoshi text-lg md:text-xl text-off-white/80 mb-10 max-w-md mx-auto">
          Would you like to see them now, or shall I ask a few more questions to be precise?
        </p>
        <div className="flex flex-col md:flex-row gap-4 w-full justify-center">
          <button
            onClick={onShow}
            className="font-satoshi font-bold text-lg text-off-white bg-royal-blue border-2 border-off-white/30 rounded-2xl px-8 py-4 shadow-lg transition-all duration-300 hover:scale-105 hover:bg-jinny-pink focus:outline-none"
          >
            Show me the gifts
          </button>
          <button
            onClick={onMore}
            className="font-satoshi font-bold text-lg text-midnight-blue bg-off-white rounded-2xl px-8 py-4 shadow-lg transition-all duration-300 hover:scale-105 hover:bg-gray-100 focus:outline-none"
          >
            Ask me more
          </button>
        </div>
      </div>
    </div>
  );
};

const StatusScreen: React.FC<{ animation: string; title: string; message: string }> = ({ animation, title, message }) => {
  return (
    <div className={`flex flex-col items-center justify-center text-center p-8 w-full h-full ${animation}`}>
      <div className="flex-grow flex items-center justify-center">
        <JinnyMascot size="large" />
      </div>
      <div className="flex-shrink-0 w-full pb-8">
        <h1 className="font-figtree text-4xl md:text-5xl font-extrabold text-off-white mb-4">
          {title}
        </h1>
        <p className="font-satoshi text-lg md:text-xl text-off-white/80 mb-10 max-w-md mx-auto">
          {message}
        </p>
      </div>
    </div>
  );
};



// --- Main App Component ---
export default function App() {
  type Step = 'teaser' | 'exiting_teaser' | 'question' | 'loading' | 'decision' | 'finished' | 'error' | 'recommendations';
  
  const [step, setStep] = useState<Step>('teaser');
  const [currentQuestions, setCurrentQuestions] = useState<Question[]>(initialQuestions);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [animation, setAnimation] = useState('animate-fade-in');
  const [personaId, setPersonaId] = useState<string | null>(null);

  const handleStart = () => {
    setStep('exiting_teaser');
    setTimeout(() => {
      setStep('question');
    }, 700);
  };

  const fetchRecommendations = async (pId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/personas/${pId}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // You can customize max_recommendations if needed, backend defaults to 5
      });
      
      if (!response.ok) throw new Error('Failed to fetch recommendations');
      
      const data = await response.json();
      setRecommendations(data.recommendations);
      setStep('recommendations');
      setAnimation('animate-fade-in');
    } catch (error) {
      console.error("Error fetching recommendations:", error);
      setStep('error');
    }
  };

  const submitAnswers = async (finalAnswers: Record<string, string>) => {
    if (!personaId) return false;

    try {
      // 1. Filter out initial questions (age, gender, relationship) which don't have UUIDs usually
      // The AI questions have UUIDs. 
      // We iterate over `currentQuestions` which holds the AI questions since we are in that phase.
      const answersToSubmit = currentQuestions.map(q => ({
        question_id: q.id,
        answer_choice: finalAnswers[q.id]
      }));
      
      // If no answers to submit (should not happen if we are here), return true to proceed
      if (answersToSubmit.length === 0) return true;

      const response = await fetch('http://localhost:8000/questions/answers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: answersToSubmit }),
      });

      if (!response.ok) throw new Error('Failed to submit answers');
      return true;

    } catch (error) {
      console.error("Error submitting answers:", error);
      setStep('error');
      return false;
    }
  };

  const fetchNextQuestions = async (pId: string) => {
    try {
      setStep('loading');
      setAnimation('animate-fade-in');
      
      const questionsResponse = await fetch(`http://localhost:8000/personas/${pId}/questions`, {
        method: 'GET',
      });
      if (!questionsResponse.ok) throw new Error('Failed to fetch next questions');
      
      const newQuestionsApi = await questionsResponse.json();
      
      if (newQuestionsApi && newQuestionsApi.length > 0) {
        const formattedQuestions: Question[] = newQuestionsApi.map((q: any) => ({
          id: q.id,
          text: q.question,
          type: 'options',
          options: q.choices,
        }));
        setCurrentQuestions(formattedQuestions);
        setQuestionIndex(0);
        setStep('question');
        setAnimation('animate-fade-in');
      } else {
        // If no more questions, go to recommendations
        fetchRecommendations(pId);
      }
    } catch (error) {
      console.error("API Error in fetchNextQuestions:", error);
      setStep('error');
    }
  };

  const buildPersonaAndFetchNextQuestions = async (currentAnswers: Record<string, string>) => {
    try {
      const budgetMap: Record<string, string> = {
        'Under 25€': 'under_25',
        '25-50€': '25-50',
        '50-100€': '50-100',
        'Over 100€': 'over_100'
      };

      const personaBody = {
        occasion: "birthday",
        age: parseInt(currentAnswers.age, 10),
        gender: currentAnswers.gender.toLowerCase(),
        relationship: currentAnswers.relationship.toLowerCase(),
        budget: budgetMap[currentAnswers.budget] || '25-50',
      };

      const personaResponse = await fetch('http://localhost:8000/build-persona/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(personaBody),
      });

      if (!personaResponse.ok) throw new Error('Failed to build persona');
      const personaData = await personaResponse.json();
      setPersonaId(personaData.id);

      // Reuse the new function
      fetchNextQuestions(personaData.id);

    } catch (error) {
      console.error("API Error:", error);
      setStep('error');
    }
  };

  const handleAnswer = (questionId: string, answer: string) => {
    const newAnswers = { ...answers, [questionId]: answer };
    setAnswers(newAnswers);
    setAnimation('animate-fade-out');

    setTimeout(async () => {
      if (questionIndex < currentQuestions.length - 1) {
        setQuestionIndex(prevIndex => prevIndex + 1);
        setAnimation('animate-fade-in');
      } else {
         if (!personaId) {
          // This was the initial questionnaire
          setStep('loading');
          buildPersonaAndFetchNextQuestions(newAnswers);
        } else {
          // Finished a batch of AI questions
          setStep('loading'); // Show loading briefly while submitting
          const success = await submitAnswers(newAnswers);
          if (success) {
             setStep('decision');
             setAnimation('animate-fade-in');
          }
        }
      }
    }, 500);
  };
  
  const handleDecisionMore = () => {
    if (personaId) {
      fetchNextQuestions(personaId);
    }
  };

  const handleDecisionShow = () => {
     if (personaId) {
       setStep('finished'); // Show the "Consulting cosmos" screen
       fetchRecommendations(personaId);
     }
  };

  const renderContent = () => {
    switch (step) {
      case 'teaser':
        return <TeaserScreen onStart={handleStart} animation="animate-fade-in" />;
      case 'exiting_teaser':
        return <TeaserScreen onStart={() => {}} animation="animate-fade-out" />;
      case 'question':
        return (
          <QuestionScreen
            question={currentQuestions[questionIndex]}
            onAnswer={handleAnswer}
            animation={animation}
          />
        );
      case 'decision':
        return (
          <DecisionScreen
            onMore={handleDecisionMore}
            onShow={handleDecisionShow}
            animation={animation}
          />
        );
      case 'loading':
        return <StatusScreen animation="animate-fade-in" title="One moment..." message="Getting to know them better..." />;
      case 'finished':
        return <StatusScreen animation={animation} title="Excellent!" message="I'm consulting the cosmos to find the perfect gift... Please give me a moment." />;
      case 'recommendations':
        return <RecommendationScreen recommendations={recommendations} animation={animation} />;
      case 'error':
        return <StatusScreen animation="animate-fade-in" title="Oh no!" message="Something went wrong while consulting the cosmos. Please try refreshing." />;
      default:
        return null;
    }
  };


  return (
    <main className="bg-gradient-to-b from-midnight-blue to-royal-blue min-h-screen h-screen w-full flex flex-col items-center justify-center overflow-hidden antialiased">
      <div className="w-full h-full max-w-3xl mx-auto">
        {renderContent()}
      </div>
    </main>
  );
}
