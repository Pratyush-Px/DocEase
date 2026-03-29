import { createContext, useState } from 'react';

export const ResultsContext = createContext(null);

export function ResultsProvider({ children }) {
  const [results, setResults] = useState(null);
  const [repoUrl, setRepoUrl] = useState('');
  const [userSkills, setUserSkills] = useState([]);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [contributing, setContributing] = useState(null);
  const [repoHealth, setRepoHealth] = useState(null);
  const [activeTab, setActiveTab] = useState('action'); // 'action' | 'contributing' | 'health'

  const value = {
    results, setResults,
    repoUrl, setRepoUrl,
    userSkills, setUserSkills,
    selectedIssue, setSelectedIssue,
    actionPlan, setActionPlan,
    contributing, setContributing,
    repoHealth, setRepoHealth,
    activeTab, setActiveTab
  };

  return (
    <ResultsContext.Provider value={value}>
      {children}
    </ResultsContext.Provider>
  );
}
