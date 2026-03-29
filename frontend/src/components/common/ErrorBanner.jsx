import { useEffect } from 'react';
import '../../styles/components/error-banner.css';

export default function ErrorBanner({ message, onDismiss }) {
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        onDismiss();
      }, 6000);
      return () => clearTimeout(timer);
    }
  }, [message, onDismiss]);

  if (!message) return null;

  return (
    <div className="error-banner slide-down">
      <div className="error-content">
        <span className="error-icon">⚠️</span>
        <span className="error-text">{message}</span>
      </div>
      <button className="error-close" onClick={onDismiss} aria-label="Dismiss">
        &times;
      </button>
    </div>
  );
}
