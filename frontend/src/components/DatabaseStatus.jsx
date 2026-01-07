import { useState, useEffect } from 'react';
import { api } from '../api';
import './DatabaseStatus.css';

export default function DatabaseStatus() {
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

  if (isConnected === null) {
    return (
      <div className="db-status db-status-checking">
        <span className="db-status-dot"></span>
        <span className="db-status-text">Checking DB...</span>
      </div>
    );
  }

  return (
    <div className={`db-status ${isConnected ? 'db-status-connected' : 'db-status-disconnected'}`}>
      <span className="db-status-dot"></span>
      <span className="db-status-text">
        {isConnected ? 'DB Connected' : 'DB Disconnected'}
      </span>
    </div>
  );
}
