/**
 * API client for the LLM Council backend.
 */

const API_BASE = 'http://localhost:8001';

/**
 * Get auth headers from localStorage.
 */
function getAuthHeaders() {
  const token = localStorage.getItem('google_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Handle unauthorized responses by clearing auth and reloading.
 */
function handleUnauthorized(response) {
  if (response.status === 401) {
    localStorage.removeItem('google_token');
    localStorage.removeItem('user');
    window.location.reload();
    return true;
  }
  return false;
}

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
   * List all conversations.
   */
  async listConversations() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      headers: {
        ...getAuthHeaders(),
      },
    });
    if (handleUnauthorized(response)) return [];
    if (!response.ok) {
      throw new Error('Failed to list conversations');
    }
    return response.json();
  },

  /**
   * Create a new conversation.
   */
  async createConversation() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({}),
    });
    if (handleUnauthorized(response)) return null;
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
      {
        headers: {
          ...getAuthHeaders(),
        },
      }
    );
    if (handleUnauthorized(response)) return null;
    if (!response.ok) {
      throw new Error('Failed to get conversation');
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
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ content }),
      }
    );
    if (handleUnauthorized(response)) return null;
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
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ content }),
      }
    );

    if (handleUnauthorized(response)) return;
    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const event = parseSseData(line.slice(6));
          if (event) {
            onEvent(event.type, event);
          }
        }
      }
    }
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

    const token = localStorage.getItem('google_token');
    const url = new URL(
      `${API_BASE}/api/crawler/progress/${encodeURIComponent(targetUlid)}/${encodeURIComponent(String(version))}`
    );

    // EventSource does not support custom headers, so token must be query-based if required.
    if (token) {
      url.searchParams.set('token', token);
    }

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
        headers: {
          ...getAuthHeaders(),
        },
      }
    );

    if (handleUnauthorized(response)) return null;
    if (response.status === 404) return null;
    if (!response.ok) {
      throw new Error('Failed to get crawler status');
    }

    return response.json();
  },

  /**
   * Get current user info (validates token).
   */
  async getMe() {
    const response = await fetch(`${API_BASE}/api/me`, {
      headers: {
        ...getAuthHeaders(),
      },
    });
    if (handleUnauthorized(response)) return null;
    if (!response.ok) {
      throw new Error('Failed to get user info');
    }
    return response.json();
  },
};
