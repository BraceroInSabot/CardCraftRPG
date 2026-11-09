/** Relative luminance (WCAG) of a `#rrggbb` color, 0 = black, 1 = white. */
export function luminance(hex: string): number {
  const match = /^#?([0-9a-f]{6})$/i.exec(hex.trim())
  if (!match) return 1
  const channels = [0, 2, 4].map((offset) => parseInt(match[1].slice(offset, offset + 2), 16) / 255)
  const [r, g, b] = channels.map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/** Ink colors that stay readable on the given card background. */
export function inkFor(background: string): { ink: string; muted: string; dark: boolean } {
  return luminance(background) < 0.3
    ? { ink: '#f5f6f8', muted: '#c3c8d2', dark: true }
    : { ink: '#1f2430', muted: '#5f6673', dark: false }
}
