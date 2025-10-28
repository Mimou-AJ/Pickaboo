
import React from 'react';

const Sparkle: React.FC<{ style: React.CSSProperties }> = ({ style }) => (
  <div
    className="absolute w-2 h-2 bg-jinny-gold rounded-full animate-sparkle opacity-0"
    style={style}
  ></div>
);

const Sparkles: React.FC = () => {
  const sparkleStyles = [
    { top: '10%', left: '20%', animationDelay: '0s' },
    { top: '20%', left: '80%', animationDelay: '0.5s' },
    { top: '50%', left: '10%', animationDelay: '1.2s' },
    { top: '80%', left: '90%', animationDelay: '0.2s' },
    { top: '90%', left: '40%', animationDelay: '0.8s' },
  ];

  return (
    <>
      {sparkleStyles.map((style, i) => (
        <Sparkle key={i} style={style} />
      ))}
    </>
  );
};

export const JinnyMascot: React.FC<{ size: 'large' | 'small' }> = ({ size }) => {
  const sizeClasses = size === 'large'
    ? 'w-48 h-48 md:w-60 md:h-60'
    : 'w-16 h-16';

  return (
    <div className={`relative flex-shrink-0 transition-all duration-700 ease-in-out ${sizeClasses}`}>
      <div className="absolute inset-0 animate-float">
        <div className="w-full h-full rounded-full bg-gradient-to-br from-jinny-pink to-indigo-500 shadow-2xl shadow-jinny-pink/40"></div>
      </div>
      {size === 'large' && <Sparkles />}
    </div>
  );
};
