function getStyledCharType(char) {
  const code = char.codePointAt(0);

  const uppercaseRanges = [
    { type: 'bold', start: 0x1d400, end: 0x1d433, base: 0x41 },
    { type: 'italic', start: 0x1d434, end: 0x1d467, base: 0x41 },
    { type: 'bold-italic', start: 0x1d468, end: 0x1d49b, base: 0x41 },
    { type: 'bold', start: 0x1d5d4, end: 0x1d607, base: 0x41 },
    { type: 'italic', start: 0x1d608, end: 0x1d63b, base: 0x41 },
    { type: 'bold-italic', start: 0x1d63c, end: 0x1d66f, base: 0x41 },
    { type: 'code', start: 0x1d670, end: 0x1d6a3, base: 0x41 }
  ];

  const lowercaseRanges = [
    { type: 'bold', start: 0x1d41a, end: 0x1d44d, base: 0x61 },
    { type: 'italic', start: 0x1d44e, end: 0x1d481, base: 0x61 },
    { type: 'bold-italic', start: 0x1d482, end: 0x1d4b5, base: 0x61 },
    { type: 'bold', start: 0x1d5ee, end: 0x1d621, base: 0x61 },
    { type: 'italic', start: 0x1d622, end: 0x1d655, base: 0x61 },
    { type: 'bold-italic', start: 0x1d656, end: 0x1d689, base: 0x61 },
    { type: 'code', start: 0x1d6a6, end: 0x1d6d9, base: 0x61 }
  ];

  const ranges = uppercaseRanges.concat(lowercaseRanges);
  const match = ranges.find((range) => code >= range.start && code <= range.end);
  return match ? { type: match.type, base: match.base } : null;
}

function normalizeStyledChar(char) {
  const style = getStyledCharType(char);
  if (!style) return char;

  return char.normalize('NFKD');
}

function convertToMarkdown(text) {
  if (typeof text !== 'string') return '';

  const lines = text.split(/\r?\n/);
  const convertedLines = lines.map((line) => {
    if (/^[\s•◦‣●*]+/u.test(line)) {
      return `- ${line.replace(/^[\s•◦‣●*]+\s*/u, '')}`;
    }

    const chars = Array.from(line);
    const hasStyledText = chars.some((char) => getStyledCharType(char));

    if (!hasStyledText) {
      return line;
    }

    const normalized = chars.map((char) => normalizeStyledChar(char)).join('');
    const styles = chars.map((char) => getStyledCharType(char)).filter(Boolean);

    let styleType = null;
    if (styles.some((style) => style.type === 'code')) {
      styleType = 'code';
    } else if (styles.some((style) => style.type === 'bold-italic')) {
      styleType = 'bold-italic';
    } else if (styles.some((style) => style.type === 'bold')) {
      styleType = 'bold';
    } else if (styles.some((style) => style.type === 'italic')) {
      styleType = 'italic';
    }

    if (styleType === 'bold') {
      return `**${normalized}**`;
    }
    if (styleType === 'italic') {
      return `*${normalized}*`;
    }
    if (styleType === 'bold-italic') {
      return `***${normalized}***`;
    }
    if (styleType === 'code') {
      return `\`${normalized}\``;
    }

    return normalized;
  });

  return convertedLines.join('\n');
}

if (typeof module !== 'undefined') {
  module.exports = { convertToMarkdown };
}
