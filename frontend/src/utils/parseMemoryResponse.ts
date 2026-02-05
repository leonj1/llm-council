/**
 * Memory Response Parser
 * 
 * Robust parser for the Memory Explorer API responses.
 * Handles all edge cases safely and provides defaults for missing fields.
 */

import type {
  RawMemory,
  RawSearchResult,
  RawSearchResponse,
  ParsedMemory,
  ParsedSearchResponse,
  MatchType,
} from '../types/memory';

import {
  isRawMemory,
  isRawSearchResult,
  isRawSearchResponse,
} from '../types/memory';

// ============================================================
// SAFE VALUE EXTRACTORS
// ============================================================

/**
 * Safely extract a string value with a fallback.
 */
function safeString(value: unknown, fallback: string = ''): string {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return fallback;
  return String(value);
}

/**
 * Safely extract a number value with a fallback.
 */
function safeNumber(value: unknown, fallback: number = 0): number {
  if (typeof value === 'number' && !Number.isNaN(value)) return value;
  if (typeof value === 'string') {
    const parsed = parseFloat(value);
    if (!Number.isNaN(parsed)) return parsed;
  }
  return fallback;
}

/**
 * Safely extract a string array with a fallback to empty array.
 */
function safeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string');
}

/**
 * Safely extract an optional string (returns null if not a valid string).
 */
function safeOptionalString(value: unknown): string | null {
  if (typeof value === 'string' && value.trim() !== '') return value;
  return null;
}

/**
 * Safely extract a number array (for embeddings).
 */
function safeNumberArray(value: unknown): number[] | null {
  if (!Array.isArray(value)) return null;
  if (value.length === 0) return null;
  const numbers = value.filter((item): item is number => typeof item === 'number');
  // Only return if all values were valid numbers
  return numbers.length === value.length ? numbers : null;
}

/**
 * Safely extract match type with validation.
 */
function safeMatchType(value: unknown): MatchType {
  if (value === 'keyword' || value === 'vector') return value;
  return 'unknown';
}

/**
 * Generate a unique temporary ID for results without valid IDs.
 */
function generateTempId(): string {
  return `temp-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

// ============================================================
// MEMORY PARSER
// ============================================================

/**
 * Parse a single raw memory object into a safe ParsedMemory.
 * 
 * @param raw - The raw memory object from API (may be partial or malformed)
 * @param score - The search score (from wrapper or memory itself)
 * @param matchType - The match type (from wrapper or default)
 * @returns ParsedMemory with all fields safely populated
 */
export function parseMemory(
  raw: unknown,
  score: number = 0,
  matchType: MatchType | string = 'unknown'
): ParsedMemory {
  // Validate matchType
  const safeMatchTypeValue = safeMatchType(matchType);
  
  // Handle null/undefined input
  if (raw === null || raw === undefined || typeof raw !== 'object') {
    return createEmptyMemory(score, safeMatchTypeValue);
  }

  const obj = raw as Record<string, unknown>;

  return {
    id: safeString(obj.id) || generateTempId(),
    agentId: safeString(obj.agent_id, 'unknown'),
    content: safeString(obj.content),
    embedding: safeNumberArray(obj.embedding),
    projectId: safeOptionalString(obj.project_id),
    tags: safeStringArray(obj.tags),
    tsvectorContent: safeString(obj.tsvector_content),
    createdAt: safeString(obj.created_at),
    updatedAt: safeString(obj.updated_at),
    score: safeNumber(score),
    matchType: safeMatchTypeValue,
  };
}

/**
 * Create an empty/placeholder memory object.
 */
function createEmptyMemory(score: number = 0, matchType: MatchType = 'unknown'): ParsedMemory {
  return {
    id: generateTempId(),
    agentId: 'unknown',
    content: '',
    embedding: null,
    projectId: null,
    tags: [],
    tsvectorContent: '',
    createdAt: '',
    updatedAt: '',
    score: score,
    matchType: matchType,
  };
}

// ============================================================
// SEARCH RESULT PARSER
// ============================================================

/**
 * Parse a single search result item (memory + metadata wrapper).
 * 
 * @param item - Raw search result item from API
 * @returns ParsedMemory with score and match_type attached
 */
export function parseSearchResult(item: unknown): ParsedMemory {
  // Handle null/undefined
  if (item === null || item === undefined || typeof item !== 'object') {
    return createEmptyMemory();
  }

  const obj = item as Record<string, unknown>;

  // Extract score and match_type from wrapper
  const score = safeNumber(obj.score);
  const matchType = safeMatchType(obj.match_type);

  // Check if this is a wrapped result { memory: {...}, score, match_type }
  if (obj.memory && typeof obj.memory === 'object') {
    return parseMemory(obj.memory, score, matchType);
  }

  // Otherwise, treat the item itself as a memory object
  // (may include score/match_type as direct properties)
  return parseMemory(obj, score, matchType);
}

// ============================================================
// FULL RESPONSE PARSER
// ============================================================

/**
 * Parse the full API response from /search endpoint.
 * 
 * This is the main entry point for parsing API responses.
 * It handles all edge cases including:
 * - null/undefined response
 * - missing results array
 * - results as wrong type
 * - malformed individual results
 * 
 * @param response - Raw API response (may be any type)
 * @returns ParsedSearchResponse with guaranteed structure
 */
export function parseMemoryResponse(response: unknown): ParsedSearchResponse {
  // Handle null/undefined/non-object response
  if (response === null || response === undefined) {
    return {
      results: [],
      count: 0,
      success: false,
      warning: 'Response is null or undefined',
    };
  }

  if (typeof response !== 'object') {
    return {
      results: [],
      count: 0,
      success: false,
      warning: `Response is not an object (got ${typeof response})`,
    };
  }

  const obj = response as Record<string, unknown>;

  // Extract results array
  let rawResults: unknown[];
  if (Array.isArray(obj.results)) {
    rawResults = obj.results;
  } else if (Array.isArray(response)) {
    // Handle case where API returns array directly
    rawResults = response as unknown[];
  } else {
    return {
      results: [],
      count: 0,
      success: false,
      warning: 'Response does not contain a results array',
    };
  }

  // Parse each result with error tracking
  const parsedResults: ParsedMemory[] = [];
  let parseErrors = 0;

  for (const item of rawResults) {
    try {
      const parsed = parseSearchResult(item);
      parsedResults.push(parsed);
    } catch (e) {
      parseErrors++;
      // Still try to create a placeholder
      parsedResults.push(createEmptyMemory());
    }
  }

  // Build response
  const result: ParsedSearchResponse = {
    results: parsedResults,
    count: parsedResults.length,
    success: true,
  };

  // Add warning if some items failed to parse
  if (parseErrors > 0) {
    result.warning = `${parseErrors} of ${rawResults.length} results had parsing issues`;
  }

  return result;
}

// ============================================================
// CONVENIENCE EXPORTS
// ============================================================

export {
  isRawMemory,
  isRawSearchResult,
  isRawSearchResponse,
};
