import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './RenderMarkdown.css';

/**
 * Detect if content looks like markdown based on common patterns
 */
export function looksLikeMarkdown(content) {
  if (!content || typeof content !== 'string') return false;
  
  // Check for common markdown patterns
  const patterns = [
    /^#{1,6}\s+/m,           // Headers: # ## ### etc
    /\*\*[^*]+\*\*/,         // Bold: **text**
    /(?<!\*)\*[^*]+\*(?!\*)/, // Italic: *text* (not bold)
    /_[^_]+_/,               // Italic: _text_
    /```[\s\S]*?```/,        // Code blocks: ```code```
    /`[^`]+`/,               // Inline code: `code`
    /^\s*[-*+]\s+/m,         // Unordered lists: - item, * item, + item
    /^\s*\d+\.\s+/m,         // Ordered lists: 1. item
    /\[.+?\]\(.+?\)/,        // Links: [text](url)
    /^\s*>/m,                // Blockquotes: > quote
    /^\s*[-*_]{3,}\s*$/m,    // Horizontal rules: --- *** ___
    /!\[.+?\]\(.+?\)/,       // Images: ![alt](url)
  ];
  
  // Return true if any pattern matches
  return patterns.some(pattern => pattern.test(content));
}

/**
 * Renders markdown content as formatted HTML if it looks like markdown,
 * otherwise displays as plain text.
 * 
 * @param {Object} props
 * @param {string} props.content - The content to render
 * @param {boolean} [props.forceMarkdown] - Force markdown rendering regardless of detection
 * @param {boolean} [props.forcePlainText] - Force plain text rendering regardless of detection
 * @param {string} [props.className] - Additional CSS class for the container
 */
export default function RenderMarkdown({ 
  content, 
  forceMarkdown = false, 
  forcePlainText = false,
  className = '' 
}) {
  if (!content) {
    return null;
  }

  const contentStr = String(content);
  
  // Determine rendering mode
  const shouldRenderMarkdown = forcePlainText 
    ? false 
    : (forceMarkdown || looksLikeMarkdown(contentStr));

  if (shouldRenderMarkdown) {
    return (
      <div className={`render-markdown ${className}`.trim()}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {contentStr}
        </ReactMarkdown>
      </div>
    );
  }

  // Plain text fallback - preserve whitespace
  return (
    <div className={`render-plaintext ${className}`.trim()}>
      {contentStr}
    </div>
  );
}
