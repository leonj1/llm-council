import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage4.css';

export default function Stage4({ stage4Data, isLoading, onRegenerateFinalScript, isRegenerating }) {
  const [expandedTurns, setExpandedTurns] = useState({});
  const [copyStatus, setCopyStatus] = useState('idle'); // 'idle' | 'copied' | 'error'

  if (!stage4Data && !isLoading) {
    return null;
  }

  const toggleTurn = (index) => {
    setExpandedTurns((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const expandAll = () => {
    const allExpanded = {};
    (stage4Data?.dialogue_history || []).forEach((_, index) => {
      allExpanded[index] = true;
    });
    setExpandedTurns(allExpanded);
  };

  const collapseAll = () => {
    setExpandedTurns({});
  };

  const copyToClipboard = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const script = stage4Data?.refined_script;
    if (!script) {
      console.error('No script to copy');
      setCopyStatus('error');
      setTimeout(() => setCopyStatus('idle'), 2000);
      return;
    }

    try {
      // Try modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(script);
      } else {
        // Fallback for older browsers or non-HTTPS contexts
        const textArea = document.createElement('textarea');
        textArea.value = script;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        textArea.style.top = '-9999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
      setCopyStatus('error');
      setTimeout(() => setCopyStatus('idle'), 2000);
    }
  };

  const collaborators = stage4Data?.collaborators || [];
  const dialogueHistory = stage4Data?.dialogue_history || [];
  const refinedScript = stage4Data?.refined_script;
  const numTurns = stage4Data?.num_turns || 0;
  const runtimeValidation = stage4Data?.runtime_validation;

  // Group dialogue by turn number
  const groupedByTurn = dialogueHistory.reduce((acc, entry) => {
    const turn = entry.turn;
    if (!acc[turn]) {
      acc[turn] = [];
    }
    acc[turn].push(entry);
    return acc;
  }, {});

  const getModelShort = (model) => model?.split('/')[1] || model;

  return (
    <div className="stage stage4">
      <h3 className="stage-title">Stage 4: Collaborative Refinement</h3>

      {collaborators.length >= 2 && (
        <div className="collaborators-info">
          <span className="collab-label">Collaboration between:</span>
          <span className="model-tag author">{getModelShort(collaborators[0])}</span>
          <span className="and">and</span>
          <span className="model-tag collaborator">{getModelShort(collaborators[1])}</span>
          {numTurns > 0 && <span className="turns-count">({numTurns} turns)</span>}
        </div>
      )}

      {dialogueHistory.length > 0 && (
        <div className="dialogue-controls">
          <button className="control-btn" onClick={expandAll}>
            Expand All
          </button>
          <button className="control-btn" onClick={collapseAll}>
            Collapse All
          </button>
        </div>
      )}

      <div className="dialogue-timeline">
        {Object.entries(groupedByTurn).map(([turnNum, entries]) => (
          <div key={turnNum} className="dialogue-round">
            <div className="round-header">Round {turnNum}</div>
            {entries.map((entry, idx) => {
              const globalIndex = dialogueHistory.indexOf(entry);
              const isExpanded = expandedTurns[globalIndex];
              const isAuthor = entry.role === 'author';

              return (
                <div
                  key={idx}
                  className={`dialogue-entry ${isAuthor ? 'author' : 'collaborator'}`}
                >
                  <div
                    className="entry-header"
                    onClick={() => toggleTurn(globalIndex)}
                  >
                    <span className="entry-model">
                      {isAuthor ? '📝' : '💡'} {getModelShort(entry.model)}
                    </span>
                    <span className="entry-role">
                      {isAuthor ? 'Author' : 'Collaborator'}
                    </span>
                    <span className="expand-icon">{isExpanded ? '−' : '+'}</span>
                  </div>
                  {isExpanded && (
                    <div className="entry-content markdown-content">
                      <ReactMarkdown>{entry.message}</ReactMarkdown>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}

        {isLoading && dialogueHistory.length === 0 && (
          <div className="dialogue-loading">
            <div className="spinner"></div>
            <span>Models are collaborating...</span>
          </div>
        )}

        {isLoading && dialogueHistory.length > 0 && (
          <div className="dialogue-loading inline">
            <div className="spinner small"></div>
            <span>Generating next turn...</span>
          </div>
        )}
      </div>

      {refinedScript && (
        <div className="refined-script-section">
          <h4 className="refined-script-header">
            <span className="script-icon">📜</span>
            Final Refined Script
            {refinedScript && refinedScript !== 'Unable to generate final script.' && (
              <button
                type="button"
                className="copy-btn"
                onClick={copyToClipboard}
                title={copyStatus === 'copied' ? 'Copied!' : 'Copy to clipboard'}
              >
                {copyStatus === 'copied' ? '✓' : copyStatus === 'error' ? '✗' : '📋'}
              </button>
            )}
            {refinedScript === 'Unable to generate final script.' && onRegenerateFinalScript && (
              <button
                className="regenerate-btn"
                onClick={onRegenerateFinalScript}
                disabled={isRegenerating}
              >
                {isRegenerating ? 'Regenerating...' : 'Retry Generation'}
              </button>
            )}
          </h4>

          {runtimeValidation && (
            <div className="runtime-validation">
              <div className={`validation-badge ${runtimeValidation.status}`}>
                {runtimeValidation.status === 'compliant' ? '✓' : runtimeValidation.status === 'too_short' ? '↑' : '↓'}
                <span className="validation-text">
                  Est. {runtimeValidation.estimated_runtime} min / Target {runtimeValidation.target_runtime} min
                </span>
                <span className="word-count">({runtimeValidation.word_count} words)</span>
              </div>
              {runtimeValidation.refinement_attempts > 0 && (
                <span className="refinement-note">
                  Refined {runtimeValidation.refinement_attempts}x to meet runtime
                </span>
              )}
            </div>
          )}

          <div className="refined-script-content markdown-content">
            {isRegenerating ? (
              <div className="regenerating-indicator">
                <div className="spinner"></div>
                <span>Regenerating final script...</span>
              </div>
            ) : (
              <ReactMarkdown>{refinedScript}</ReactMarkdown>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
