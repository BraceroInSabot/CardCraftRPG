import { Anchor, List, Paper, SimpleGrid, Stack, Text, Title } from '@mantine/core'
import { Link } from 'react-router-dom'
import { GameCard } from '../components/cards/GameCard'
import { RARITIES } from '../domain/types'

const sample = {
  category: 'Wondrous',
  title: 'Cloak of Embers',
  frameColor: RARITIES[2].color,
  tags: [{ label: 'Rare', color: RARITIES[2].color }],
  body: 'While wearing this charred cloak you resist fire damage. Once per day you can wreathe yourself in harmless flames.',
  stats: [
    { label: 'Cost', value: '4,000 gp' },
    { label: 'Weight', value: '1 lb' },
  ],
  origin: 'Ironvale Fantasy',
  footnote: 'The Ashen Crown',
}

const steps = [
  { to: '/systems', label: 'Create an RPG system', detail: 'The rule set everything else belongs to.' },
  { to: '/campaigns', label: 'Add campaigns', detail: 'Optional. Tie content to a single story.' },
  { to: '/items', label: 'Fill in items, races, classes and their skills', detail: 'Each one becomes a card.' },
  { to: '/items', label: 'Filter, select and print', detail: 'Cards print at 6 × 9 cm, nine per A4 sheet.' },
]

export function HomePage() {
  return (
    <SimpleGrid cols={{ base: 1, md: 2 }} spacing={48} maw={980}>
      <Stack gap="lg">
        <div>
          <Title order={1} ff="Alegreya, Georgia, serif" fw={800}>
            Your table’s cards, ready to cut.
          </Title>
          <Text c="dimmed" mt="xs" maw={460}>
            Keep every item, race, class and skill of your campaigns in one place, then print the ones your players
            need tonight.
          </Text>
        </div>
        <Paper withBorder radius="md" p="lg">
          <List spacing="md" type="ordered" center={false}>
            {steps.map((step) => (
              <List.Item key={step.label}>
                <Anchor component={Link} to={step.to} fw={600}>
                  {step.label}
                </Anchor>
                <Text size="sm" c="dimmed">
                  {step.detail}
                </Text>
              </List.Item>
            ))}
          </List>
        </Paper>
        <Text size="sm" c="dimmed">
          Want sample data? Run <code>python manage.py seed_demo</code> in the backend.
        </Text>
      </Stack>
      <Stack align="center" justify="center">
        <div style={{ transform: 'rotate(-3deg)', filter: 'drop-shadow(0 12px 24px rgb(31 36 48 / 25%))' }}>
          <GameCard card={sample} />
        </div>
        <Text size="xs" c="dimmed">
          Prints at 6 × 9 cm
        </Text>
      </Stack>
    </SimpleGrid>
  )
}
