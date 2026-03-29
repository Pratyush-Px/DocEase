import { useState } from 'react';

// Using inline styles for gap box or we can just import issue-card.css
export default function SkillGapBox({ gap }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!gap) return null;

  return (
    <div className={`skill-gap-box ${isOpen ? 'open' : ''}`}>
      <button 
        className="skill-gap-toggle" 
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className="toggle-icon">{isOpen ? '▼' : '▶'}</span>
        <span className="toggle-text">Skill Gap Analysis</span>
      </button>
      
      <div className="skill-gap-content-wrapper">
        <div className="skill-gap-content">
          <p>{gap}</p>
        </div>
      </div>
    </div>
  );
}
