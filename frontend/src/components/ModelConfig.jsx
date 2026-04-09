import { useState, useEffect, useRef } from 'react';
import { api, getApiBase } from '../api';
import './ModelConfig.css';

// Cookie helpers
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

function setCookie(name, value, days = 365) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
}

function deleteCookie(name) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
}

export default function ModelConfig() {
  const [councilModels, setCouncilModels] = useState([]);
  const [chairmanModel, setChairmanModel] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModels, setSelectedModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [searchTerms, setSearchTerms] = useState([]);
  const [openDropdown, setOpenDropdown] = useState(null);
  const dropdownRefs = useRef([]);

  useEffect(() => {
    loadData();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (openDropdown !== null) {
        const ref = dropdownRefs.current[openDropdown];
        if (ref && !ref.contains(event.target)) {
          setOpenDropdown(null);
        }
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [openDropdown]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const API_BASE = getApiBase();
      const [councilResp, availableResp] = await Promise.all([
        fetch(`${API_BASE}/api/models/council`, { credentials: 'include' }).then(r => {
          if (!r.ok) throw new Error('Failed to fetch council models');
          return r.json();
        }),
        fetch(`${API_BASE}/api/models/available`, { credentials: 'include' }).then(r => {
          if (!r.ok) throw new Error('Failed to fetch available models');
          return r.json();
        }),
      ]);

      const defaults = councilResp.council_models || [];
      setCouncilModels(defaults);
      setChairmanModel(councilResp.chairman_model || '');
      setAvailableModels(availableResp.models || []);

      // Initialize selections: cookie values take precedence over defaults
      const initial = defaults.map((defaultModel, i) => {
        const cookieVal = getCookie(`council_model_${i}`);
        return cookieVal || defaultModel;
      });
      setSelectedModels(initial);
      setSearchTerms(initial.map(() => ''));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleModelChange = (index, model) => {
    setSelectedModels(prev => {
      const next = [...prev];
      next[index] = model;
      return next;
    });
    setOpenDropdown(null);
    setSearchTerms(prev => {
      const next = [...prev];
      next[index] = '';
      return next;
    });
  };

  const handleSearchChange = (index, value) => {
    setSearchTerms(prev => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  };

  const handleSave = () => {
    selectedModels.forEach((model, i) => {
      setCookie(`council_model_${i}`, model);
    });
    setSuccessMessage('Configuration saved successfully!');
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleReset = () => {
    councilModels.forEach((_, i) => {
      deleteCookie(`council_model_${i}`);
    });
    setSelectedModels([...councilModels]);
    setSearchTerms(councilModels.map(() => ''));
    setSuccessMessage('Reset to default models.');
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const getFilteredModels = (index) => {
    const term = (searchTerms[index] || '').toLowerCase();
    if (!term) return availableModels;
    return availableModels.filter(m => m.toLowerCase().includes(term));
  };

  const isModified = (index) => {
    return selectedModels[index] !== councilModels[index];
  };

  if (loading) {
    return (
      <div className="model-config">
        <div className="model-config-loading">
          <div className="loading-spinner"></div>
          <p>Loading model configuration...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="model-config">
        <div className="model-config-error">
          <h3>Error Loading Models</h3>
          <p>{error}</p>
          <button className="model-config-retry-btn" onClick={loadData}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="model-config">
      <div className="model-config-header">
        <h2>Council Model Configuration</h2>
        <p className="model-config-subtitle">
          Configure which LLM models serve on the council. Changes are saved to browser cookies and override the server defaults.
        </p>
      </div>

      {successMessage && (
        <div className="model-config-success">{successMessage}</div>
      )}

      <div className="model-config-info">
        <span className="model-config-info-label">Chairman Model:</span>
        <span className="model-config-info-value">{chairmanModel}</span>
      </div>

      <div className="model-config-list">
        {selectedModels.map((model, index) => {
          const filtered = getFilteredModels(index);
          return (
            <div key={index} className="model-config-slot">
              <label className="model-config-label">
                Council Member {index + 1}
                {isModified(index) && <span className="model-config-modified">modified</span>}
              </label>
              <div
                className="model-config-select-wrapper"
                ref={el => dropdownRefs.current[index] = el}
              >
                <div
                  className={`model-config-select-trigger ${openDropdown === index ? 'open' : ''}`}
                  onClick={() => setOpenDropdown(openDropdown === index ? null : index)}
                >
                  <span className="model-config-select-value">{model}</span>
                  <span className="model-config-select-arrow">{openDropdown === index ? '\u25B2' : '\u25BC'}</span>
                </div>
                {openDropdown === index && (
                  <div className="model-config-dropdown">
                    <input
                      type="text"
                      className="model-config-search"
                      placeholder="Search models..."
                      value={searchTerms[index] || ''}
                      onChange={(e) => handleSearchChange(index, e.target.value)}
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div className="model-config-options">
                      {filtered.length === 0 ? (
                        <div className="model-config-no-results">No models found</div>
                      ) : (
                        filtered.map(m => (
                          <div
                            key={m}
                            className={`model-config-option ${m === model ? 'selected' : ''} ${m === councilModels[index] ? 'default' : ''}`}
                            onClick={() => handleModelChange(index, m)}
                          >
                            <span>{m}</span>
                            {m === councilModels[index] && <span className="model-config-default-badge">default</span>}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="model-config-actions">
        <button className="model-config-save-btn" onClick={handleSave}>
          Save Configuration
        </button>
        <button className="model-config-reset-btn" onClick={handleReset}>
          Reset to Defaults
        </button>
      </div>
    </div>
  );
}
