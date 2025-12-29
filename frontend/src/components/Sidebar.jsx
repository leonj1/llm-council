import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  isMobile,
}) {
  return (
    <div className={`sidebar ${isMobile ? 'mobile' : ''}`}>
      <div className="sidebar-header">
        <h1>LLM Council</h1>
        <button className="new-conversation-btn" onClick={onNewConversation}>
          + New Conversation
        </button>
      </div>

      <div className={`conversation-list ${isMobile ? 'cards' : ''}`}>
        {conversations.length === 0 ? (
          <div className="no-conversations">
            <p>No conversations yet</p>
            <p className="no-conversations-hint">Tap "New Conversation" to get started</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${isMobile ? 'card' : ''} ${
                conv.id === currentConversationId ? 'active' : ''
              }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-title">
                {conv.title || 'New Conversation'}
              </div>
              <div className="conversation-meta">
                {conv.message_count} messages
              </div>
              {isMobile && (
                <div className="conversation-arrow">›</div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
