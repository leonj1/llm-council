/**
 * TypeScript interfaces for the Memory Explorer API.
 * 
 * These types represent the raw API response structure from the
 * agent-memory-api service and the parsed/safe output structure.
 */

// ============================================================
// RAW API RESPONSE TYPES (what the API actually returns)
// ============================================================

/**
 * Raw memory object as returned by the API.
 * All fields except id are potentially nullable or missing.
 */
export interface RawMemory {
  id: string;
  agent_id: string;
  content: string;
  embedding: number[] | null;
  project_id: string | null;
  tags: string[];
  tsvector_content: string;
  created_at: string;
  updated_at: string;
}

/**
 * Raw search result item wrapping a memory with search metadata.
 */
export interface RawSearchResult {
  memory: RawMemory;
  score: number;
  match_type: 'keyword' | 'vector';
}

/**
 * Raw API response from the /search endpoint.
 */
export interface RawSearchResponse {
  results: RawSearchResult[];
}

// ============================================================
// PARSED/SAFE OUTPUT TYPES (what our parser returns)
// ============================================================

/**
 * Match type enumeration for type safety.
 */
export type MatchType = 'keyword' | 'vector' | 'unknown';

/**
 * Parsed memory object with guaranteed non-null fields and safe defaults.
 * This is what components should use.
 */
export interface ParsedMemory {
  /** Unique identifier for the memory */
  id: string;
  /** Agent that created the memory */
  agentId: string;
  /** Memory content text */
  content: string;
  /** Vector embedding (null if not generated) */
  embedding: number[] | null;
  /** Optional project identifier */
  projectId: string | null;
  /** Array of tags (never null, defaults to empty array) */
  tags: string[];
  /** Full-text search content (for debugging) */
  tsvectorContent: string;
  /** ISO timestamp of creation */
  createdAt: string;
  /** ISO timestamp of last update */
  updatedAt: string;
  /** Search relevance score (0-1 range typically) */
  score: number;
  /** Type of search match */
  matchType: MatchType;
}

/**
 * Parsed search response with guaranteed structure.
 */
export interface ParsedSearchResponse {
  /** Array of parsed memory results */
  results: ParsedMemory[];
  /** Total count of results */
  count: number;
  /** Whether the response was successfully parsed */
  success: boolean;
  /** Optional error message if parsing partially failed */
  warning?: string;
}

// ============================================================
// INPUT TYPE FOR PARSER (handles unknown API responses)
// ============================================================

/**
 * Type guard to check if a value is a valid RawMemory object.
 */
export function isRawMemory(value: unknown): value is RawMemory {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.id === 'string' &&
    typeof obj.agent_id === 'string' &&
    typeof obj.content === 'string'
  );
}

/**
 * Type guard to check if a value is a valid RawSearchResult.
 */
export function isRawSearchResult(value: unknown): value is RawSearchResult {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    isRawMemory(obj.memory) &&
    typeof obj.score === 'number' &&
    (obj.match_type === 'keyword' || obj.match_type === 'vector')
  );
}

/**
 * Type guard to check if a value is a valid RawSearchResponse.
 */
export function isRawSearchResponse(value: unknown): value is RawSearchResponse {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return Array.isArray(obj.results);
}
