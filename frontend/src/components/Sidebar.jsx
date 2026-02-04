import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../api';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isMobile,
  collapsed,
  onToggleCollapse,
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [showDropdown, setShowDropdown] = useState(false);
  const [openMenuId, setOpenMenuId] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const dropdownRef = useRef(null);
  const menuRef = useRef(null);

  // Check user role for admin features
  useEffect(() => {
    const fetchUserRole = async () => {
      try {
        const user = await api.getCurrentUser();
        setUserRole(user.role || 'user');
      } catch {
        setUserRole(null);
      }
    };
    fetchUserRole();
  }, []);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOpenMenuId(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleNewConversation = (type) => {
    onNewConversation(type);
    setShowDropdown(false);
  };

  const handleMenuClick = (e, convId) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === convId ? null : convId);
  };

  const handleDelete = (e, convId) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this conversation?')) {
      onDeleteConversation(convId);
    }
    setOpenMenuId(null);
  };

  return (
    <div className={`sidebar ${isMobile ? 'mobile' : ''} ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-header-top">
          {!collapsed && <h1>LLM Council</h1>}
          {!isMobile && (
            <button
              className="collapse-toggle-btn"
              onClick={onToggleCollapse}
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {collapsed ? '»' : '«'}
            </button>
          )}
        </div>
        {!collapsed && (
          <div className="new-conversation-dropdown" ref={dropdownRef}>
            <button
              className="new-conversation-btn"
              onClick={() => setShowDropdown(!showDropdown)}
            >
              + New
            </button>
          {showDropdown && (
            <div className="dropdown-menu">
              <button
                className="dropdown-item"
                onClick={() => handleNewConversation('council')}
              >
                <span className="dropdown-icon">💬</span>
                <span className="dropdown-text">
                  <span className="dropdown-title">New Conversation</span>
                  <span className="dropdown-desc">Ask the council a question</span>
                </span>
              </button>
              <button
                className="dropdown-item"
                onClick={() => handleNewConversation('movie_script')}
              >
                <span className="dropdown-icon">🎬</span>
                <span className="dropdown-text">
                  <span className="dropdown-title">New Movie Script</span>
                  <span className="dropdown-desc">Collaborative script writing</span>
                </span>
              </button>
            </div>
          )}
          </div>
        )}
      </div>

      <div className={`conversation-list ${isMobile ? 'cards' : ''} ${collapsed ? 'collapsed' : ''}`}>
        {conversations.length === 0 ? (
          !collapsed && (
            <div className="no-conversations">
              <p>No conversations yet</p>
              <p className="no-conversations-hint">Tap "+ New" to get started</p>
            </div>
          )
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${isMobile ? 'card' : ''} ${
                conv.id === currentConversationId ? 'active' : ''
              } ${collapsed ? 'collapsed' : ''}`}
              onClick={() => onSelectConversation(conv.id)}
              title={collapsed ? (conv.title || 'New Conversation') : undefined}
            >
              <div className="conversation-type-icon">
                {conv.type === 'movie_script' ? '🎬' : '💬'}
              </div>
              {!collapsed && (
                <>
                  <div className="conversation-info">
                    <div className="conversation-title">
                      {conv.title || 'New Conversation'}
                    </div>
                    <div className="conversation-meta">
                      {conv.message_count} messages
                    </div>
                  </div>
                  <div
                    className="conversation-menu-wrapper"
                    ref={openMenuId === conv.id ? menuRef : null}
                  >
                    <button
                      className="conversation-menu-btn"
                      onClick={(e) => handleMenuClick(e, conv.id)}
                      aria-label="Conversation options"
                    >
                      ⋮
                    </button>
                    {openMenuId === conv.id && (
                      <div className="conversation-menu">
                        <button
                          className="conversation-menu-item delete"
                          onClick={(e) => handleDelete(e, conv.id)}
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    )}
                  </div>
                  {isMobile && (
                    <div className="conversation-arrow">›</div>
                  )}
                </>
              )}
            </div>
          ))
        )}
      </div>

      {/* Admin Navigation */}
      {(userRole === 'admin' || userRole === 'superadmin') && !collapsed && (
        <div className="sidebar-admin-nav">
          <div className="admin-nav-label">Admin</div>
          <button
            className={`admin-nav-item ${location.pathname === '/memories' ? 'active' : ''}`}
            onClick={() => navigate('/memories')}
          >
            <span className="admin-nav-icon">🧠</span>
            <span className="admin-nav-text">Memory Explorer</span>
          </button>
        </div>
      )}
      {(userRole === 'admin' || userRole === 'superadmin') && collapsed && (
        <div className="sidebar-admin-nav collapsed">
          <button
            className={`admin-nav-item collapsed ${location.pathname === '/memories' ? 'active' : ''}`}
            onClick={() => navigate('/memories')}
            title="Memory Explorer"
          >
            <span className="admin-nav-icon">🧠</span>
          </button>
        </div>
      )}
    </div>
  );
}
