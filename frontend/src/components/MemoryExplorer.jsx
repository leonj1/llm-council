import { useState, useEffect } from 'react';
import { api } from '../api';
import { useToast } from './Toast';
import './MemoryExplorer.css';

/**
 * Format error message with HTTP status details
 */
function formatErrorMessage(err) {
  // Check for network errors
  if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
    return 'Network error: Unable to connect to the server. Please check your connection.';
  }

  // Check for HTTP status codes
  if (err.status) {
    const statusMessages = {
      400: 'Bad Request: Invalid search parameters',
      401: 'Unauthorized: Please log in again',
      403: 'Forbidden: You do not have permission to access memories',
      404: 'Not Found: The memory API endpoint was not found',
      429: 'Too Many Requests: Please wait a moment and try again',
      500: 'Server Error: Something went wrong on the server',
      502: 'Bad Gateway: Server is temporarily unavailable',
      503: 'Service Unavailable: Server is under maintenance',
    };
    const statusMsg = statusMessages[err.status] || `HTTP ${err.status}`;
    return err.message ? `${statusMsg}: ${err.message}` : statusMsg;
  }

  return err.message || 'An unexpected error occurred';
}

export default function MemoryExplorer() {
  // Search state
  const [query, setQuery] = useState('');
  const [scope, setScope] = useState('network');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [projectId, setProjectId] = useState('');
  const [tags, setTags] = useState('');
  
  // Data state
  const [agents, setAgents] = useState([]);
  const [results, setResults] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  
  // Loading/error state
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingAgents, setIsLoadingAgents] = useState(true);
  const [error, setError] = useState(null);

  // Toast notifications
  const toast = useToast();

  // Load agents on mount
  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setIsLoadingAgents(true);
      const response = await api.getMemoryAgents();
      // API returns { agents: [...] }, extract the array
      const agentList = response?.agents || response || [];
      setAgents(Array.isArray(agentList) ? agentList : []);
    } catch (err) {
      console.error('Failed to load agents:', err);
      // Show toast but don't block the UI
      toast.warning('Could not load agent list. You can still search manually.');
    } finally {
      setIsLoadingAgents(false);
    }
  };

  const handleSearch = async (e) => {
    // Prevent default form submission (important for both button click and Enter key)
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    
    if (!query.trim()) {
      toast.warning('Please enter a search query');
      return;
    }

    setIsLoading(true);
    setError(null);
    setExpandedId(null);

    try {
      // Build scope based on selection
      let searchScope = scope;
      if (scope === 'agent' && selectedAgent) {
        searchScope = `agent:${selectedAgent}`;
      }

      // Parse tags
      const tagList = tags
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0);

      const searchResults = await api.searchMemories({
        query: query.trim(),
        scope: searchScope,
        limit: 50,
        agent_id: selectedAgent || undefined,
        project_id: projectId.trim() || undefined,
        tags: tagList.length > 0 ? tagList : undefined,
      });

      // API returns { results: [{ memory: {...}, score, match_type }] }
      // Flatten to array of memory objects with score attached
      const rawResults = searchResults?.results || searchResults || [];
      const resultArray = (Array.isArray(rawResults) ? rawResults : []).map(item => {
        // Handle both wrapped { memory, score } and flat memory objects
        const memory = item?.memory || item || {};
        return {
          ...memory,
          // Ensure critical fields have safe defaults
          id: memory.id || `temp-${Date.now()}-${Math.random()}`,
          content: memory.content || '',
          agent_id: memory.agent_id || 'unknown',
          tags: Array.isArray(memory.tags) ? memory.tags : [],
          project_id: memory.project_id || null,
          created_at: memory.created_at || null,
          // Attach score/match_type from wrapper or memory itself
          score: item?.score ?? memory?.score,
          match_type: item?.match_type ?? memory?.match_type,
        };
      });
      setResults(resultArray);
      
      // Show success toast
      if (resultArray.length > 0) {
        toast.success(`Found ${resultArray.length} memor${resultArray.length === 1 ? 'y' : 'ies'}`);
      } else {
        toast.info('No memories found matching your search');
      }
    } catch (err) {
      console.error('Search failed:', err);
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      toast.error(errorMessage);
      // IMPORTANT: Do NOT clear results on error - keep previous results visible
      // setResults([]); <- removed to preserve existing results
    } finally {
      setIsLoading(false);
    }
  };

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleString();
    } catch {
      return dateStr;
    }
  };

  const truncateContent = (content, maxLength = 200) => {
    // Defensive check for null/undefined content
    if (!content) return '';
    const str = String(content);
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
  };

  return (
    <div className="memory-explorer">
      <div className="memory-header">
        <h1>🧠 Memory Explorer</h1>
        <p className="memory-subtitle">Search shared agent memories across the network</p>
      </div>

      <form className="memory-search-form" onSubmit={handleSearch}>
        <div className="search-row">
          <input
            type="text"
            className="search-input"
            placeholder="Search memories..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button 
            type="button" 
            className="search-btn"
            disabled={isLoading}
            onClick={handleSearch}
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="filters-row">
          <div className="filter-group">
            <label>Scope</label>
            <select 
              value={scope} 
              onChange={(e) => setScope(e.target.value)}
            >
              <option value="network">All Memories (Network)</option>
              <option value="agent">Specific Agent</option>
            </select>
          </div>

          {scope === 'agent' && (
            <div className="filter-group">
              <label>Agent</label>
              <select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                disabled={isLoadingAgents}
              >
                <option value="">Select agent...</option>
                {agents.map((agent) => {
                  // Handle both { id, name } and { agent_id } formats, plus plain strings
                  const agentId = agent?.id || agent?.agent_id || agent;
                  const agentName = agent?.name || agent?.agent_id || agent;
                  return (
                    <option key={agentId} value={agentId}>
                      {agentName}
                    </option>
                  );
                })}
              </select>
            </div>
          )}

          <div className="filter-group">
            <label>Project ID</label>
            <input
              type="text"
              placeholder="Optional"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label>Tags</label>
            <input
              type="text"
              placeholder="tag1, tag2, ..."
              value={tags}
              onChange={(e) => setTags(e.target.value)}
            />
          </div>
        </div>
      </form>

      {error && (
        <div className="memory-error">
          {error}
        </div>
      )}

      <div className="memory-results">
        {isLoading ? (
          <div className="memory-loading">
            <div className="loading-spinner"></div>
            <p>Searching memories...</p>
          </div>
        ) : results.length === 0 ? (
          <div className="memory-empty">
            {query ? 'No memories found matching your search.' : 'Enter a search query to find memories.'}
          </div>
        ) : (
          <>
            <div className="results-header">
              Found {results.length} memor{results.length === 1 ? 'y' : 'ies'}
            </div>
            {results.map((memory) => (
              <div 
                key={memory.id} 
                className={`memory-card ${expandedId === memory.id ? 'expanded' : ''}`}
                onClick={() => toggleExpand(memory.id)}
              >
                <div className="memory-card-header">
                  <div className="memory-meta">
                    <span className="memory-agent" title="Agent ID">
                      🤖 {memory.agent_id}
                    </span>
                    {memory.project_id && (
                      <span className="memory-project" title="Project ID">
                        📁 {memory.project_id}
                      </span>
                    )}
                    <span className="memory-date" title="Created at">
                      🕐 {formatDate(memory.created_at)}
                    </span>
                    {memory.score !== undefined && (
                      <span className="memory-score" title="Relevance score">
                        ⭐ {(memory.score * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                  <div className="memory-expand-icon">
                    {expandedId === memory.id ? '▼' : '▶'}
                  </div>
                </div>

                <div className="memory-content">
                  {expandedId === memory.id 
                    ? (memory.content || '') 
                    : truncateContent(memory.content || '')
                  }
                </div>

                {memory.tags && memory.tags.length > 0 && (
                  <div className="memory-tags">
                    {memory.tags.map((tag, idx) => (
                      <span key={idx} className="memory-tag">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
