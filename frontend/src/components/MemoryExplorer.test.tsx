import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MemoryExplorer from './MemoryExplorer';
import { ToastProvider } from './Toast';
import { api } from '../api';

// Mock the API module
vi.mock('../api', () => ({
  api: {
    getMemoryAgents: vi.fn(),
    searchMemories: vi.fn(),
    synthesizeMemories: vi.fn(),
  },
}));

// Helper to render with providers
function renderWithProviders(component: React.ReactNode) {
  return render(
    <ToastProvider>
      {component}
    </ToastProvider>
  );
}

describe('MemoryExplorer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock implementations
    vi.mocked(api.getMemoryAgents).mockResolvedValue({ agents: [] });
    vi.mocked(api.searchMemories).mockResolvedValue({ results: [] });
    vi.mocked(api.synthesizeMemories).mockResolvedValue({ 
      answer: 'Test answer', 
      model: 'test-model',
      memories_used: 0,
      memories_total: 0,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Enter key search behavior', () => {
    it('should trigger search when Enter is pressed in the search input', async () => {
      const user = userEvent.setup();
      
      // Mock successful search response
      vi.mocked(api.searchMemories).mockResolvedValue({
        results: [
          {
            memory: {
              id: 'test-memory-1',
              agent_id: 'test-agent',
              content: 'Test memory content',
              embedding: null,
              project_id: null,
              tags: ['test'],
              tsvector_content: '',
              created_at: '2026-01-01T00:00:00Z',
              updated_at: '2026-01-01T00:00:00Z',
            },
            score: 0.95,
            match_type: 'vector',
          },
        ],
      });

      renderWithProviders(<MemoryExplorer />);

      // Wait for the component to load agents
      await waitFor(() => {
        expect(api.getMemoryAgents).toHaveBeenCalled();
      });

      // Find the search input by placeholder
      const searchInput = screen.getByPlaceholderText('Search memories...');
      expect(searchInput).toBeInTheDocument();

      // Type a search query
      await user.type(searchInput, 'test query');

      // Verify the input has the value
      expect(searchInput).toHaveValue('test query');

      // Press Enter to submit
      await user.keyboard('{Enter}');

      // Verify the API was called with the search query
      await waitFor(() => {
        expect(api.searchMemories).toHaveBeenCalledTimes(1);
      });

      // Check the API was called with correct parameters
      expect(api.searchMemories).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'test query',
          scope: 'network',
          limit: 50,
        })
      );
    });

    it('should trigger search when clicking the Search button', async () => {
      const user = userEvent.setup();

      vi.mocked(api.searchMemories).mockResolvedValue({ results: [] });

      renderWithProviders(<MemoryExplorer />);

      // Wait for agents to load
      await waitFor(() => {
        expect(api.getMemoryAgents).toHaveBeenCalled();
      });

      // Type a search query
      const searchInput = screen.getByPlaceholderText('Search memories...');
      await user.type(searchInput, 'button test');

      // Click the search button
      const searchButton = screen.getByRole('button', { name: /search/i });
      await user.click(searchButton);

      // Verify the API was called
      await waitFor(() => {
        expect(api.searchMemories).toHaveBeenCalledTimes(1);
      });

      expect(api.searchMemories).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'button test',
        })
      );
    });

    it('should not trigger search on Enter with empty query', async () => {
      const user = userEvent.setup();

      renderWithProviders(<MemoryExplorer />);

      // Wait for agents to load
      await waitFor(() => {
        expect(api.getMemoryAgents).toHaveBeenCalled();
      });

      // Find the search input (it should be empty)
      const searchInput = screen.getByPlaceholderText('Search memories...');
      
      // Focus the input and press Enter without typing anything
      await user.click(searchInput);
      await user.keyboard('{Enter}');

      // API should NOT be called (empty query validation)
      expect(api.searchMemories).not.toHaveBeenCalled();
    });

    it('should trigger search on Enter after typing in filter fields', async () => {
      const user = userEvent.setup();

      vi.mocked(api.searchMemories).mockResolvedValue({ results: [] });

      renderWithProviders(<MemoryExplorer />);

      // Wait for agents to load
      await waitFor(() => {
        expect(api.getMemoryAgents).toHaveBeenCalled();
      });

      // Type a search query first
      const searchInput = screen.getByPlaceholderText('Search memories...');
      await user.type(searchInput, 'filter test');

      // Also add a project ID filter
      const projectInput = screen.getByPlaceholderText('Optional');
      await user.type(projectInput, 'my-project');

      // Press Enter in the project field
      await user.keyboard('{Enter}');

      // The search should be triggered
      await waitFor(() => {
        expect(api.searchMemories).toHaveBeenCalledTimes(1);
      });

      expect(api.searchMemories).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'filter test',
          project_id: 'my-project',
        })
      );
    });
  });
});
