import { useState, useEffect } from 'react';
import { api } from '../api';
import './MemoryExplorer.css';

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

  // Load agents on mount
  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setIsLoadingAgents(true);
      const agentList = await api.getMemoryAgents();
      setAgents(agentList);
    } catch (err) {
      console.error('Failed to load agents:', err);
      // Don't block the UI if agents fail to load
    } finally {
      setIsLoadingAgents(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a search query');
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

      setResults(searchResults.results || searchResults || []);
    } catch (err) {
      console.error('Search failed:', err);
      setError(err.message || 'Failed to search memories');
      setResults([]);
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
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
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
            type="submit" 
            className="search-btn"
            disabled={isLoading}
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
                {agents.map((agent) => (
                  <option key={agent.agent_id || agent} value={agent.agent_id || agent}>
                    {agent.agent_id || agent}
                  </option>
                ))}
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
                    ? memory.content 
                    : truncateContent(memory.content)
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
