import { Link, useLocation } from 'react-router-dom';
import '../../styles/components/header.css';

export default function Header() {
  const location = useLocation();
  const showNewSearch = location.pathname === '/results';

  return (
    <header className="site-header">
      <div className="container header-container">
        <Link to="/" className="logo">
          <span className="logo-icon">◈</span>
          ResumeIssueHunter
        </Link>
        
        {showNewSearch && (
          <Link to="/" className="btn-new-search">
            &larr; New Search
          </Link>
        )}
      </div>
    </header>
  );
}
