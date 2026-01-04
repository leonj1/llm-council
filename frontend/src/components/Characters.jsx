import { useState, useMemo } from 'react';
import './Characters.css';

/**
 * Parse characters from the script markdown.
 * Looks for the **CHARACTERS:** section and extracts character info.
 */
function parseCharacters(scriptText) {
  if (!scriptText) return [];

  const characters = [];

  // Find the CHARACTERS section
  const charactersMatch = scriptText.match(/\*\*CHARACTERS:\*\*\s*([\s\S]*?)(?=\*\*(?:REFINED\s+)?OUTLINE:\*\*|\*\*KEY SCENES:\*\*|$)/i);

  if (!charactersMatch) return [];

  const charactersSection = charactersMatch[1];

  // Split by character entries - look for **Name** or - **Name** patterns
  const characterBlocks = charactersSection.split(/(?=(?:^|\n)\s*[-•]?\s*\*\*[A-Z])/);

  for (const block of characterBlocks) {
    if (!block.trim()) continue;

    // Extract character name - look for **Name**: or **Name**
    const nameMatch = block.match(/\*\*([^*]+)\*\*\s*:?/);
    if (!nameMatch) continue;

    const name = nameMatch[1].trim();
    if (name.toLowerCase() === 'name' || name.toLowerCase() === 'characters') continue;

    // Extract appearance - handle multi-line detailed descriptions
    let appearance = '';
    const appearanceMatch = block.match(/\*\*Appearance\*\*\s*:?\s*([\s\S]*?)(?=\*\*Personality\*\*|$)/i);
    if (appearanceMatch) {
      // Clean up the appearance text - remove sub-bullets formatting but keep content
      appearance = appearanceMatch[1]
        .replace(/^\s*[-•]\s*/gm, '')  // Remove bullet points
        .replace(/\n\s*\n/g, ' ')       // Collapse double newlines
        .replace(/\n/g, ' ')            // Replace newlines with spaces
        .replace(/\s+/g, ' ')           // Collapse multiple spaces
        .trim();
    }

    // Extract personality
    let personality = '';
    const personalityMatch = block.match(/\*\*Personality\*\*\s*:?\s*([^\n*]+(?:\n(?!\s*[-•]?\s*\*\*)[^\n*]+)*)/i);
    if (personalityMatch) {
      personality = personalityMatch[1].trim();
    }

    // If no structured format, try to get description after the name
    if (!appearance && !personality) {
      const descMatch = block.match(/\*\*[^*]+\*\*\s*:?\s*(.+)/s);
      if (descMatch) {
        const desc = descMatch[1].trim();
        // Split roughly in half for appearance/personality if it's long enough
        if (desc.length > 50) {
          const sentences = desc.split(/(?<=[.!?])\s+/);
          const mid = Math.ceil(sentences.length / 2);
          appearance = sentences.slice(0, mid).join(' ');
          personality = sentences.slice(mid).join(' ');
        } else {
          appearance = desc;
        }
      }
    }

    if (name && (appearance || personality)) {
      characters.push({ name, appearance, personality });
    }
  }

  return characters;
}

/**
 * Generate a consistent color for a character based on their name
 */
function getCharacterColor(name) {
  const colors = [
    { bg: '#e3f2fd', border: '#1976d2', text: '#1565c0' },
    { bg: '#e8f5e9', border: '#388e3c', text: '#2e7d32' },
    { bg: '#fff3e0', border: '#f57c00', text: '#e65100' },
    { bg: '#f3e5f5', border: '#7b1fa2', text: '#6a1b9a' },
    { bg: '#e0f7fa', border: '#0097a7', text: '#00838f' },
    { bg: '#fce4ec', border: '#c2185b', text: '#ad1457' },
    { bg: '#fff8e1', border: '#ffa000', text: '#ff8f00' },
    { bg: '#e8eaf6', border: '#3f51b5', text: '#303f9f' },
  ];

  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
}

/**
 * Get initials from a character name
 */
function getInitials(name) {
  return name
    .split(/\s+/)
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export default function Characters({ scriptText }) {
  const [isExpanded, setIsExpanded] = useState(true);

  const characters = useMemo(() => parseCharacters(scriptText), [scriptText]);

  if (characters.length === 0) {
    return null;
  }

  return (
    <div className="characters-section">
      <div className="characters-header" onClick={() => setIsExpanded(!isExpanded)}>
        <span className="characters-icon">🎭</span>
        <h4>Characters ({characters.length})</h4>
        <span className="expand-toggle">{isExpanded ? '−' : '+'}</span>
      </div>

      {isExpanded && (
        <div className="characters-grid">
          {characters.map((char, index) => {
            const color = getCharacterColor(char.name);
            return (
              <div
                key={index}
                className="character-card"
                style={{ borderColor: color.border }}
              >
                <div className="character-header" style={{ background: color.bg }}>
                  <div
                    className="character-avatar"
                    style={{ background: color.border, color: '#fff' }}
                  >
                    {getInitials(char.name)}
                  </div>
                  <h5 className="character-name" style={{ color: color.text }}>
                    {char.name}
                  </h5>
                </div>

                <div className="character-details">
                  {char.appearance && (
                    <div className="character-trait">
                      <span className="trait-label">Appearance</span>
                      <p className="trait-value">{char.appearance}</p>
                    </div>
                  )}

                  {char.personality && (
                    <div className="character-trait">
                      <span className="trait-label">Personality</span>
                      <p className="trait-value">{char.personality}</p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
