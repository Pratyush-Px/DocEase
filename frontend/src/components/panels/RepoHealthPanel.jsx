import { useState, useEffect } from 'react';
import '../../styles/components/panels.css';
import { getRepoHealth } from '../../api/client';

const ScoreRing = ({ score }) => {
  const [offset, setOffset] = useState(251.2); // 2 * PI * 40
  const percentage = (score / 8) * 100;
  
  // Wait to trigger transition
  useEffect(() => {
    const timer = setTimeout(() => {
      const targetOffset = 251.2 - (251.2 * percentage) / 100;
      setOffset(targetOffset);
    }, 100);
    return () => clearTimeout(timer);
  }, [percentage]);

  let ringColor = 'var(--color-danger)';
  if (score >= 6) ringColor = 'var(--color-success)';
  else if (score >= 4) ringColor = 'var(--color-warning)';

  return (
    <div className="score-ring-wrapper">
      <svg className="score-ring" width="100" height="100" viewBox="0 0 100 100">
        <circle className="ring-bg" cx="50" cy="50" r="40" strokeWidth="8" fill="none" />
        <circle 
          className="ring-progress" 
          cx="50" cy="50" r="40" 
          strokeWidth="8" 
          fill="none" 
          stroke={ringColor}
          strokeDasharray="251.2"
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="ring-text count-up-anim">{score}/8</div>
    </div>
  );
};

export default function RepoHealthPanel({ repoHealth, setRepoHealth, repoUrl }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLoad = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getRepoHealth(repoUrl);
      setRepoHealth(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load repository health.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!repoHealth && !isLoading && !error) {
    return (
      <div className="panel-content empty-state">
        <span className="empty-icon">❤️‍🩹</span>
        <p className="empty-text">Analyze repository activity, popularity, and maintenance load.</p>
        <button className="btn-load-panel" onClick={handleLoad}>Analyze Repo Health</button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="panel-content flex-col items-center">
        <div className="shimmer-circle"></div>
        <div className="shimmer-lines w-100" style={{marginTop: '20px'}}>
          <div className="shimmer-line text w-80"></div>
          <div className="shimmer-line text w-70"></div>
        </div>
      </div>
    );
  }

  if (error || repoHealth.error) {
    return (
      <div className="panel-content empty-state">
        <span className="empty-icon">⚠️</span>
        <p className="empty-text text-danger">{error || repoHealth.error}</p>
        <button className="btn-load-panel retry" onClick={handleLoad}>Retry</button>
      </div>
    );
  }

  return (
    <div className="panel-content fade-in-anim repo-health-view">
      <ScoreRing score={repoHealth.health_score} />
      
      <p className="health-summary">{repoHealth.summary}</p>
      
      <div className="health-stats">
        <div className="stat"><span>⭐</span> {repoHealth.stars?.toLocaleString() || 0}</div>
        <div className="stat"><span>🍴</span> {repoHealth.forks?.toLocaleString() || 0}</div>
        <div className="stat"><span>🐛</span> {repoHealth.open_issues?.toLocaleString() || 0}</div>
      </div>

      {repoHealth.insights && repoHealth.insights.length > 0 && (
        <ul className="insights-list">
          {repoHealth.insights.map((insight, idx) => (
            <li key={idx}><span className="insight-bullet">•</span> {insight}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
