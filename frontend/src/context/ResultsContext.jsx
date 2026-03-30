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
  const [activeTab, setActiveTab] = useState('action'); // 'action' | 'contributing' | 'health' | 'pr' | 'chat'

  const [prDraft, setPrDraft] = useState(null);
  const [prDraftLoading, setPrDraftLoading] = useState(false);
  const [prDraftError, setPrDraftError] = useState(null);
  const [prDraftIssue, setPrDraftIssue] = useState(null);

  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);
  const [chatIssueContext, setChatIssueContext] = useState(null);

  const addChatMessage = (message) => setChatMessages(prev => [...prev, message]);
  const clearChat = () => setChatMessages([]);

  const value = {
    results, setResults,
    repoUrl, setRepoUrl,
    userSkills, setUserSkills,
    selectedIssue, setSelectedIssue,
    actionPlan, setActionPlan,
    contributing, setContributing,
    repoHealth, setRepoHealth,
    activeTab, setActiveTab,
    prDraft, setPrDraft,
    prDraftLoading, setPrDraftLoading,
    prDraftError, setPrDraftError,
    prDraftIssue, setPrDraftIssue,
    chatMessages, setChatMessages,
    chatLoading, setChatLoading,
    chatError, setChatError,
    chatIssueContext, setChatIssueContext,
    addChatMessage, clearChat
  };

  return (
    <ResultsContext.Provider value={value}>
      {children}
    </ResultsContext.Provider>
  );
}
