/**
 * API client for the LLM Council backend.
 */

// Use relative URLs - Vite dev server proxies /api to the backend
const API_BASE = '';

export const getApiBase = () => API_BASE;

function parseSseData(rawData) {
  if (!rawData) return null;
  try {
    return JSON.parse(rawData);
  } catch (error) {
    console.error('Failed to parse SSE event:', error);
    return null;
  }
}

export const api = {
  /**
   * Get current authenticated user.
   */
  async getCurrentUser() {
    const response = await fetch(`${API_BASE}/api/auth/me`, {
      credentials: 'include',
    });
    if (!response.ok) {
      const error = new Error('Not authenticated');
      error.status = response.status;
      throw error;
    }
    return response.json();
  },

  /**
   * Check database connection status.
   */
  async checkDatabaseStatus() {
    try {
      const response = await fetch(`${API_BASE}/api/health/db`, {
        credentials: 'include',
      });
      if (!response.ok) {
        return { connected: false };
      }
      return response.json();
    } catch {
      return { connected: false };
    }
  },

  /**
   * Get database configuration (requires authentication).
   */
  async getDatabaseConfig() {
    const response = await fetch(`${API_BASE}/api/db/config`, {
      credentials: 'include',
    });
    if (!response.ok) {
      const error = new Error('Failed to get database config');
      error.status = response.status;
      throw error;
    }
    return response.json();
  },

  /**
   * List all conversations.
   */
  async listConversations() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      credentials: 'include',
    });
    if (!response.ok) {
      const error = new Error('Failed to list conversations');
      error.status = response.status;
      throw error;
    }
    return response.json();
  },

  /**
   * Create a new conversation.
   * @param {string} type - The conversation type ("council" or "movie_script")
   */
  async createConversation(type = 'council') {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ type }),
    });
    if (!response.ok) {
      throw new Error('Failed to create conversation');
    }
    return response.json();
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`,
      { credentials: 'include' }
    );
    if (!response.ok) {
      const error = new Error('Failed to get conversation');
      error.status = response.status;
      throw error;
    }
    return response.json();
  },

  /**
   * Delete a conversation.
   */
  async deleteConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`,
      {
        method: 'DELETE',
        credentials: 'include',
      }
    );
    if (!response.ok) {
      throw new Error('Failed to delete conversation');
    }
    return response.json();
  },

  /**
   * Read council model cookies and return council_models array if any are set.
   */
  _getCouncilModelsFromCookies() {
    const models = [];
    let hasAny = false;
    for (let i = 0; i < 4; i++) {
      const match = document.cookie.match(new RegExp('(^| )council_model_' + i + '=([^;]+)'));
      if (match) {
        models.push(decodeURIComponent(match[2]));
        hasAny = true;
      } else {
        models.push(null);
      }
    }
    return hasAny ? models.filter(m => m !== null) : null;
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content) {
    const body = { content };
    const councilModels = this._getCouncilModelsFromCookies();
    if (councilModels) {
      body.council_models = councilModels;
    }
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(body),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    return response.json();
  },

  /**
   * Send a message and receive streaming updates.
   * @param {string} conversationId - The conversation ID
   * @param {string} content - The message content
   * @param {function} onEvent - Callback function for each event: (eventType, data) => void
   * @returns {Promise<void>}
   */
  async sendMessageStream(conversationId, content, onEvent) {
    const body = { content };
    const councilModels = this._getCouncilModelsFromCookies();
    if (councilModels) {
      body.council_models = councilModels;
    }
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(body),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const event = JSON.parse(data);
            onEvent(event.type, event);
          } catch (e) {
            console.error('Failed to parse SSE event:', e, 'Data:', data.substring(0, 100));
          }
        }
      }
    }

    // Process any remaining data in the buffer
    if (buffer.startsWith('data: ')) {
      const data = buffer.slice(6);
      try {
        const event = JSON.parse(data);
        onEvent(event.type, event);
      } catch (e) {
        console.error('Failed to parse final SSE event:', e);
      }
    }
  },

  /**
   * Send a movie script request and receive streaming updates.
   * @param {string} conversationId - The conversation ID
   * @param {string} content - The movie idea/prompt
   * @param {number} numTurns - Number of collaboration turns (1-7)
   * @param {number} movieLength - Target movie length in minutes
   * @param {function} onEvent - Callback function for each event: (eventType, data) => void
   * @returns {Promise<void>}
   */
  async sendMovieScriptStream(conversationId, content, numTurns, movieLength, onEvent) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/movie-script/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ content, num_turns: numTurns, movie_length: movieLength }),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to generate movie script');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const event = JSON.parse(data);
            onEvent(event.type, event);
          } catch (e) {
            console.error('Failed to parse SSE event:', e, 'Data:', data.substring(0, 100));
          }
        }
      }
    }

    // Process any remaining data in the buffer
    if (buffer.startsWith('data: ')) {
      const data = buffer.slice(6);
      try {
        const event = JSON.parse(data);
        onEvent(event.type, event);
      } catch (e) {
        console.error('Failed to parse final SSE event:', e);
      }
    }
  },

  /**
   * Regenerate the final script for a movie script conversation.
   * @param {string} conversationId - The conversation ID
   * @returns {Promise<{status: string, refined_script: string}>}
   */
  async regenerateFinalScript(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/movie-script/regenerate-final`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || 'Failed to regenerate final script');
    }

    return response.json();
  },

  /**
   * Subscribe to crawler progress SSE updates.
   * @param {string} targetUlid - Target ULID
   * @param {string|number} version - Crawl version
   * @param {function} onEvent - Callback: (eventType, payload) => void
   * @returns {function} Unsubscribe function
   */
  subscribeToCrawlProgress(targetUlid, version, onEvent) {
    if (!targetUlid || version === undefined || version === null) {
      return () => {};
    }

    const url = new URL(
      `${API_BASE}/api/crawler/progress/${encodeURIComponent(targetUlid)}/${encodeURIComponent(String(version))}`,
      window.location.origin
    );

    const source = new EventSource(url.toString());

    source.onmessage = (event) => {
      const payload = parseSseData(event.data);
      if (payload) {
        onEvent(payload.type || 'progress', payload);
      }
    };

    const forwardEvent = (eventType) => (event) => {
      const payload = parseSseData(event.data);
      onEvent(eventType, payload || {});
    };

    source.addEventListener('progress', forwardEvent('progress'));
    source.addEventListener('status', forwardEvent('status'));
    source.addEventListener('complete', forwardEvent('complete'));

    source.onerror = (event) => {
      onEvent('error', event);
    };

    return () => {
      source.close();
    };
  },

  /**
   * Get crawler status for a target/version pair.
   */
  async getCrawlerStatus(targetUlid, version) {
    if (!targetUlid || version === undefined || version === null) {
      return null;
    }

    const response = await fetch(
      `${API_BASE}/api/crawler/status/${encodeURIComponent(targetUlid)}/${encodeURIComponent(String(version))}`,
      {
        credentials: 'include',
      }
    );

    if (response.status === 404) return null;
    if (!response.ok) {
      throw new Error('Failed to get crawler status');
    }

    return response.json();
  },

  // ===== Memory Explorer API (Admin Only) =====

  /**
   * Helper to extract error details from a response.
   * Tries to parse JSON error body, falls back to status text.
   */
  async _extractError(response, defaultMessage) {
    let errorMessage = defaultMessage;
    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorBody = await response.json();
        // Handle various API error formats
        errorMessage = errorBody.detail || errorBody.message || errorBody.error || defaultMessage;
      } else {
        // Try to get text if not JSON
        const text = await response.text();
        if (text && text.length < 200) {
          errorMessage = text;
        }
      }
    } catch {
      // If we can't parse the response, use default
    }
    const error = new Error(errorMessage);
    error.status = response.status;
    error.statusText = response.statusText;
    return error;
  },

  /**
   * Get list of agents with memories.
   * Requires admin or superadmin role.
   */
  async getMemoryAgents() {
    const response = await fetch(`${API_BASE}/api/memories/agents`, {
      credentials: 'include',
    });
    if (!response.ok) {
      throw await this._extractError(response, 'Failed to get agents');
    }
    return response.json();
  },

  /**
   * Search memories.
   * Requires admin or superadmin role.
   * @param {Object} params - Search parameters
   * @param {string} params.query - Search query
   * @param {string} params.scope - Scope: "network", "mine", or "agent:agent-name"
   * @param {number} params.limit - Max results (default 20)
   * @param {string} params.agent_id - Optional agent ID for X-Agent-ID header
   * @param {string} params.project_id - Optional project ID filter
   * @param {string[]} params.tags - Optional tags filter
   */
  async searchMemories(params) {
    const response = await fetch(`${API_BASE}/api/memories/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(params),
    });
    if (!response.ok) {
      throw await this._extractError(response, 'Failed to search memories');
    }
    return response.json();
  },

  /**
   * Get a specific memory by ID.
   * Requires admin or superadmin role.
   * @param {string} memoryId - Memory ID
   */
  async getMemory(memoryId) {
    const response = await fetch(`${API_BASE}/api/memories/${memoryId}`, {
      credentials: 'include',
    });
    if (!response.ok) {
      throw await this._extractError(response, 'Failed to get memory');
    }
    return response.json();
  },

  /**
   * Synthesize an answer from memory search results using Claude Opus 4.5.
   * Requires admin or superadmin role.
   * @param {Object} params - Synthesis parameters
   * @param {string} params.query - The original user query
   * @param {Object[]} params.memories - Array of memory objects from search results
   * @returns {Promise<{answer: string, model: string}>}
   */
  async synthesizeMemories(params) {
    const response = await fetch(`${API_BASE}/api/memories/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(params),
    });
    if (!response.ok) {
      throw await this._extractError(response, 'Failed to synthesize memories');
    }
    return response.json();
  },
};
