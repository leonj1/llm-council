import { useState, useEffect, useRef } from 'react';
import Markdown from './Markdown';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import Stage3MovieScript from './Stage3MovieScript';
import Stage4 from './Stage4';
import DatabaseStatus from './DatabaseStatus';
import DbConfigModal from './DbConfigModal';
import RoleIndicator from './RoleIndicator';
import './ChatInterface.css';

export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
  isMobile,
  onBack,
  onRegenerateFinalScript,
  isRegenerating,
}) {
  const [input, setInput] = useState('');
  const [numTurns, setNumTurns] = useState(3);
  const [movieLength, setMovieLength] = useState(90);
  const [collapsedMessages, setCollapsedMessages] = useState({});
  const [showDbConfigModal, setShowDbConfigModal] = useState(false);
  const messagesEndRef = useRef(null);

  const toggleCollapse = (index) => {
    setCollapsedMessages(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const truncateText = (text, maxLength = 100) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const CollapseIcon = ({ isCollapsed }) => (
    <svg
      className={`collapse-icon ${isCollapsed ? 'collapsed' : ''}`}
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="currentColor"
    >
      <path d="M4.5 5.5L8 9L11.5 5.5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const movieLengthOptions = [
    { value: 5, label: '5 min (Short)' },
    { value: 15, label: '15 min (Short Film)' },
    { value: 30, label: '30 min (TV Episode)' },
    { value: 60, label: '60 min (TV Hour)' },
    { value: 90, label: '90 min (Feature)' },
    { value: 180, label: '180 min (Epic)' },
    { value: 300, label: '300 min (Mini-Series)' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input, numTurns, movieLength);
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isMovieScript = conversation?.type === 'movie_script';

  if (!conversation) {
    return (
      <div className={`chat-interface ${isMobile ? 'mobile' : ''}`}>
        {isMobile ? (
          <div className="mobile-header">
            <button className="back-button" onClick={onBack}>
              ‹ Back
            </button>
            <h2>LLM Council</h2>
            <div className="header-status-group">
              <RoleIndicator />
              <DatabaseStatus onClick={() => setShowDbConfigModal(true)} isLoggedIn={true} />
            </div>
          </div>
        ) : (
          <div className="desktop-header">
            <RoleIndicator />
            <DatabaseStatus onClick={() => setShowDbConfigModal(true)} isLoggedIn={true} />
          </div>
        )}
        <div className="empty-state">
          <h2>Welcome to LLM Council</h2>
          <p>Create a new conversation to get started</p>
        </div>
        <DbConfigModal isOpen={showDbConfigModal} onClose={() => setShowDbConfigModal(false)} />
      </div>
    );
  }

  return (
    <div className={`chat-interface ${isMobile ? 'mobile' : ''}`}>
      {isMobile ? (
        <div className="mobile-header">
          <button className="back-button" onClick={onBack}>
            ‹ Back
          </button>
          <h2>{conversation.title || 'New Conversation'}</h2>
          <div className="header-status-group">
            <RoleIndicator />
            <DatabaseStatus onClick={() => setShowDbConfigModal(true)} isLoggedIn={true} />
          </div>
        </div>
      ) : (
        <div className="desktop-header">
          <RoleIndicator />
          <DatabaseStatus onClick={() => setShowDbConfigModal(true)} isLoggedIn={true} />
        </div>
      )}
      <DbConfigModal isOpen={showDbConfigModal} onClose={() => setShowDbConfigModal(false)} />
      <div className="messages-container">
        {conversation.messages.length === 0 ? (
          <div className="empty-state">
            <h2>{isMovieScript ? 'Create a Movie Script' : 'Start a conversation'}</h2>
            <p>
              {isMovieScript
                ? 'Describe your movie idea and watch the council collaborate'
                : 'Ask a question to consult the LLM Council'}
            </p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === 'user' ? (
                <div className="user-message">
                  <div className="message-label">
                    <button
                      className="collapse-toggle"
                      onClick={() => toggleCollapse(index)}
                      aria-label={collapsedMessages[index] ? 'Expand message' : 'Collapse message'}
                    >
                      <CollapseIcon isCollapsed={collapsedMessages[index]} />
                    </button>
                    You
                  </div>
                  {collapsedMessages[index] ? (
                    <div className="message-content collapsed-preview">
                      {truncateText(msg.content)}
                    </div>
                  ) : (
                    <div className="message-content">
                      <div className="markdown-content">
                        <Markdown>{msg.content}</Markdown>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="assistant-message">
                  <div className="message-label">
                    <button
                      className="collapse-toggle"
                      onClick={() => toggleCollapse(index)}
                      disabled={msg.loading?.stage1 || msg.loading?.stage2 || msg.loading?.stage3 || msg.loading?.stage4}
                      aria-label={collapsedMessages[index] ? 'Expand message' : 'Collapse message'}
                    >
                      <CollapseIcon isCollapsed={collapsedMessages[index]} />
                    </button>
                    {isMovieScript ? 'Movie Script Studio' : 'LLM Council'}
                  </div>

                  {collapsedMessages[index] ? (
                    <div className="collapsed-preview assistant-collapsed">
                      <em>Message collapsed - click to expand</em>
                    </div>
                  ) : (
                    <>
                      {/* Stage 1 */}
                      {msg.loading?.stage1 && (
                        <div className="stage-loading">
                          <div className="spinner"></div>
                          <span>
                            {isMovieScript
                              ? 'Running Stage 1: Generating script proposals...'
                              : 'Running Stage 1: Collecting individual responses...'}
                          </span>
                        </div>
                      )}
                      {msg.stage1 && <Stage1 responses={msg.stage1} />}

                      {/* Stage 2 */}
                      {msg.loading?.stage2 && (
                        <div className="stage-loading">
                          <div className="spinner"></div>
                          <span>Running Stage 2: Peer review and ranking...</span>
                        </div>
                      )}
                      {msg.stage2 && (
                        <Stage2
                          rankings={msg.stage2}
                          labelToModel={msg.metadata?.label_to_model}
                          aggregateRankings={msg.metadata?.aggregate_rankings}
                        />
                      )}

                      {/* Stage 3 - Different component for movie script */}
                      {msg.loading?.stage3 && (
                        <div className="stage-loading">
                          <div className="spinner"></div>
                          <span>
                            {isMovieScript
                              ? 'Running Stage 3: Selecting best script...'
                              : 'Running Stage 3: Final synthesis...'}
                          </span>
                        </div>
                      )}
                      {msg.stage3 && (
                        isMovieScript ? (
                          <Stage3MovieScript selection={msg.stage3} />
                        ) : (
                          <Stage3 finalResponse={msg.stage3} />
                        )
                      )}

                      {/* Stage 4 - Movie script only */}
                      {isMovieScript && (
                        <>
                          {msg.loading?.stage4 && !msg.stage4?.dialogue_history?.length && (
                            <div className="stage-loading">
                              <div className="spinner"></div>
                              <span>Running Stage 4: Starting collaborative refinement...</span>
                            </div>
                          )}
                          {(msg.stage4 || msg.loading?.stage4) && (
                            <Stage4
                              stage4Data={msg.stage4}
                              isLoading={msg.loading?.stage4}
                              onRegenerateFinalScript={onRegenerateFinalScript}
                              isRegenerating={isRegenerating}
                            />
                          )}
                        </>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>
              {isMovieScript
                ? 'Generating your movie script...'
                : 'Consulting the council...'}
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <textarea
          className="message-input"
          placeholder={
            isMovieScript
              ? 'Describe your movie idea... (e.g., "A sci-fi thriller about AI becoming sentient")'
              : 'Ask your question... (Shift+Enter for new line, Enter to send)'
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={3}
        />

        {isMovieScript && (
          <div className="movie-script-options">
            <div className="movie-length-select">
              <label htmlFor="length-input">Movie length:</label>
              <select
                id="length-input"
                value={movieLength}
                onChange={(e) => setMovieLength(parseInt(e.target.value, 10))}
                disabled={isLoading}
              >
                {movieLengthOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="turns-slider">
              <label htmlFor="turns-input">
                Collaboration turns: <strong>{numTurns}</strong>
              </label>
              <input
                id="turns-input"
                type="range"
                min="1"
                max="7"
                value={numTurns}
                onChange={(e) => setNumTurns(parseInt(e.target.value, 10))}
                disabled={isLoading}
              />
              <div className="turns-labels">
                <span>1</span>
                <span>7</span>
              </div>
            </div>
          </div>
        )}

        <button
          type="submit"
          className="send-button"
          disabled={!input.trim() || isLoading}
        >
          {isMovieScript ? 'Generate Script' : 'Send'}
        </button>
      </form>
    </div>
  );
}
