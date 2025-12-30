import ReactMarkdown from 'react-markdown';
import './Stage3MovieScript.css';

export default function Stage3MovieScript({ selection }) {
  if (!selection) {
    return null;
  }

  const winnerShort = selection.winning_model?.split('/')[1] || selection.winning_model;
  const collaborators = selection.collaborators || [];

  return (
    <div className="stage stage3-movie-script">
      <h3 className="stage-title">Stage 3: Script Selection</h3>

      <div className="selection-summary">
        <div className="winner-badge">
          <span className="trophy">🏆</span>
          <span className="winner-label">Winning Script</span>
        </div>
        <div className="winner-model">by {winnerShort}</div>
      </div>

      <div className="selection-rationale">
        <h4>Selection Rationale</h4>
        <div className="markdown-content">
          <ReactMarkdown>{selection.selection_rationale}</ReactMarkdown>
        </div>
      </div>

      {collaborators.length >= 2 && (
        <div className="collaborators-preview">
          <h4>Stage 4 Collaborators</h4>
          <div className="collaborator-tags">
            <span className="collaborator-tag author">
              {collaborators[0]?.split('/')[1] || collaborators[0]}
              <span className="role-label">Author</span>
            </span>
            <span className="plus">+</span>
            <span className="collaborator-tag collaborator">
              {collaborators[1]?.split('/')[1] || collaborators[1]}
              <span className="role-label">Collaborator</span>
            </span>
          </div>
        </div>
      )}

      <details className="winning-script-details">
        <summary>View Winning Script</summary>
        <div className="winning-script-content markdown-content">
          <ReactMarkdown>{selection.winning_script}</ReactMarkdown>
        </div>
      </details>
    </div>
  );
}
