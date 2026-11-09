import { Alert, Button, Group, Loader, Modal, ScrollArea, Stack, Text } from '@mantine/core'
import { IconPrinter } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import type { QueryParams } from '../../api/http'
import { useLookups } from '../../hooks/useLookups'
import type { ResourceDefinition } from '../../resources/types'
import { cardFor } from '../../resources/cards'
import { GameCard } from '../cards/GameCard'
import { CARDS_PER_PAGE, PrintSheet } from './PrintSheet'

export interface PrintRequest {
  title: string
  params: QueryParams
}

interface Props {
  resource: ResourceDefinition
  request: PrintRequest | null
  onClose(): void
}

export function PrintDialog({ resource, request, onClose }: Props) {
  const lookups = useLookups()
  const query = useQuery({
    queryKey: [resource.key, 'print', request?.params],
    queryFn: () => resource.api.listAll(request?.params ?? {}),
    enabled: request !== null,
  })

  const cards = (query.data ?? []).map((entity) => ({ id: entity.id, card: cardFor(resource, entity, lookups) }))
  const sheets = Math.ceil(cards.length / CARDS_PER_PAGE)
  const ready = query.isSuccess && !lookups.loading

  return (
    <Modal opened={request !== null} onClose={onClose} title={request?.title} size="auto" centered>
      <Stack gap="md" maw={760}>
        {query.isLoading && (
          <Group justify="center" py="xl">
            <Loader />
          </Group>
        )}
        {query.isError && (
          <Alert color="red" title="Could not load the cards">
            {(query.error as Error).message}
          </Alert>
        )}
        {ready && cards.length === 0 && <Text c="dimmed">No cards match these filters.</Text>}
        {ready && cards.length > 0 && (
          <>
            <Text size="sm" c="dimmed">
              {cards.length} {cards.length === 1 ? 'card' : 'cards'} at real size (6 × 9 cm) on {sheets} A4{' '}
              {sheets === 1 ? 'sheet' : 'sheets'}, 9 per sheet with dashed cut guides. In the print dialog, keep scale
              at 100% and turn on background graphics.
            </Text>
            <ScrollArea.Autosize mah="60vh" type="auto">
              <Group gap="sm" justify="center" p="xs" bg="gray.1" style={{ borderRadius: 8 }}>
                {cards.map(({ id, card }) => (
                  <GameCard key={id} card={card} />
                ))}
              </Group>
            </ScrollArea.Autosize>
            <PrintSheet cards={cards} />
          </>
        )}
        <Group justify="flex-end">
          <Button variant="default" onClick={onClose}>
            Close
          </Button>
          <Button leftSection={<IconPrinter size={18} />} disabled={!ready || cards.length === 0} onClick={() => window.print()}>
            Print {cards.length || ''} {cards.length === 1 ? 'card' : 'cards'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
