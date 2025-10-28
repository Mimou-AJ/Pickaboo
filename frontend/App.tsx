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

// --- Status Screen (for loading and final message) ---
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
  type Step = 'teaser' | 'exiting_teaser' | 'question' | 'loading' | 'finished' | 'error';
  
  const [step, setStep] = useState<Step>('teaser');
  const [currentQuestions, setCurrentQuestions] = useState<Question[]>(initialQuestions);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [animation, setAnimation] = useState('animate-fade-in');
  const [personaId, setPersonaId] = useState<string | null>(null);

  const handleStart = () => {
    setStep('exiting_teaser');
    setTimeout(() => {
      setStep('question');
    }, 700);
  };

  const buildPersonaAndFetchNextQuestions = async (currentAnswers: Record<string, string>) => {
    try {
      const personaBody = {
        occasion: "birthday",
        age: parseInt(currentAnswers.age, 10),
        gender: currentAnswers.gender.toLowerCase(),
        relationship: currentAnswers.relationship.toLowerCase(),
      };

      const personaResponse = await fetch('http://localhost:8000/build-persona/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json',
          'Authorization': "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiJiZmZiODFmNy02MTNmLTQzMDItOGYzMy1jN2I1YTRjZDZiNTIiLCJleHAiOjE3NjA4MDMxOTZ9.SmF-bx8I9mDnk_FZu5t_erSZIdaPVvTZOyYAWu3glBQ"
         },
        body: JSON.stringify(personaBody),
      });

      if (!personaResponse.ok) throw new Error('Failed to build persona');
      const personaData = await personaResponse.json();
      setPersonaId(personaData.id);

      const questionsResponse = await fetch(`http://localhost:8000/personas/${personaData.id}/questions/next`, {
        method: 'GET',
        headers: { 
                  'Authorization': "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiJiZmZiODFmNy02MTNmLTQzMDItOGYzMy1jN2I1YTRjZDZiNTIiLCJleHAiOjE3NjA4MDMxOTZ9.SmF-bx8I9mDnk_FZu5t_erSZIdaPVvTZOyYAWu3glBQ"
}});
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
        setStep('finished');
        setAnimation('animate-fade-in');
      }
    } catch (error) {
      console.error("API Error:", error);
      setStep('error');
    }
  };

  const handleAnswer = (questionId: string, answer: string) => {
    const newAnswers = { ...answers, [questionId]: answer };
    setAnswers(newAnswers);
    setAnimation('animate-fade-out');

    setTimeout(() => {
      if (questionIndex < currentQuestions.length - 1) {
        setQuestionIndex(prevIndex => prevIndex + 1);
        setAnimation('animate-fade-in');
      } else {
        if (!personaId) {
          setStep('loading');
          buildPersonaAndFetchNextQuestions(newAnswers);
        } else {
          console.log("Final Answers:", newAnswers);
          setStep('finished');
          setAnimation('animate-fade-in');
        }
      }
    }, 500);
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
      case 'loading':
        return <StatusScreen animation="animate-fade-in" title="One moment..." message="Getting to know them better..." />;
      case 'finished':
        return <StatusScreen animation={animation} title="Excellent!" message="I'm consulting the cosmos to find the perfect gift... Please give me a moment." />;
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
