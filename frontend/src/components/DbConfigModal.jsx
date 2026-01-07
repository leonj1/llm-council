import { useState, useEffect } from 'react';
import { api } from '../api';
import './DbConfigModal.css';

export default function DbConfigModal({ isOpen, onClose }) {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      setError(null);
      api.getDatabaseConfig()
        .then(data => {
          setConfig(data);
          setLoading(false);
        })
        .catch(err => {
          if (err.status === 401) {
            setError('You must be logged in to view database configuration.');
          } else {
            setError('Failed to load database configuration.');
          }
          setLoading(false);
        });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="db-config-overlay" onClick={onClose}>
      <div className="db-config-modal" onClick={e => e.stopPropagation()}>
        <div className="db-config-header">
          <h2>Database Configuration</h2>
          <button className="db-config-close" onClick={onClose}>&times;</button>
        </div>
        <div className="db-config-body">
          {loading && <div className="db-config-loading">Loading...</div>}
          {error && <div className="db-config-error">{error}</div>}
          {config && (
            <table className="db-config-table">
              <tbody>
                <tr>
                  <td className="db-config-label">Status</td>
                  <td>
                    <span className={`db-config-status ${config.connected ? 'connected' : 'disconnected'}`}>
                      {config.connected ? 'Connected' : 'Disconnected'}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="db-config-label">Host</td>
                  <td><code>{config.host || '(not set)'}</code></td>
                </tr>
                <tr>
                  <td className="db-config-label">Port</td>
                  <td><code>{config.port}</code></td>
                </tr>
                <tr>
                  <td className="db-config-label">User</td>
                  <td><code>{config.user || '(not set)'}</code></td>
                </tr>
                <tr>
                  <td className="db-config-label">Database</td>
                  <td><code>{config.database || '(not set)'}</code></td>
                </tr>
                <tr>
                  <td className="db-config-label">Password</td>
                  <td><code>{config.password}</code></td>
                </tr>
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
