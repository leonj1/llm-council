import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api';
import MemoryExplorer from '../components/MemoryExplorer';
import './MemoriesPage.css';

export default function MemoriesPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const userData = await api.getCurrentUser();
      
      // Check if user has admin access
      const role = userData.role || 'user';
      if (role !== 'admin' && role !== 'superadmin') {
        setError('Access denied. Admin privileges required.');
        setUser(null);
      } else {
        setUser(userData);
      }
    } catch (err) {
      // Not authenticated
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="memories-page">
        <div className="memories-loading">
          <div className="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="memories-page">
        <div className="memories-access-denied">
          <h2>🔒 Access Denied</h2>
          <p>{error}</p>
          <Link to="/chat" className="back-link">← Back to Chat</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="memories-page">
      <nav className="memories-nav">
        <Link to="/chat" className="nav-back">← Back to Chat</Link>
        <div className="nav-user">
          {user?.picture && (
            <img src={user.picture} alt="" className="nav-avatar" />
          )}
          <span className="nav-name">{user?.name}</span>
          <span className="nav-role">{user?.role}</span>
        </div>
      </nav>
      <MemoryExplorer />
    </div>
  );
}
