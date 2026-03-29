import { useEffect, useState } from 'react';
import '../../styles/components/score-bar.css';

export default function ScoreBar({ label, score }) {
  const percentage = Math.round(score * 100);
  const [mounted, setMounted] = useState(false);
  
  // Set mounted true after initial render to trigger CSS animation
  useEffect(() => {
    // slight delay to ensure it animates cleanly upon appearing
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  let colorClass = 'low';
  if (percentage >= 70) colorClass = 'high';
  else if (percentage >= 40) colorClass = 'mid';

  return (
    <div className="score-bar-wrapper">
      <div className="score-bar-labels">
        <span className="score-label">{label}</span>
        <span className="score-value">{percentage}%</span>
      </div>
      <div className="score-bar-bg">
        <div 
          className={`score-bar-fill ${colorClass} ${mounted ? 'start-anim' : ''}`}
          style={{ '--target-width': `${percentage}%` }}
        />
      </div>
    </div>
  );
}
