import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../api';
import './CrawlIndicator.css';

const ACTIVE_STATUS = new Set(['running', 'in_progress', 'queued', 'active', 'processing']);

const INITIAL_STATE = {
  isActive: false,
  percent: 0,
  completed: 0,
  total: 0,
  currentUrl: '',
  status: 'idle',
};

function firstDefined(...values) {
  return values.find((value) => value !== undefined && value !== null);
}

function toNumber(value) {
  if (value === undefined || value === null || value === '') return null;
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}

function clampPercent(value) {
  if (value === null || value === undefined) return null;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function normalizeProgress(payload, eventType) {
  const source =
    payload && typeof payload === 'object' && payload.data && typeof payload.data === 'object'
      ? payload.data
      : payload;

  const completed = toNumber(
    firstDefined(
      source?.items_completed,
      source?.itemsCompleted,
      source?.completed,
      source?.done,
      source?.visited_count,
      source?.visitedCount
    )
  );

  const total = toNumber(
    firstDefined(
      source?.items_total,
      source?.itemsTotal,
      source?.total,
      source?.total_items,
      source?.totalItems,
      source?.discovered_count,
      source?.discoveredCount
    )
  );

  let percent = clampPercent(
    toNumber(
      firstDefined(
        source?.progress_percent,
        source?.progressPercent,
        source?.percent,
        source?.percentage,
        source?.progress
      )
    )
  );

  if (percent === null && completed !== null && total !== null && total > 0) {
    percent = clampPercent((completed / total) * 100);
  }

  const rawStatus = firstDefined(source?.status, source?.state, source?.phase);
  const status = typeof rawStatus === 'string' ? rawStatus.toLowerCase() : undefined;

  let isActive = firstDefined(source?.is_active, source?.isActive, source?.active, source?.running);

  if (typeof isActive !== 'boolean') {
    if (eventType === 'complete') {
      isActive = false;
    } else if (status) {
      isActive = ACTIVE_STATUS.has(status);
    } else if (percent !== null) {
      isActive = percent < 100;
    }
  }

  if (eventType === 'complete') {
    isActive = false;
    if (percent === null) {
      percent = 100;
    }
  }

  if (eventType === 'error') {
    isActive = false;
  }

  const currentUrl = firstDefined(
    source?.current_url,
    source?.currentUrl,
    source?.url,
    source?.current,
    source?.last_url,
    source?.lastUrl
  );

  return {
    isActive: typeof isActive === 'boolean' ? isActive : undefined,
    percent,
    completed,
    total,
    currentUrl: typeof currentUrl === 'string' ? currentUrl : undefined,
    status: status || (eventType === 'error' ? 'error' : undefined),
  };
}

function statusLabel(progress, hasTarget) {
  if (!hasTarget) return 'No crawl selected';
  if (progress.status === 'error') return 'Crawl error';
  if (progress.isActive) return 'Crawling';
  return 'Idle';
}

export default function CrawlIndicator({ targetUlid, version }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [progress, setProgress] = useState(INITIAL_STATE);
  const hasAutoExpanded = useRef(false);

  const hasTarget = Boolean(targetUlid) && version !== undefined && version !== null;
  const visibleProgress = hasTarget ? progress : INITIAL_STATE;

  useEffect(() => {
    hasAutoExpanded.current = false;
  }, [targetUlid, version]);

  const applyProgress = useCallback((payload, eventType = 'progress') => {
    const next = normalizeProgress(payload, eventType);

    if (next.isActive && !hasAutoExpanded.current) {
      hasAutoExpanded.current = true;
      setIsExpanded(true);
    }

    setProgress((prev) => ({
      ...prev,
      ...(next.isActive !== undefined ? { isActive: next.isActive } : null),
      ...(next.percent !== null ? { percent: next.percent } : null),
      ...(next.completed !== null ? { completed: next.completed } : null),
      ...(next.total !== null ? { total: next.total } : null),
      ...(next.currentUrl !== undefined ? { currentUrl: next.currentUrl } : null),
      ...(next.status ? { status: next.status } : null),
    }));
  }, []);

  useEffect(() => {
    if (!hasTarget) {
      return undefined;
    }

    let isCancelled = false;

    const loadStatus = async () => {
      try {
        const status = await api.getCrawlerStatus(targetUlid, version);
        if (!isCancelled && status) {
          applyProgress(status, 'status');
        }
      } catch (error) {
        if (!isCancelled) {
          console.error('Failed to load crawler status:', error);
          applyProgress({}, 'error');
        }
      }
    };

    loadStatus();

    const unsubscribe = api.subscribeToCrawlProgress(
      targetUlid,
      version,
      (eventType, payload) => {
        if (!isCancelled) {
          applyProgress(payload, eventType);
        }
      }
    );

    return () => {
      isCancelled = true;
      unsubscribe();
    };
  }, [applyProgress, hasTarget, targetUlid, version]);

  const summary = useMemo(() => {
    const label = statusLabel(visibleProgress, hasTarget);
    if (!visibleProgress.isActive) return label;
    return `${visibleProgress.percent}%`;
  }, [hasTarget, visibleProgress]);

  const showDetails = hasTarget && isExpanded;

  return (
    <div
      className={`crawl-indicator ${visibleProgress.isActive ? 'is-active' : 'is-idle'} ${
        showDetails ? 'is-expanded' : 'is-collapsed'
      }`}
      data-testid="crawl-indicator"
    >
      <button
        type="button"
        className="crawl-indicator-toggle"
        onClick={() => setIsExpanded((prev) => !prev)}
        aria-label="Crawl status"
        title="Crawl status"
      >
        <span
          className={`crawl-indicator-icon ${visibleProgress.isActive ? 'spin' : ''}`}
          aria-hidden="true"
        >
          {visibleProgress.isActive ? '↻' : '•'}
        </span>
        {showDetails && <span className="crawl-indicator-summary">{summary}</span>}
      </button>

      {showDetails && (
        <div className="crawl-indicator-details">
          <div className="crawl-indicator-row">
            <span>{visibleProgress.percent}%</span>
            <span>
              {visibleProgress.completed}/{visibleProgress.total || 0}
            </span>
          </div>

          {visibleProgress.currentUrl && (
            <div className="crawl-indicator-url" title={visibleProgress.currentUrl}>
              {visibleProgress.currentUrl}
            </div>
          )}

          {!visibleProgress.currentUrl && (
            <div className="crawl-indicator-url crawl-indicator-empty">No URL in progress</div>
          )}
        </div>
      )}
    </div>
  );
}
