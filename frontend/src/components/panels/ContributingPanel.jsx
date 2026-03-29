import { useState } from 'react';
import '../../styles/components/panels.css';
import { getContributing } from '../../api/client';

export default function ContributingPanel({ contributing, setContributing, repoUrl }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLoad = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getContributing(repoUrl);
      setContributing(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load contributing guidelines.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!contributing && !isLoading && !error) {
    return (
      <div className="panel-content empty-state">
        <span className="empty-icon">🛠️</span>
        <p className="empty-text">View the repository's setup steps and contribution guidelines.</p>
        <button className="btn-load-panel" onClick={handleLoad}>Load Contributing Guide</button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="panel-content">
        <div className="shimmer-lines">
          <div className="shimmer-line title"></div>
          <div className="shimmer-line text w-70"></div>
          <div className="shimmer-line text w-50"></div>
          <div className="shimmer-line text w-60"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel-content empty-state">
        <span className="empty-icon">⚠️</span>
        <p className="empty-text text-danger">{error}</p>
        <button className="btn-load-panel retry" onClick={handleLoad}>Retry</button>
      </div>
    );
  }

  return (
    <div className="panel-content fade-in-anim contributing-view">
      {contributing.llm_summary && (
        <div className="summary-section">
          <h4>Contribution Workflow</h4>
          <p className="llm-summary">{contributing.llm_summary}</p>
        </div>
      )}

      {contributing.setup_steps && contributing.setup_steps.length > 0 && (
        <div className="setup-section">
          <h4>Setup Steps</h4>
          <ol className="setup-list">
            {contributing.setup_steps.map((step, idx) => (
              <li key={idx}><code>{step}</code></li>
            ))}
          </ol>
        </div>
      )}

      {contributing.message && (
        <p className="no-data-msg">{contributing.message}</p>
      )}
    </div>
  );
}
