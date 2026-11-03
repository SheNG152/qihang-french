// A board's random ID seeds its layout, so saved games reopen in the same positions.
export function cardLayout(board) {
  let seed = 2166136261;
  for (const char of board.id) seed = Math.imul(seed ^ char.charCodeAt(0), 16777619);
  const random = () => { seed |= 0; seed = seed + 0x6d2b79f5 | 0; let n = Math.imul(seed ^ seed >>> 15, 1 | seed); n ^= n + Math.imul(n ^ n >>> 7, 61 | n); return ((n ^ n >>> 14) >>> 0) / 4294967296; };
  const tokens = [...board.left.map(key => ({ side: 'left', key })), ...board.right.map(key => ({ side: 'right', key }))];
  for (let attempt = 0; attempt < 48; attempt++) {
    const layout = [...tokens];
    for (let i = layout.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [layout[i], layout[j]] = [layout[j], layout[i]]; }
    if (tokens.length < 6 || [0, 1, 2].every(col => new Set(layout.filter((_, i) => i % 3 === col).map(t => t.side)).size === 2)) return layout;
  }
  return tokens;
}
