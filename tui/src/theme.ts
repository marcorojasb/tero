/** Calm, dense palette — closer to OpenCode than to a neon demo. */

export const theme = {
  bg: "#0b0d10",
  panel: "#12151a",
  panelAlt: "#161a20",
  border: "#2c333c",
  borderFocus: "#6cb6ff",
  text: "#d8dee9",
  muted: "#7a8490",
  faint: "#4b5563",
  accent: "#82aaff",
  ok: "#9ece6a",
  warn: "#c9a227",
  err: "#e06c75",
  chip: "#1a2330",
  chipFg: "#c8d6f0",
  cursor: "#82aaff",
  inputBg: "#0e1116",
  overlay: "#0f141c",
} as const

export type Theme = typeof theme
