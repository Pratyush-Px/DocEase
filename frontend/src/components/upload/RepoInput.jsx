import { useState } from 'react';

export default function RepoInput({ value, onChange, error }) {
  const [isFocused, setIsFocused] = useState(false);
  const [isTouched, setIsTouched] = useState(false);

  const isValidUrl = value.startsWith('https://github.com/') || value.startsWith('topic:');
  const showSuccess = isValidUrl && value.length > 20;
  const showError = error || (isTouched && !isFocused && !isValidUrl && value.length > 0);

  return (
    <div className={`repo-input-wrapper ${showError ? 'has-error' : ''} ${showSuccess ? 'has-success' : ''}`}>
      <label className="input-label" htmlFor="repo_url">GitHub Repository or Topic</label>
      <div className="input-container">
        <svg className="github-icon" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.45-1.15-1.11-1.46-1.11-1.46-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 10 0 0 12 2Z"></path>
        </svg>
        <input
          id="repo_url"
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => {
            setIsFocused(false);
            setIsTouched(true);
          }}
          placeholder="https://github.com/owner/repo"
          className="repo-input"
        />
        {showSuccess && <div className="input-success-icon">✓</div>}
      </div>
      {showError && <span className="input-error-msg">{error || "Please enter a valid GitHub URL or topic"}</span>}
      {!showError && <span className="input-hint">Paste a repository URL or e.g., topic:python</span>}
    </div>
  );
}
