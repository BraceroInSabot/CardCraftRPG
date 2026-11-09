import { createTheme, type MantineColorsTuple } from '@mantine/core'

const lapis: MantineColorsTuple = [
  '#eef3fb',
  '#dbe4f3',
  '#b4c6e5',
  '#8aa6d7',
  '#678bcb',
  '#517ac4',
  '#4571c2',
  '#3660ab',
  '#2c4f8a',
  '#22437f',
]

export const theme = createTheme({
  primaryColor: 'lapis',
  primaryShade: 8,
  colors: { lapis },
  defaultRadius: 'md',
  fontFamily: "'Alegreya Sans', 'Segoe UI', system-ui, sans-serif",
  headings: {
    fontFamily: "'Alegreya', Georgia, serif",
    fontWeight: '700',
  },
  black: '#1f2430',
})
