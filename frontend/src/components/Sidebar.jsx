import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  user,
  onLogout,
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>LLM Council</h1>
        <button className="new-conversation-btn" onClick={onNewConversation}>
          + New Conversation
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">No conversations yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
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
            </div>
          ))
        )}
      </div>

      {user && (
        <div className="sidebar-user">
          <div className="user-info">
            {user.picture && (
              <img
                src={user.picture}
                alt={user.name}
                className="user-avatar"
                referrerPolicy="no-referrer"
              />
            )}
            <div className="user-details">
              <div className="user-name">{user.name}</div>
              <div className="user-email">{user.email}</div>
            </div>
          </div>
          <button className="logout-btn" onClick={onLogout}>
            Logout
          </button>
        </div>
      )}
    </div>
  );
}
