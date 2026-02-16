import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CrawlIndicator from './CrawlIndicator';
import { api } from '../api';

vi.mock('../api', () => ({
  api: {
    getCrawlerStatus: vi.fn(),
    subscribeToCrawlProgress: vi.fn(),
  },
}));

describe('CrawlIndicator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getCrawlerStatus).mockResolvedValue(null);
    vi.mocked(api.subscribeToCrawlProgress).mockReturnValue(() => {});
  });

  it('renders a compact indicator when no crawl target is provided', () => {
    render(<CrawlIndicator />);

    expect(screen.getByRole('button', { name: 'Crawl status' })).toBeInTheDocument();
    expect(api.getCrawlerStatus).not.toHaveBeenCalled();
    expect(api.subscribeToCrawlProgress).not.toHaveBeenCalled();
  });

  it('shows active crawl details from initial status', async () => {
    vi.mocked(api.getCrawlerStatus).mockResolvedValue({
      is_active: true,
      progress_percent: 35,
      items_completed: 7,
      items_total: 20,
      current_url: 'https://example.com/start',
    });

    render(<CrawlIndicator targetUlid="target-1" version="1" />);

    expect(await screen.findByTitle('https://example.com/start')).toBeInTheDocument();
    expect(screen.getAllByText('35%').length).toBeGreaterThan(0);
    expect(screen.getByText('7/20')).toBeInTheDocument();
  });

  it('updates progress when SSE events arrive', async () => {
    let onEventHandler = null;

    vi.mocked(api.getCrawlerStatus).mockResolvedValue({
      is_active: true,
      progress_percent: 10,
      items_completed: 1,
      items_total: 10,
      current_url: 'https://example.com/1',
    });

    vi.mocked(api.subscribeToCrawlProgress).mockImplementation((_, __, onEvent) => {
      onEventHandler = onEvent;
      return () => {};
    });

    render(<CrawlIndicator targetUlid="target-1" version="1" />);

    expect(await screen.findByTitle('https://example.com/1')).toBeInTheDocument();
    expect(screen.getAllByText('10%').length).toBeGreaterThan(0);

    await act(async () => {
      onEventHandler?.('progress', {
        progress_percent: 70,
        items_completed: 7,
        items_total: 10,
        current_url: 'https://example.com/7',
        is_active: true,
      });
    });

    await waitFor(() => {
      expect(screen.getAllByText('70%').length).toBeGreaterThan(0);
      expect(screen.getByText('7/10')).toBeInTheDocument();
      expect(screen.getByTitle('https://example.com/7')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Crawl status' }));
    expect(screen.queryByText('70%')).not.toBeInTheDocument();
  });
});
