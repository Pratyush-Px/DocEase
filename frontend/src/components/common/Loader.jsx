import { useState, useEffect } from 'react';
import '../../styles/components/loader.css';

const messages = [
  "Parsing your resume…",
  "Extracting skills…",
  "Fetching GitHub issues…",
  "Building embeddings…",
  "Ranking matches…"
];

export default function Loader() {
  const [msgIndex, setMsgIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMsgIndex((prev) => (prev + 1) % messages.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loader-overlay">
      <div className="loader-card">
        <svg className="spinner" viewBox="0 0 50 50">
          <circle className="path" cx="25" cy="25" r="20" fill="none" strokeWidth="4"></circle>
        </svg>
        <div className="loader-text-wrapper">
          <p key={msgIndex} className="loader-text slide-up-anim">{messages[msgIndex]}</p>
        </div>
      </div>
    </div>
  );
}
