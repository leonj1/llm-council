/**
 * API client for the LLM Council backend.
 */

// Use relative URLs for production, absolute for development
const API_BASE = import.meta.env.DEV ? 'http://localhost:8004' : '';

export const getApiBase = () => API_BASE;

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
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ content }),
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
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ content }),
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
};
