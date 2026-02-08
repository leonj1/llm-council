import { useState, useEffect } from 'react';
import { api } from '../api';
import { useToast } from './Toast';
import { parseMemoryResponse } from '../utils/parseMemoryResponse';
import RenderMarkdown from './RenderMarkdown';
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
  const [isSourcesExpanded, setIsSourcesExpanded] = useState(false);
  
  // AI Synthesis state
  const [aiAnswer, setAiAnswer] = useState(null);
  const [aiModel, setAiModel] = useState(null);
  const [memoriesUsed, setMemoriesUsed] = useState(0);
  const [memoriesTotal, setMemoriesTotal] = useState(0);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [synthesisError, setSynthesisError] = useState(null);
  
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
    setIsSourcesExpanded(false);
    // Clear previous AI answer when starting new search
    setAiAnswer(null);
    setAiModel(null);
    setMemoriesUsed(0);
    setMemoriesTotal(0);
    setSynthesisError(null);

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

      // Use the robust parser to handle all edge cases safely
      const parsed = parseMemoryResponse(searchResults);
      
      // Convert ParsedMemory objects to the format expected by the component
      // (maintaining snake_case for backwards compatibility with template)
      const resultArray = parsed.results.map(memory => ({
        id: memory.id,
        agent_id: memory.agentId,
        content: memory.content,
        embedding: memory.embedding,
        project_id: memory.projectId,
        tags: memory.tags,
        tsvector_content: memory.tsvectorContent,
        created_at: memory.createdAt,
        updated_at: memory.updatedAt,
        score: memory.score,
        match_type: memory.matchType,
      }));
      
      setResults(resultArray);
      
      // Show success toast
      if (resultArray.length > 0) {
        toast.success(`Found ${resultArray.length} memor${resultArray.length === 1 ? 'y' : 'ies'}`);
        
        // Automatically synthesize answer if we have results
        synthesizeAnswer(query.trim(), resultArray);
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

  /**
   * Synthesize an AI answer from the memory results using Claude Opus 4.5
   */
  const synthesizeAnswer = async (searchQuery, memories) => {
    if (!memories || memories.length === 0) {
      return;
    }

    setIsSynthesizing(true);
    setSynthesisError(null);

    try {
      const response = await api.synthesizeMemories({
        query: searchQuery,
        memories: memories,
      });

      setAiAnswer(response.answer);
      setAiModel(response.model);
      setMemoriesUsed(response.memories_used ?? memories.length);
      setMemoriesTotal(response.memories_total ?? memories.length);
    } catch (err) {
      console.error('Synthesis failed:', err);
      const errorMessage = formatErrorMessage(err);
      setSynthesisError(errorMessage);
      // Don't show toast for synthesis errors - just show inline error
    } finally {
      setIsSynthesizing(false);
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
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !isLoading) {
                e.preventDefault();
                handleSearch(e);
              }
            }}
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

      {/* AI Synthesis Section */}
      {(isSynthesizing || aiAnswer || synthesisError) && (
        <div className="ai-answer-section">
          <div className="ai-answer-header">
            <span className="ai-answer-icon">✨</span>
            <h2>AI Answer</h2>
            {aiModel && <span className="ai-model-badge">{aiModel.split('/').pop()}</span>}
            {memoriesUsed > 0 && memoriesTotal > 0 && (
              <span className="ai-memories-badge" title="High-quality memories used for synthesis">
                {memoriesUsed === memoriesTotal 
                  ? `${memoriesUsed} memor${memoriesUsed === 1 ? 'y' : 'ies'}`
                  : `${memoriesUsed} of ${memoriesTotal} (filtered by relevance)`
                }
              </span>
            )}
          </div>
          
          {isSynthesizing ? (
            <div className="ai-answer-loading">
              <div className="loading-spinner"></div>
              <p>Claude is analyzing memories and synthesizing an answer...</p>
            </div>
          ) : synthesisError ? (
            <div className="ai-answer-error">
              <p>Failed to generate AI answer: {synthesisError}</p>
              <button 
                className="retry-btn"
                onClick={() => synthesizeAnswer(query, results)}
              >
                Retry
              </button>
            </div>
          ) : aiAnswer ? (
            <div className="ai-answer-content">
              <RenderMarkdown content={aiAnswer} forceMarkdown={true} />
            </div>
          ) : null}
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
              <button
                type="button"
                className="sources-toggle"
                onClick={() => setIsSourcesExpanded(!isSourcesExpanded)}
                aria-expanded={isSourcesExpanded}
                aria-label={isSourcesExpanded ? 'Collapse sources' : 'Expand sources'}
              >
                <span>
                  {aiAnswer ? (
                    <>📚 Sources ({results.length} memor{results.length === 1 ? 'y' : 'ies'})</>
                  ) : (
                    <>Found {results.length} memor{results.length === 1 ? 'y' : 'ies'}</>
                  )}
                </span>
                <span className="sources-toggle-icon">{isSourcesExpanded ? '▼' : '▶'}</span>
              </button>
            </div>
            {isSourcesExpanded && (
              results.map((memory) => (
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
                    {expandedId === memory.id ? (
                      <RenderMarkdown content={memory.content || ''} />
                    ) : (
                      truncateContent(memory.content || '')
                    )}
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
              ))
            )}
            {!isSourcesExpanded && (
              <div className="sources-collapsed-hint">
                Sources are collapsed. Click to expand.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
