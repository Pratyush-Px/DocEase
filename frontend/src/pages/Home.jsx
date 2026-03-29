import { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { ResultsContext } from '../context/ResultsContext';
import { matchIssues } from '../api/client';
import ResumeDropzone from '../components/upload/ResumeDropzone';
import RepoInput from '../components/upload/RepoInput';
import Loader from '../components/common/Loader';
import ErrorBanner from '../components/common/ErrorBanner';
import '../styles/pages/home.css';

export default function Home() {
  const navigate = useNavigate();
  const { setResults, repoUrl, setRepoUrl, setUserSkills, setActiveTab } = useContext(ResultsContext);
  
  const [file, setFile] = useState(null);
  const [experienceLevel, setExperienceLevel] = useState('junior');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({ file: null, repo: null });

  const validateForm = () => {
    let isValid = true;
    const errors = { file: null, repo: null };

    if (!file) {
      errors.file = 'Please upload a PDF resume.';
      isValid = false;
    }
    
    if (!repoUrl) {
      errors.repo = 'Please provide a GitHub repository URL.';
      isValid = false;
    } else if (!repoUrl.startsWith('https://github.com/') && !repoUrl.startsWith('topic:')) {
      errors.repo = 'URL must start with https://github.com/ or topic:';
      isValid = false;
    }

    setFormErrors(errors);
    return isValid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    setIsLoading(true);
    setError(null);

    try {
      const data = await matchIssues({
        resumeFile: file,
        repoUrl,
        experienceLevel
      });
      
      setResults(data);
      setUserSkills(data.user_skills);
      setActiveTab('action');
      navigate('/results');
    } catch (err) {
      console.error(err);
      if (err.response) {
        switch (err.response.status) {
          case 400:
            setError('Invalid input. Please check your URL and resume.');
            break;
          case 403:
            setError('GitHub rate limit reached. Add a GitHub token or wait.');
            break;
          case 404:
            setError('Repository not found. Double-check the URL.');
            break;
          case 503:
            setError('Service temporarily unavailable. Try again in a moment.');
            break;
          default:
            setError('Something went wrong. Please try again.');
        }
      } else {
        setError('Network error or server is down. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="home-page fade-in">
      <div className="container">
        {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
        
        {isLoading && <Loader />}

        <section className="hero-section">
          <h1 className="hero-title">Find GitHub Issues That Match Your Skills</h1>
          <p className="hero-subtitle">Upload your resume. Get matched issues.</p>
        </section>

        <section className="form-section">
          <div className="form-card">
            <form onSubmit={handleSubmit} className="match-form">
              
              <div className="form-group">
                <ResumeDropzone file={file} setFile={setFile} error={formErrors.file} />
              </div>

              <div className="form-group">
                <RepoInput value={repoUrl} onChange={setRepoUrl} error={formErrors.repo} />
              </div>

              <div className="form-group experience-group">
                <label className="input-label">Experience Level</label>
                <div className="experience-pills">
                  {['junior', 'mid', 'senior'].map((level) => (
                    <button
                      key={level}
                      type="button"
                      className={`pill-btn ${experienceLevel === level ? 'active' : ''}`}
                      onClick={() => setExperienceLevel(level)}
                    >
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              <button 
                type="submit" 
                className="btn-submit" 
                disabled={isLoading}
              >
                {isLoading ? 'Analysing...' : 'Match Me to Issues →'}
              </button>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
