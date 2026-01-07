import { useState, useEffect } from 'react';
import { api } from '../api';
import './DatabaseStatus.css';

export default function DatabaseStatus({ onClick, isLoggedIn }) {
  const [isConnected, setIsConnected] = useState(null);

  useEffect(() => {
    const checkStatus = async () => {
      const result = await api.checkDatabaseStatus();
      setIsConnected(result.connected);
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleClick = () => {
    if (isLoggedIn && onClick) {
      onClick();
    }
  };

  const clickableClass = isLoggedIn && onClick ? 'db-status-clickable' : '';

  if (isConnected === null) {
    return (
      <div
        className={`db-status db-status-checking ${clickableClass}`}
        onClick={handleClick}
        role={isLoggedIn ? 'button' : undefined}
        tabIndex={isLoggedIn ? 0 : undefined}
        onKeyDown={isLoggedIn ? (e) => e.key === 'Enter' && handleClick() : undefined}
      >
        <span className="db-status-dot"></span>
        <span className="db-status-text">Checking DB...</span>
      </div>
    );
  }

  return (
    <div
      className={`db-status ${isConnected ? 'db-status-connected' : 'db-status-disconnected'} ${clickableClass}`}
      onClick={handleClick}
      role={isLoggedIn ? 'button' : undefined}
      tabIndex={isLoggedIn ? 0 : undefined}
      onKeyDown={isLoggedIn ? (e) => e.key === 'Enter' && handleClick() : undefined}
    >
      <span className="db-status-dot"></span>
      <span className="db-status-text">
        {isConnected ? 'DB Connected' : 'DB Disconnected'}
      </span>
    </div>
  );
}
