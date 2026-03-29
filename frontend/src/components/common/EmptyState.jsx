import '../../styles/components/error-banner.css'; /* Reuse some styles if needed, but going to use inline or dedicated CSS if requested */
import { Link } from 'react-router-dom';

/* Since Empty state CSS was not explicitly named in the file tree prompt but EmptyState.jsx was,
   I'll put the empty state specific styles in the results.css or in a style block here */
   
export default function EmptyState() {
  return (
    <div className="empty-state" style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', 
      justifyContent: 'center', minHeight: '50vh', textAlign: 'center',
      animation: 'cardReveal 400ms ease forwards'
    }}>
      <div className="empty-illustration" style={{
        fontSize: '4rem', marginBottom: 'var(--space-4)', opacity: 0.8,
        animation: 'float 4s ease-in-out infinite'
      }}>
        🔍
      </div>
      <h2 style={{ marginBottom: 'var(--space-2)' }}>No matching issues found</h2>
      <p style={{ color: 'var(--color-text-muted)', marginBottom: 'var(--space-5)' }}>
        We scanned the latest open issues but couldn't find a strong skill match.
      </p>
      <Link to="/" style={{
        backgroundColor: 'var(--color-surface)', border: '2px solid var(--color-border)',
        padding: '12px 24px', borderRadius: 'var(--radius-md)', fontWeight: 600,
        transition: 'all 200ms ease'
      }}>
        Try another repository
      </Link>
    </div>
  );
}
