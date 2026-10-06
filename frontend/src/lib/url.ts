/**
 * Truncates a URL for display without hiding the domain — the part users
 * actually need to judge trust — instead of cutting off the end (which
 * always shows "https://c..." for anything long).
 */
export function truncateMiddle(value: string, maxLen = 42): string {
  if (value.length <= maxLen) return value;

  let head: string;
  let tail: string;
  try {
    const parsed = new URL(value);
    head = `${parsed.protocol}//${parsed.hostname}`;
    tail = `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    const splitAt = Math.ceil(value.length * 0.4);
    head = value.slice(0, splitAt);
    tail = value.slice(splitAt);
  }

  if (head.length >= maxLen - 8) {
    return `${head.slice(0, maxLen - 1)}…`;
  }

  const remaining = maxLen - head.length - 1;
  const tailLen = Math.max(remaining, 4);
  const tailPart = tail.length > tailLen ? tail.slice(tail.length - tailLen) : tail;

  return `${head}…${tailPart}`;
}
