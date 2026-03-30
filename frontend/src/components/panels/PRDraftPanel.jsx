import { useContext, useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { ResultsContext } from '../../context/ResultsContext';
import { generatePRDraft } from '../../api/client';
import '../../styles/components/pr-draft.css';

function PRDraftStructured({ draft }) {
  if (!draft) return null;
  return (
    <div className="pr-result fade-in-anim">
      <div className="pr-section">
        <h3 className="pr-section-title">📋 PR Title</h3>
        <p>{draft.pr_title}</p>
      </div>
      
      <div className="pr-section">
        <h3 className="pr-section-title">📝 Summary</h3>
        <p>{draft.summary}</p>
      </div>

      <div className="pr-section">
        <h3 className="pr-section-title">🔧 Changes Made</h3>
        <ul className="action-plan-content ul" style={{margin:0}}>
          {draft.changes?.map((change, i) => (
            <li key={i}>{change}</li>
          ))}
        </ul>
      </div>

      <div className="pr-section">
        <h3 className="pr-section-title">🧪 How to Test</h3>
        <ul className="action-plan-content" style={{margin:0}}>
          {draft.testing?.map((test, i) => (
            <li key={i}>{test}</li>
          ))}
        </ul>
      </div>

      <div className="pr-section">
        <h3 className="pr-section-title">✅ Checklist</h3>
        <div>
          {draft.checklist?.map((item, i) => (
            <div key={i} className="pr-checklist-item">
              <input type="checkbox" id={`chk-${i}`} />
              <label htmlFor={`chk-${i}`}>{item.replace(/^☐\s*|^\s*\[\s\]\s*/, '')}</label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function PRDraftPanel() {
  const {
    repoUrl,
    prDraft, setPrDraft,
    prDraftLoading, setPrDraftLoading,
    prDraftError, setPrDraftError,
    prDraftIssue
  } = useContext(ResultsContext);

  const [solutionDescription, setSolutionDescription] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Reset copy state when draft changes
    setCopied(false);
  }, [prDraft]);

  const handleSubmit = async () => {
    if (solutionDescription.length < 20 || solutionDescription.length > 500) return;
    
    setPrDraftError(null);
    setPrDraftLoading(true);
    setPrDraft(null);

    try {
      const data = await generatePRDraft({
        issueTitle: prDraftIssue.title,
        issueDescription: prDraftIssue.description || prDraftIssue.url, // Fallback if description is missing
        solutionDescription,
        repoUrl
      });

      if (!data.pr_draft) {
        throw new Error("No draft generated");
      }
      
      setPrDraft(data.pr_draft);
    } catch (err) {
      console.error(err);
      setPrDraftError(
        err.response?.status === 422 
          ? "Missing required fields. Please try again."
          : "Generation failed. The AI service may be unavailable or connection timed out."
      );
    } finally {
      setPrDraftLoading(false);
    }
  };

  const handleCopy = () => {
    let copyText = typeof prDraft === 'string' ? prDraft : JSON.stringify(prDraft, null, 2);
    // Rough formatting for object if it's structured
    if (typeof prDraft === 'object') {
      copyText = `# ${prDraft.pr_title}\n\n## Summary\n${prDraft.summary}\n\n## Changes Made\n${prDraft.changes?.map(c => '- '+c).join('\n')}\n\n## How to Test\n${prDraft.testing?.map(t => '- '+t).join('\n')}\n\n## Checklist\n${prDraft.checklist?.map(c => '- [ ] '+c.replace(/^☐\s*/,'')).join('\n')}`;
    }

    navigator.clipboard.writeText(copyText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleClear = () => {
    setPrDraft(null);
  };

  if (!prDraftIssue) {
    return (
      <div className="pr-draft-panel">
        <div className="pr-draft-scrollable">
          <div className="pr-draft-empty">
            <div className="empty-icon" style={{fontSize: '3rem', marginBottom: '1rem'}}>📄</div>
            <div>Select an issue and describe your solution to generate a PR draft.</div>
          </div>
        </div>
      </div>
    );
  }

  const charCount = solutionDescription.length;
  const isNearLimit = charCount > 400;
  const isAtLimit = charCount >= 500;
  const isTooShort = charCount < 20;

  return (
    <div className="pr-draft-panel">
      <div className="pr-draft-scrollable">
        {!prDraft && (
          <div className="pr-draft-form">
          <div className="pr-draft-context-bar">
            Working on: {prDraftIssue.title.length > 60 ? prDraftIssue.title.substring(0, 60) + '...' : prDraftIssue.title}
          </div>
          
          <div>
            <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: 600, fontSize: '14px'}}>
              Describe your solution
            </label>
            <textarea
              className="solution-textarea"
              placeholder="I fixed this by..."
              value={solutionDescription}
              onChange={(e) => setSolutionDescription(e.target.value.substring(0, 500))}
              disabled={prDraftLoading}
            />
            <div className={`char-counter ${isNearLimit ? (isAtLimit ? 'at-limit' : 'near-limit') : ''}`}>
              {charCount} / 500 chars (min 20)
            </div>
          </div>
          
          <button 
            className="btn-action-plan" 
            style={{ width: '100%', padding: '12px' }}
            onClick={handleSubmit}
            disabled={prDraftLoading || isTooShort || isAtLimit}
          >
            {prDraftLoading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <span className="typing-dot" style={{background: 'currentColor', animationName: 'spin', animationDuration: '1s'}} /> Generating draft...
              </span>
            ) : 'Generate PR Draft'}
          </button>
          
          {prDraftError && (
            <div className="pr-error fade-in-anim">
               ⚠ {prDraftError}
            </div>
          )}
        </div>
      )}

      {prDraft && (
        <div className="pr-result fade-in-anim">
          
          {typeof prDraft === 'string' ? (
            <div className="action-plan-content">
              <ReactMarkdown>{prDraft}</ReactMarkdown>
            </div>
          ) : (
            <PRDraftStructured draft={prDraft} />
          )}

          <div className="pr-actions">
            <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={handleCopy}>
              {copied ? 'Copied!' : 'Copy to Clipboard'}
            </button>
            <button className="btn-load-panel retry" style={{margin: 0, flex: 1}} onClick={handleClear}>
              Generate Again
            </button>
          </div>
        </div>
      )}

      </div>
    </div>
  );
}
