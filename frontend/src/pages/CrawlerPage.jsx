import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api';
import './CrawlerPage.css';

// Simple ULID generator
function generateULID() {
  const ENCODING = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
  const ENCODING_LEN = ENCODING.length;
  
  // Timestamp (10 chars)
  let timestamp = Date.now();
  let timestampChars = '';
  for (let i = 0; i < 10; i++) {
    timestampChars = ENCODING[timestamp % ENCODING_LEN] + timestampChars;
    timestamp = Math.floor(timestamp / ENCODING_LEN);
  }
  
  // Randomness (16 chars)
  let randomChars = '';
  const randomBytes = crypto.getRandomValues(new Uint8Array(16));
  for (let i = 0; i < 16; i++) {
    randomChars += ENCODING[randomBytes[i] % ENCODING_LEN];
  }
  
  return timestampChars + randomChars;
}

// Check if URL is YouTube
function isYouTubeUrl(url) {
  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.toLowerCase();
    return hostname.includes('youtube.com') || hostname.includes('youtu.be');
  } catch {
    return false;
  }
}

// Check if URL is valid
function isValidUrl(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

// Extractor service URLs - configurable via environment variables with production defaults
const YOUTUBE_EXTRACTOR_BASE = import.meta.env.VITE_YOUTUBE_EXTRACTOR_BASE || 'https://crawl-youtube-extractor-production.up.railway.app';
const URL_EXTRACTOR_BASE = import.meta.env.VITE_URL_EXTRACTOR_BASE || 'https://crawl-url-extractor-production.up.railway.app';

export default function CrawlerPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Extraction state
  const [url, setUrl] = useState('');
  const [depth, setDepth] = useState(2);
  const [extracting, setExtracting] = useState(false);
  const [progress, setProgress] = useState([]);
  const [result, setResult] = useState(null);
  const [extractionError, setExtractionError] = useState(null);
  
  const eventSourceRef = useRef(null);
  const progressContainerRef = useRef(null);
  const pollingTimeoutRef = useRef(null);

  useEffect(() => {
    checkAuth();
    return () => {
      // Cleanup SSE on unmount
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      // Cleanup polling on unmount
      if (pollingTimeoutRef.current) {
        clearTimeout(pollingTimeoutRef.current);
      }
    };
  }, []);

  // Auto-scroll progress
  useEffect(() => {
    if (progressContainerRef.current) {
      progressContainerRef.current.scrollTop = progressContainerRef.current.scrollHeight;
    }
  }, [progress]);

  const checkAuth = async () => {
    try {
      const userData = await api.getCurrentUser();
      const role = userData.role || 'user';
      if (role !== 'admin' && role !== 'superadmin') {
        setError('Access denied. Admin privileges required.');
        setUser(null);
      } else {
        setUser(userData);
      }
    } catch {
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Reset state
    setExtractionError(null);
    setProgress([]);
    setResult(null);
    
    // Validate URL
    if (!url.trim()) {
      setExtractionError('Please enter a URL');
      return;
    }

    // Check if valid URL
    if (!isValidUrl(url)) {
      setExtractionError('Please enter a valid URL');
      return;
    }

    // Start extraction
    setExtracting(true);
    const targetUlid = generateULID();
    const isYouTube = isYouTubeUrl(url);

    try {
      if (isYouTube) {
        // YouTube extraction with SSE
        await handleYouTubeExtraction(targetUlid);
      } else {
        // Regular URL extraction with polling
        await handleUrlExtraction(targetUlid);
      }
    } catch (err) {
      console.error('Extraction error:', err);
      setExtractionError(err.message || 'Failed to start extraction');
      setExtracting(false);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (pollingTimeoutRef.current) {
        clearTimeout(pollingTimeoutRef.current);
      }
    }
  };

  const handleYouTubeExtraction = async (targetUlid) => {
    // Note: Extractor endpoints are intentionally public (no auth required).
    // They use ULID-based tracking for job isolation instead of user authentication.
    const version = 1;

    // Start SSE connection for progress FIRST
    const progressUrl = `${YOUTUBE_EXTRACTOR_BASE}/extract/${targetUlid}/${version}/progress`;
    const eventSource = new EventSource(progressUrl);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setProgress(prev => [...prev, data]);

        // Check for completion
        if (data.status === 'complete' || data.status === 'completed') {
          setResult(data);
          eventSource.close();
          setExtracting(false);
        } else if (data.status === 'error' || data.status === 'failed') {
          setExtractionError(data.message || data.error || 'Extraction failed');
          eventSource.close();
          setExtracting(false);
        }
      } catch (parseErr) {
        console.error('Failed to parse SSE event:', parseErr);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      // Don't set error immediately - could just be connection closing normally
      if (eventSource.readyState === EventSource.CLOSED) {
        // Check if we already have a result before setting error
        setExtracting(currentExtracting => {
          if (currentExtracting) {
            setExtractionError('Connection to progress stream lost');
          }
          return false;
        });
      }
    };

    // Now trigger the extraction
    const response = await fetch(`${YOUTUBE_EXTRACTOR_BASE}/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        youtube_url: url,
        target_ulid: targetUlid,
        version: version,
        bucket: 'crawler-extractions',
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
    }

    // Response might contain immediate result or just acknowledgment
    const data = await response.json();
    if (data.status === 'complete' || data.status === 'completed') {
      setResult(data);
      eventSource.close();
      setExtracting(false);
    }
  };

  const handleUrlExtraction = async (targetUlid) => {
    // Note: Extractor endpoints are intentionally public (no auth required).
    // They use ULID-based tracking for job isolation instead of user authentication.

    // Add initial progress message
    setProgress([{ status: 'started', message: 'Submitting URL for extraction...' }]);

    // Submit URL for extraction
    const response = await fetch(`${URL_EXTRACTOR_BASE}/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: url,
        target_ulid: targetUlid,
        bucket: 'crawler-extractions',
        depth: depth,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
    }

    const submitData = await response.json();
    setProgress(prev => [...prev, { status: 'processing', message: 'Extraction submitted, polling for status...' }]);

    // Check if already complete
    if (submitData.status === 'complete' || submitData.status === 'completed') {
      setResult(submitData);
      setExtracting(false);
      return;
    }

    // Start polling for status using recursive setTimeout to prevent overlapping requests
    const maxPolls = 120; // 2 minutes at 1 second intervals

    const pollStatus = async (pollCount) => {
      if (pollCount > maxPolls) {
        setExtractionError('Extraction timed out');
        setExtracting(false);
        return;
      }

      try {
        const statusResponse = await fetch(`${URL_EXTRACTOR_BASE}/status/${targetUlid}`);

        if (!statusResponse.ok) {
          // 404 means still processing, schedule next poll
          if (statusResponse.status === 404) {
            pollingTimeoutRef.current = setTimeout(() => pollStatus(pollCount + 1), 1000);
            return;
          }
          const errorData = await statusResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || errorData.message || `HTTP ${statusResponse.status}`);
        }

        const statusData = await statusResponse.json();

        // Update progress using functional updater to avoid stale closure
        setProgress(prev => {
          const lastStatus = prev[prev.length - 1]?.status;
          if (statusData.status && statusData.status !== lastStatus) {
            return [...prev, statusData];
          }
          return prev;
        });

        // Check for completion
        if (statusData.status === 'complete' || statusData.status === 'completed') {
          setResult(statusData);
          setExtracting(false);
        } else if (statusData.status === 'error' || statusData.status === 'failed') {
          setExtractionError(statusData.message || statusData.error || 'Extraction failed');
          setExtracting(false);
        } else {
          // Still processing, schedule next poll
          pollingTimeoutRef.current = setTimeout(() => pollStatus(pollCount + 1), 1000);
        }
      } catch (pollErr) {
        console.error('Polling error:', pollErr);
        setExtractionError(pollErr.message || 'Failed to check extraction status');
        setExtracting(false);
      }
    };

    // Start first poll
    pollingTimeoutRef.current = setTimeout(() => pollStatus(1), 1000);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'started':
      case 'processing':
      case 'downloading':
      case 'transcribing':
      case 'extracting':
      case 'crawling':
      case 'pending':
        return '⏳';
      case 'complete':
      case 'completed':
        return '✅';
      case 'error':
      case 'failed':
        return '❌';
      default:
        return '📋';
    }
  };

  if (loading) {
    return (
      <div className="crawler-page">
        <div className="crawler-loading">
          <div className="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="crawler-page">
        <div className="crawler-access-denied">
          <h2>🔒 Access Denied</h2>
          <p>{error}</p>
          <Link to="/chat" className="back-link">← Back to Chat</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="crawler-page">
      <nav className="crawler-nav">
        <Link to="/chat" className="nav-back">← Back to Chat</Link>
        <div className="nav-user">
          {user?.picture && (
            <img src={user.picture} alt="" className="nav-avatar" />
          )}
          <span className="nav-name">{user?.name}</span>
          <span className="nav-role">{user?.role}</span>
        </div>
      </nav>
      
      <div className="crawler-content">
        <div className="crawler-header">
          <h1>🕷️ Content Crawler</h1>
          <p>Extract content from YouTube videos and web pages</p>
        </div>
        
        <form className="crawler-form" onSubmit={handleSubmit}>
          <div className="url-input-group">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste a YouTube or web page URL..."
              className="url-input"
              disabled={extracting}
            />
            <button 
              type="submit" 
              className="extract-btn"
              disabled={extracting || !url.trim()}
            >
              {extracting ? 'Extracting...' : 'Extract'}
            </button>
          </div>
          
          {/* Depth selector - only show for non-YouTube URLs */}
          {url.trim() && isValidUrl(url) && !isYouTubeUrl(url) && (
            <div className="depth-selector">
              <label htmlFor="depth-select">Crawl Depth:</label>
              <select
                id="depth-select"
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
                disabled={extracting}
                className="depth-select"
              >
                {[1, 2, 3, 4, 5].map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          )}

          {extractionError && (
            <div className="extraction-error">
              <span className="error-icon">⚠️</span>
              {extractionError}
            </div>
          )}
        </form>
        
        {progress.length > 0 && (
          <div className="progress-section">
            <h3>Progress</h3>
            <div className="progress-container" ref={progressContainerRef}>
              {progress.map((item, idx) => (
                <div key={idx} className={`progress-item status-${item.status}`}>
                  <span className="progress-icon">{getStatusIcon(item.status)}</span>
                  <span className="progress-status">{item.status}</span>
                  {item.message && (
                    <span className="progress-message">{item.message}</span>
                  )}
                  {item.step && (
                    <span className="progress-step">{item.step}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {result && (
          <div className="result-section">
            <h3>✅ Extraction Complete</h3>
            <div className="result-card">
              {result.title && (
                <div className="result-field">
                  <label>Title</label>
                  <p>{result.title}</p>
                </div>
              )}
              {result.channel && (
                <div className="result-field">
                  <label>Channel</label>
                  <p>{result.channel}</p>
                </div>
              )}
              {result.duration && (
                <div className="result-field">
                  <label>Duration</label>
                  <p>{result.duration}</p>
                </div>
              )}
              {result.transcript_length && (
                <div className="result-field">
                  <label>Transcript Length</label>
                  <p>{result.transcript_length.toLocaleString()} characters</p>
                </div>
              )}
              {result.s3_path && (
                <div className="result-field">
                  <label>Saved To</label>
                  <p className="result-path">{result.s3_path}</p>
                </div>
              )}
              {result.memory_id && (
                <div className="result-field">
                  <label>Memory ID</label>
                  <p className="result-path">{result.memory_id}</p>
                </div>
              )}
              <p className="result-note">
                📝 Content saved to S3 and indexed in agent memory for future retrieval.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
