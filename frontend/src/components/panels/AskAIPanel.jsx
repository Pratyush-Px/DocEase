import { useContext, useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { ResultsContext } from '../../context/ResultsContext';
import { askCodingQuestion } from '../../api/client';
import '../../styles/components/ask-ai.css';

export default function AskAIPanel() {
  const {
    repoUrl,
    chatMessages,
    addChatMessage,
    clearChat,
    chatLoading, setChatLoading,
    chatError, setChatError,
    chatIssueContext, setChatIssueContext
  } = useContext(ResultsContext);

  const [inputVal, setInputVal] = useState('');
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, chatLoading, chatError]);

  const handleClearContext = () => {
    setChatIssueContext(null);
  };

  const handleInput = (e) => {
    setInputVal(e.target.value);
    // Auto-grow textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = '40px'; // reset
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = Math.min(scrollHeight, 120) + 'px';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = async () => {
    if (!inputVal.trim() || chatLoading) return;

    const questionText = inputVal.trim();
    setInputVal('');
    if (textareaRef.current) textareaRef.current.style.height = '40px';
    
    setChatError(null);
    addChatMessage({
      role: 'user',
      content: questionText,
      timestamp: new Date()
    });

    setChatLoading(true);

    try {
      const data = await askCodingQuestion({
        question: questionText,
        issueTitle: chatIssueContext?.title || '',
        issueDescription: chatIssueContext?.description || '',
        repoUrl
      });
      
      if (!data.answer) {
         throw new Error("No answer generated");
      }

      addChatMessage({
        role: 'assistant',
        content: data.answer,
        timestamp: new Date()
      });
    } catch (err) {
      console.error("Ask AI error:", err);
      // Determine what to do with the error.
      // Do not block chat, just show error inline bubble.
      setChatError(
        err.response?.status === 422 
          ? "⚠ Missing required fields. Please try again."
          : "⚠ Failed to get a response. Please try again."
      );
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="ask-ai-panel">
      <div className="ask-ai-header">
        <button className="btn-clear-chat" onClick={clearChat} title="Clear history">
          Clear Chat
        </button>
      </div>

      {chatIssueContext ? (
        <div className="chat-context-bar fade-in-anim">
          <span>🔗 Context: {chatIssueContext.title.length > 50 ? chatIssueContext.title.substring(0, 50) + '...' : chatIssueContext.title}</span>
          <button onClick={handleClearContext}>&times; Clear</button>
        </div>
      ) : null}

      <div className="chat-messages" ref={messagesContainerRef}>
        {chatMessages.length === 0 ? (
          <div className="chat-empty">
            <p>Ask any coding question. Select an issue for context-aware answers.</p>
          </div>
        ) : (
          chatMessages.map((msg, idx) => (
            <div key={idx} className={`chat-bubble ${msg.role}`}>
              {msg.role === 'user' ? (
                msg.content
              ) : (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              )}
            </div>
          ))
        )}

        {chatLoading && (
          <div className="chat-bubble assistant">
             <div className="typing-indicator">
               <div className="typing-dot"></div>
               <div className="typing-dot"></div>
               <div className="typing-dot"></div>
             </div>
          </div>
        )}

        {chatError && (
          <div className="chat-bubble error">
            {chatError}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={inputVal}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Type your question..."
          rows={1}
          disabled={chatLoading}
        />
        <button 
          className="chat-send-btn" 
          onClick={handleSend}
          disabled={!inputVal.trim() || chatLoading}
        >
          Send &rarr;
        </button>
      </div>
    </div>
  );
}
