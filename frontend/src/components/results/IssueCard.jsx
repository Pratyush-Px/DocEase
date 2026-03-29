import ScoreBar from './ScoreBar';
import SkillBadge from './SkillBadge';
import SkillGapBox from './SkillGapBox';
import '../../styles/components/issue-card.css';

export default function IssueCard({ issue, index, onGenerateActionPlan, isGenerating }) {
  const { title, url, score, readiness_score, matched_skills, labels, skill_gap } = issue;

  return (
    <div className="issue-card" style={{ '--i': index }}>
      <div className="issue-card-header">
        <span className="issue-rank">#{index + 1}</span>
        <div className="issue-labels">
          {labels?.slice(0, 3).map((label, i) => (
            <span key={i} className="issue-label-tag">{label}</span>
          ))}
          {labels?.length > 3 && <span className="issue-label-tag">+{labels.length - 3}</span>}
        </div>
      </div>

      <h3 className="issue-title" title={title}>{title}</h3>

      <div className="issue-scores">
        <ScoreBar label="Match Score" score={score} />
        <ScoreBar label="Readiness" score={readiness_score} />
      </div>

      <div className="issue-skills">
        <span className="skills-prefix">Matched skills:</span>
        <div className="skills-list">
          {matched_skills?.length > 0 ? (
            matched_skills.map((skill, i) => (
              <SkillBadge key={i} skill={skill} variant="matched" delayIndex={i} />
            ))
          ) : (
            <span className="no-skills-text">No direct keyword match</span>
          )}
        </div>
      </div>

      {skill_gap && <SkillGapBox gap={skill_gap} />}

      <div className="issue-actions">
        <button 
          className="btn-action-plan"
          onClick={() => onGenerateActionPlan(issue)}
          disabled={isGenerating}
        >
          {isGenerating ? 'Generating...' : 'Generate Action Plan'}
        </button>
        <a 
          href={url} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="btn-view-issue"
        >
          View Issue &rarr;
        </a>
      </div>
    </div>
  );
}
