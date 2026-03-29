import ReactMarkdown from 'react-markdown';
import '../../styles/components/panels.css';

export default function ActionPlanPanel({ actionPlan, error, isLoading }) {
  if (isLoading) {
    return (
      <div className="panel-content">
        <div className="shimmer-lines">
          <div className="shimmer-line title"></div>
          <div className="shimmer-line text"></div>
          <div className="shimmer-line text"></div>
          <div className="shimmer-line text"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel-content empty-state">
        <span className="empty-icon">⚠️</span>
        <p className="empty-text text-danger">{error}</p>
      </div>
    );
  }

  if (!actionPlan) {
    return (
      <div className="panel-content empty-state">
        <span className="empty-icon">📝</span>
        <p className="empty-text">Click "Generate Action Plan" on any issue to see a step-by-step guide here.</p>
      </div>
    );
  }

  return (
    <div className="panel-content action-plan-content fade-in-anim">
      <ReactMarkdown>{actionPlan}</ReactMarkdown>
    </div>
  );
}
