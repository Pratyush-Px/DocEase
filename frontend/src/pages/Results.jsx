import { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ResultsContext } from '../context/ResultsContext';
import { generateActionPlan } from '../api/client';
import IssueCard from '../components/results/IssueCard';
import SkillBadge from '../components/results/SkillBadge';
import ActionPlanPanel from '../components/panels/ActionPlanPanel';
import ContributingPanel from '../components/panels/ContributingPanel';
import RepoHealthPanel from '../components/panels/RepoHealthPanel';
import PRDraftPanel from '../components/panels/PRDraftPanel';
import AskAIPanel from '../components/panels/AskAIPanel';
import EmptyState from '../components/common/EmptyState';
import '../styles/pages/results.css';

export default function Results() {
  const navigate = useNavigate();
  const { 
    results, repoUrl, userSkills, 
    activeTab, setActiveTab,
    selectedIssue, setSelectedIssue,
    actionPlan, setActionPlan,
    contributing, setContributing,
    repoHealth, setRepoHealth 
  } = useContext(ResultsContext);

  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [planError, setPlanError] = useState(null);

  useEffect(() => {
    if (!results) {
      navigate('/');
    }
  }, [results, navigate]);

  if (!results) return null;

  const handleGenerateActionPlan = async (issue) => {
    setSelectedIssue(issue);
    setActiveTab('action');
    setIsGeneratingPlan(true);
    setPlanError(null);
    setActionPlan(null); // Clear previous plan

    try {
      const data = await generateActionPlan({
        issueTitle: issue.title,
        issueDescription: issue.url, // Usually full description, using URL as fallback if not in list
        repoUrl,
        userSkills
      });
      setActionPlan(data.markdown_plan);
    } catch (err) {
      console.error(err);
      setPlanError('Failed to generate action plan. Please try again.');
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const topMatches = results.top_matches || [];

  return (
    <div className="results-page fade-in-anim">
      <div className="container">
        <header className="results-header">
          <div className="results-meta">
            <h2>{topMatches.length} issues matched for <span className="highlight-repo">{results.repo}</span></h2>
            <span className="scanned-count">{results.issues_scanned} issues scanned</span>
          </div>
          <div className="user-skills-summary">
            <span className="skills-prefix">Your parsed skills:</span>
            <div className="skills-list">
              {userSkills.slice(0, 8).map((skill, idx) => (
                <SkillBadge key={idx} skill={skill} variant="neutral" delayIndex={idx} />
              ))}
              {userSkills.length > 8 && (
                <span className="plus-skills">+{userSkills.length - 8}</span>
              )}
            </div>
          </div>
        </header>

        {topMatches.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="results-layout">
            <div className="results-layout__left">
              {topMatches.map((issue, index) => (
                <IssueCard 
                  key={issue.url} 
                  issue={issue} 
                  index={index} 
                  onGenerateActionPlan={handleGenerateActionPlan}
                  isGenerating={isGeneratingPlan && selectedIssue?.url === issue.url}
                />
              ))}
            </div>
            <div className="results-layout__right">
              <aside className="panel-wrapper">
                <nav className="panel-tabs">
                  <button 
                    className={`tab-btn ${activeTab === 'action' ? 'active' : ''}`}
                    onClick={() => setActiveTab('action')}
                  >
                    Action Plan
                  </button>
                  <button 
                    className={`tab-btn ${activeTab === 'contributing' ? 'active' : ''}`}
                    onClick={() => setActiveTab('contributing')}
                  >
                    Contributing
                  </button>
                  <button 
                    className={`tab-btn ${activeTab === 'health' ? 'active' : ''}`}
                    onClick={() => setActiveTab('health')}
                  >
                    Repo Health
                  </button>
                  <button 
                    className={`tab-btn ${activeTab === 'pr' ? 'active' : ''}`}
                    onClick={() => setActiveTab('pr')}
                  >
                    PR Draft
                  </button>
                  <button 
                    className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                    onClick={() => setActiveTab('chat')}
                  >
                    Ask AI
                  </button>
                </nav>
                
                <div className="panel-body">
                  {activeTab === 'action' && (
                    <ActionPlanPanel 
                      actionPlan={actionPlan} 
                      error={planError} 
                      isLoading={isGeneratingPlan} 
                    />
                  )}
                  {activeTab === 'contributing' && (
                    <ContributingPanel 
                      contributing={contributing} 
                      setContributing={setContributing} 
                      repoUrl={repoUrl} 
                    />
                  )}
                  {activeTab === 'health' && (
                    <RepoHealthPanel 
                      repoHealth={repoHealth} 
                      setRepoHealth={setRepoHealth} 
                      repoUrl={repoUrl} 
                    />
                  )}
                  {activeTab === 'pr' && (
                    <PRDraftPanel />
                  )}
                  {activeTab === 'chat' && (
                    <AskAIPanel />
                  )}
                </div>
              </aside>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
