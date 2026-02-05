/**
 * Integration tests for Memory Response Parser
 * 
 * Uses actual API response data from /home/jose/memory-response.json
 */

import { describe, it, expect } from 'vitest';
import { parseMemoryResponse, parseSearchResult, parseMemory } from './parseMemoryResponse';
import type { ParsedMemory, ParsedSearchResponse, RawSearchResponse } from '../types/memory';
import { readFileSync } from 'fs';
import { resolve } from 'path';

// Load actual API response data
const responseFile = resolve('/home/jose/memory-response.json');
const actualResponse: RawSearchResponse = JSON.parse(readFileSync(responseFile, 'utf-8'));

describe('parseMemoryResponse', () => {
  describe('with actual API response data', () => {
    let parsed: ParsedSearchResponse;

    beforeAll(() => {
      parsed = parseMemoryResponse(actualResponse);
    });

    it('should parse successfully', () => {
      expect(parsed.success).toBe(true);
      expect(parsed.warning).toBeUndefined();
    });

    it('should have the correct count', () => {
      expect(parsed.count).toBe(actualResponse.results.length);
      expect(parsed.results.length).toBe(actualResponse.results.length);
    });

    it('should parse all result IDs correctly', () => {
      const expectedIds = actualResponse.results.map(r => r.memory.id);
      const parsedIds = parsed.results.map(r => r.id);
      expect(parsedIds).toEqual(expectedIds);
    });

    it('should parse agent_id to agentId correctly', () => {
      const first = parsed.results[0];
      expect(first.agentId).toBe('jarvis-macbook');

      const second = parsed.results[1];
      expect(second.agentId).toBe('jarvis-intel');
    });

    it('should handle null embedding values', () => {
      // All memories in the sample have null embeddings
      for (const memory of parsed.results) {
        expect(memory.embedding).toBeNull();
      }
    });

    it('should handle null project_id values', () => {
      // First memory has null project_id
      const first = parsed.results[0];
      expect(first.projectId).toBeNull();

      // Second memory has "daily-session" project_id
      const second = parsed.results[1];
      expect(second.projectId).toBe('daily-session');
    });

    it('should parse tags correctly', () => {
      const first = parsed.results[0];
      expect(first.tags).toEqual(['hourly-sync', 'watch-hobby', 'code-review', 'investment-system']);

      const second = parsed.results[1];
      expect(second.tags).toEqual(['roadmap-research', 'business-ideas', 'email-scanner', 'session-summary']);
    });

    it('should parse scores correctly', () => {
      // First result has a keyword match with low score
      const first = parsed.results[0];
      expect(first.score).toBeCloseTo(1.9221136e-07, 10);

      // Second result has a vector match with negative score
      const second = parsed.results[1];
      expect(second.score).toBeCloseTo(-0.05714880944384215, 10);
    });

    it('should parse match_type correctly', () => {
      const first = parsed.results[0];
      expect(first.matchType).toBe('keyword');

      const second = parsed.results[1];
      expect(second.matchType).toBe('vector');
    });

    it('should parse timestamps correctly', () => {
      const first = parsed.results[0];
      expect(first.createdAt).toBe('2026-02-04T13:01:57.652Z');
      expect(first.updatedAt).toBe('2026-02-04T13:01:57.652Z');
    });

    it('should preserve content text', () => {
      const first = parsed.results[0];
      expect(first.content).toContain('## Hourly Sync - Feb 4, 2026');
      expect(first.content).toContain('Intersect NYC');
    });

    it('should preserve tsvector_content', () => {
      const first = parsed.results[0];
      expect(first.tsvectorContent).toContain('hour');
      expect(first.tsvectorContent.length).toBeGreaterThan(0);
    });
  });

  describe('edge cases: null/undefined input', () => {
    it('should handle null response', () => {
      const parsed = parseMemoryResponse(null);
      expect(parsed.success).toBe(false);
      expect(parsed.count).toBe(0);
      expect(parsed.results).toEqual([]);
      expect(parsed.warning).toContain('null');
    });

    it('should handle undefined response', () => {
      const parsed = parseMemoryResponse(undefined);
      expect(parsed.success).toBe(false);
      expect(parsed.count).toBe(0);
      expect(parsed.results).toEqual([]);
    });

    it('should handle non-object response (string)', () => {
      const parsed = parseMemoryResponse('invalid');
      expect(parsed.success).toBe(false);
      expect(parsed.warning).toContain('not an object');
    });

    it('should handle non-object response (number)', () => {
      const parsed = parseMemoryResponse(123);
      expect(parsed.success).toBe(false);
    });
  });

  describe('edge cases: malformed response structure', () => {
    it('should handle empty results array', () => {
      const parsed = parseMemoryResponse({ results: [] });
      expect(parsed.success).toBe(true);
      expect(parsed.count).toBe(0);
      expect(parsed.results).toEqual([]);
    });

    it('should handle missing results field', () => {
      const parsed = parseMemoryResponse({ foo: 'bar' });
      expect(parsed.success).toBe(false);
      expect(parsed.warning).toContain('results array');
    });

    it('should handle results as wrong type', () => {
      const parsed = parseMemoryResponse({ results: 'not an array' });
      expect(parsed.success).toBe(false);
    });

    it('should handle direct array (no wrapper)', () => {
      // Some APIs might return array directly
      const parsed = parseMemoryResponse([
        { memory: { id: '1', agent_id: 'test', content: 'hello' }, score: 0.5, match_type: 'vector' }
      ]);
      expect(parsed.success).toBe(true);
      expect(parsed.count).toBe(1);
      expect(parsed.results[0].id).toBe('1');
    });
  });

  describe('edge cases: malformed individual results', () => {
    it('should handle null items in results array', () => {
      const parsed = parseMemoryResponse({ results: [null, null] });
      expect(parsed.success).toBe(true);
      expect(parsed.count).toBe(2);
      // Should create placeholder memories
      expect(parsed.results[0].id).toMatch(/^temp-/);
      expect(parsed.results[0].agentId).toBe('unknown');
    });

    it('should handle missing memory wrapper', () => {
      // Result is memory object directly, not wrapped
      const parsed = parseMemoryResponse({
        results: [{
          id: 'direct-id',
          agent_id: 'direct-agent',
          content: 'direct content',
          embedding: null,
          project_id: null,
          tags: ['tag1'],
          tsvector_content: '',
          created_at: '2026-01-01',
          updated_at: '2026-01-01',
          score: 0.9,
          match_type: 'keyword'
        }]
      });
      expect(parsed.success).toBe(true);
      expect(parsed.results[0].id).toBe('direct-id');
      expect(parsed.results[0].agentId).toBe('direct-agent');
      expect(parsed.results[0].score).toBe(0.9);
    });

    it('should handle partial memory objects', () => {
      const parsed = parseMemoryResponse({
        results: [{
          memory: {
            id: 'partial-id',
            agent_id: 'partial-agent',
            content: 'partial content'
            // Missing: embedding, project_id, tags, tsvector_content, created_at, updated_at
          },
          score: 0.5,
          match_type: 'vector'
        }]
      });
      expect(parsed.success).toBe(true);
      expect(parsed.results[0].id).toBe('partial-id');
      expect(parsed.results[0].embedding).toBeNull();
      expect(parsed.results[0].projectId).toBeNull();
      expect(parsed.results[0].tags).toEqual([]);
      expect(parsed.results[0].tsvectorContent).toBe('');
      expect(parsed.results[0].createdAt).toBe('');
    });
  });
});

describe('parseSearchResult', () => {
  it('should parse a properly wrapped result', () => {
    const raw = {
      memory: {
        id: 'test-id',
        agent_id: 'test-agent',
        content: 'test content',
        embedding: [0.1, 0.2, 0.3],
        project_id: 'test-project',
        tags: ['tag1', 'tag2'],
        tsvector_content: 'test tsvector',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-02T00:00:00Z'
      },
      score: 0.95,
      match_type: 'vector' as const
    };

    const parsed = parseSearchResult(raw);
    expect(parsed.id).toBe('test-id');
    expect(parsed.agentId).toBe('test-agent');
    expect(parsed.content).toBe('test content');
    expect(parsed.embedding).toEqual([0.1, 0.2, 0.3]);
    expect(parsed.projectId).toBe('test-project');
    expect(parsed.tags).toEqual(['tag1', 'tag2']);
    expect(parsed.score).toBe(0.95);
    expect(parsed.matchType).toBe('vector');
  });

  it('should handle null input', () => {
    const parsed = parseSearchResult(null);
    expect(parsed.id).toMatch(/^temp-/);
    expect(parsed.agentId).toBe('unknown');
    expect(parsed.content).toBe('');
  });

  it('should handle undefined input', () => {
    const parsed = parseSearchResult(undefined);
    expect(parsed.id).toMatch(/^temp-/);
    expect(parsed.agentId).toBe('unknown');
  });
});

describe('parseMemory', () => {
  it('should convert snake_case to camelCase', () => {
    const raw = {
      id: 'test',
      agent_id: 'agent1',
      content: 'hello',
      project_id: 'proj1',
      tsvector_content: 'tsv',
      created_at: '2026-01-01',
      updated_at: '2026-01-02'
    };

    const parsed = parseMemory(raw);
    expect(parsed.agentId).toBe('agent1');
    expect(parsed.projectId).toBe('proj1');
    expect(parsed.tsvectorContent).toBe('tsv');
    expect(parsed.createdAt).toBe('2026-01-01');
    expect(parsed.updatedAt).toBe('2026-01-02');
  });

  it('should handle empty string project_id as null', () => {
    const raw = {
      id: 'test',
      agent_id: 'agent1',
      content: 'hello',
      project_id: ''
    };

    const parsed = parseMemory(raw);
    expect(parsed.projectId).toBeNull();
  });

  it('should handle whitespace-only project_id as null', () => {
    const raw = {
      id: 'test',
      agent_id: 'agent1',
      content: 'hello',
      project_id: '   '
    };

    const parsed = parseMemory(raw);
    expect(parsed.projectId).toBeNull();
  });

  it('should filter invalid tags', () => {
    const raw = {
      id: 'test',
      agent_id: 'agent1',
      content: 'hello',
      tags: ['valid', 123, null, 'also-valid', undefined]
    };

    const parsed = parseMemory(raw);
    expect(parsed.tags).toEqual(['valid', 'also-valid']);
  });

  it('should handle non-array tags', () => {
    const raw = {
      id: 'test',
      agent_id: 'agent1',
      content: 'hello',
      tags: 'not an array'
    };

    const parsed = parseMemory(raw);
    expect(parsed.tags).toEqual([]);
  });

  it('should handle invalid embedding values', () => {
    const raw = {
      id: 'test',
      agent_id: 'agent1',
      content: 'hello',
      embedding: ['not', 'numbers']
    };

    const parsed = parseMemory(raw);
    expect(parsed.embedding).toBeNull();
  });

  it('should handle empty embedding array as null', () => {
    const raw = {
      id: 'test',
      agent_id: 'agent1',
      content: 'hello',
      embedding: []
    };

    const parsed = parseMemory(raw);
    expect(parsed.embedding).toBeNull();
  });

  it('should generate temp ID for missing id', () => {
    const raw = {
      agent_id: 'agent1',
      content: 'hello'
    };

    const parsed = parseMemory(raw);
    expect(parsed.id).toMatch(/^temp-/);
  });

  it('should handle unknown match_type', () => {
    const parsed = parseMemory({}, 0.5, 'invalid' as any);
    expect(parsed.matchType).toBe('unknown');
  });
});

describe('type guards', () => {
  it('isRawMemory should validate correctly', async () => {
    const { isRawMemory } = await import('../types/memory');
    
    expect(isRawMemory({ id: 'a', agent_id: 'b', content: 'c' })).toBe(true);
    expect(isRawMemory({ id: 'a', agent_id: 'b' })).toBe(false);
    expect(isRawMemory(null)).toBe(false);
    expect(isRawMemory(undefined)).toBe(false);
    expect(isRawMemory({})).toBe(false);
  });

  it('isRawSearchResult should validate correctly', async () => {
    const { isRawSearchResult } = await import('../types/memory');
    
    const validResult = {
      memory: { id: 'a', agent_id: 'b', content: 'c' },
      score: 0.5,
      match_type: 'vector'
    };
    
    expect(isRawSearchResult(validResult)).toBe(true);
    expect(isRawSearchResult({ memory: {}, score: 0.5 })).toBe(false);
    expect(isRawSearchResult(null)).toBe(false);
  });

  it('isRawSearchResponse should validate correctly', async () => {
    const { isRawSearchResponse } = await import('../types/memory');
    
    expect(isRawSearchResponse({ results: [] })).toBe(true);
    expect(isRawSearchResponse({ results: [{}] })).toBe(true);
    expect(isRawSearchResponse({})).toBe(false);
    expect(isRawSearchResponse({ results: 'not array' })).toBe(false);
  });
});
