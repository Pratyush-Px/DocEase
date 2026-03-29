import '../../styles/components/skill-badge.css';

export default function SkillBadge({ skill, variant = 'matched', delayIndex = 0 }) {
  return (
    <span 
      className={`skill-badge ${variant}`} 
      style={{ '--i': delayIndex }}
    >
      {skill}
    </span>
  );
}
