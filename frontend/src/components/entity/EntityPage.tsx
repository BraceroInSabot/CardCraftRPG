import {
  Affix,
  Alert,
  Anchor,
  Button,
  Center,
  Group,
  Loader,
  Pagination,
  Paper,
  SegmentedControl,
  Stack,
  Text,
  Title,
  Transition,
} from '@mantine/core'
import { modals } from '@mantine/modals'
import { notifications } from '@mantine/notifications'
import { IconLayoutGrid, IconPlus, IconPrinter, IconTable } from '@tabler/icons-react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import type { BaseEntity } from '../../domain/types'
import { useLookups } from '../../hooks/useLookups'
import type { ResourceDefinition } from '../../resources/types'
import { PrintDialog, type PrintRequest } from '../print/PrintDialog'
import { EntityFormModal } from './EntityFormModal'
import { CardGridView, TableView } from './EntityViews'
import { FilterBar } from './FilterBar'

const PAGE_SIZE = 24
const UI_PARAMS = new Set(['view', 'page'])

/** Filter param -> form field to prefill when creating from a filtered list. */
const FILTER_TO_FIELD: Record<string, string> = {
  system: 'system_id',
  campaign: 'campaign_id',
  race: 'race_id',
  character_class: 'class_id',
}

/** "Race skills" -> "race skills", but "RPG systems" stays as is. */
function lowerFirst(text: string): string {
  return /^[A-Z][A-Z]/.test(text) ? text : text.charAt(0).toLowerCase() + text.slice(1)
}

export function EntityPage({ resource }: { resource: ResourceDefinition }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const lookups = useLookups()
  const queryClient = useQueryClient()

  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [formTarget, setFormTarget] = useState<BaseEntity | 'new' | null>(null)
  const [printRequest, setPrintRequest] = useState<PrintRequest | null>(null)

  const { view, page, filterValues } = useMemo(() => {
    const values = Object.fromEntries(searchParams.entries())
    return {
      view: (values.view as 'cards' | 'table' | undefined) ?? resource.defaultView,
      page: Number(values.page ?? 1),
      filterValues: Object.fromEntries(Object.entries(values).filter(([key]) => !UI_PARAMS.has(key))),
    }
  }, [searchParams, resource.defaultView])

  const listQuery = useQuery({
    queryKey: [resource.key, 'list', filterValues, page],
    queryFn: () => resource.api.list({ ...filterValues, page, page_size: PAGE_SIZE }),
    placeholderData: keepPreviousData,
  })

  const updateParams = (changes: Record<string, string | null>, resetPage = true) => {
    setSearchParams((current) => {
      const next = new URLSearchParams(current)
      for (const [key, value] of Object.entries(changes)) {
        if (value === null || value === '') next.delete(key)
        else next.set(key, value)
      }
      if (resetPage) next.delete('page')
      return next
    })
  }

  const clearFilters = () => {
    setSearchParams((current) => {
      const next = new URLSearchParams()
      const keptView = current.get('view')
      if (keptView) next.set('view', keptView)
      return next
    })
  }

  const remove = useMutation({
    mutationFn: (entity: BaseEntity) => resource.api.remove(entity.id),
    onSuccess: (_, entity) => {
      setSelected((current) => {
        const next = new Set(current)
        next.delete(entity.id)
        return next
      })
      queryClient.invalidateQueries()
      notifications.show({ color: 'teal', message: `${entity.name} deleted.` })
    },
    onError: (error) => notifications.show({ color: 'red', title: 'Not deleted', message: (error as Error).message }),
  })

  const confirmDelete = (entity: BaseEntity) =>
    modals.openConfirmModal({
      title: `Delete ${entity.name}?`,
      children: (
        <Text size="sm">
          This can’t be undone.{resource.deleteWarning ? ` ${resource.deleteWarning}` : ''}
        </Text>
      ),
      labels: { confirm: `Delete ${resource.singular}`, cancel: 'Keep it' },
      confirmProps: { color: 'red' },
      onConfirm: () => remove.mutate(entity),
    })

  const toggle = (id: number) =>
    setSelected((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  const toggleAll = (ids: number[], select: boolean) =>
    setSelected((current) => {
      const next = new Set(current)
      ids.forEach((id) => (select ? next.add(id) : next.delete(id)))
      return next
    })

  const formDefaults = Object.fromEntries(
    Object.entries(FILTER_TO_FIELD)
      .filter(([param]) => filterValues[param])
      .map(([param, field]) => [field, filterValues[param]]),
  )

  const data = listQuery.data
  const rows = data?.results ?? []
  const hasFilters = Object.keys(filterValues).some((key) => key !== 'ordering')
  const needsSystem = resource.key !== 'systems' && !lookups.loading && lookups.options.systems.length === 0
  const Icon = resource.icon
  const plural = lowerFirst(resource.label)
  const viewProps = {
    resource,
    rows,
    lookups,
    selected,
    onToggle: toggle,
    onToggleAll: toggleAll,
    onEdit: (entity: BaseEntity) => setFormTarget(entity),
    onDelete: confirmDelete,
  }

  return (
    <Stack gap="lg" pb={96}>
      <Group justify="space-between" align="flex-start" wrap="wrap">
        <Group gap="md" align="flex-start" wrap="nowrap">
          <Center w={44} h={44} style={{ borderRadius: 12, background: resource.color, color: '#fff', flexShrink: 0 }}>
            <Icon size={24} stroke={1.75} />
          </Center>
          <div>
            <Title order={2}>{resource.label}</Title>
            <Text c="dimmed" size="sm">
              {resource.summary}
            </Text>
          </div>
        </Group>
        <Group gap="sm">
          <Button
            variant="default"
            leftSection={<IconPrinter size={18} />}
            disabled={!data?.count}
            onClick={() =>
              setPrintRequest({
                title: hasFilters ? `Print matching ${plural}` : `Print all ${plural}`,
                params: filterValues,
              })
            }
          >
            {hasFilters ? 'Print matching' : 'Print all'} ({data?.count ?? 0})
          </Button>
          <Button leftSection={<IconPlus size={18} />} onClick={() => setFormTarget('new')} disabled={needsSystem}>
            New {resource.singular}
          </Button>
        </Group>
      </Group>

      {needsSystem && (
        <Alert color="indigo" title="Start with an RPG system">
          Everything is organised by system.{' '}
          <Anchor component={Link} to="/systems">
            Create your first RPG system
          </Anchor>{' '}
          and come back here.
        </Alert>
      )}

      <Paper p="md" radius="md" withBorder>
        <FilterBar
          key={resource.key}
          resource={resource}
          values={filterValues}
          onChange={updateParams}
          onClear={clearFilters}
        />
      </Paper>

      <Group justify="space-between">
        <Text size="sm" c="dimmed">
          {data ? `${data.count} ${data.count === 1 ? resource.singular : plural}` : ' '}
          {selected.size > 0 && `, ${selected.size} selected`}
        </Text>
        <SegmentedControl
          size="xs"
          value={view}
          onChange={(value) => updateParams({ view: value === resource.defaultView ? null : value }, false)}
          data={[
            { value: 'cards', label: <Group gap={6} wrap="nowrap"><IconLayoutGrid size={14} />Cards</Group> },
            { value: 'table', label: <Group gap={6} wrap="nowrap"><IconTable size={14} />Table</Group> },
          ]}
        />
      </Group>

      {listQuery.isLoading && (
        <Center py="xl">
          <Loader />
        </Center>
      )}
      {listQuery.isError && (
        <Alert color="red" title={`Could not load ${plural}`}>
          {(listQuery.error as Error).message}
        </Alert>
      )}

      {data && rows.length === 0 && (
        <Paper p="xl" radius="md" withBorder ta="center">
          {hasFilters ? (
            <Stack align="center" gap="xs">
              <Text fw={600}>No {plural} match these filters.</Text>
              <Button variant="light" onClick={clearFilters}>
                Clear filters
              </Button>
            </Stack>
          ) : (
            <Stack align="center" gap="xs">
              <Text fw={600}>No {plural} yet.</Text>
              <Text c="dimmed" size="sm">
                {resource.summary}
              </Text>
              {!needsSystem && (
                <Button variant="light" leftSection={<IconPlus size={16} />} onClick={() => setFormTarget('new')}>
                  Create the first {resource.singular}
                </Button>
              )}
            </Stack>
          )}
        </Paper>
      )}

      {rows.length > 0 && (view === 'cards' ? <CardGridView {...viewProps} /> : <TableView {...viewProps} />)}

      {data && data.total_pages > 1 && (
        <Group justify="center">
          <Pagination
            total={data.total_pages}
            value={page}
            onChange={(next) => updateParams({ page: next === 1 ? null : String(next) }, false)}
          />
        </Group>
      )}

      <Affix position={{ bottom: 24, left: 0, right: 0 }} zIndex={150}>
        <Transition transition="slide-up" mounted={selected.size > 0}>
          {(styles) => (
            <Center style={{ ...styles, pointerEvents: 'none' }}>
              <Paper shadow="lg" radius="xl" px="lg" py="sm" withBorder style={{ pointerEvents: 'auto' }}>
                <Group gap="md">
                  <Text fw={600}>
                    {selected.size} selected
                  </Text>
                  <Button variant="subtle" color="gray" onClick={() => setSelected(new Set())}>
                    Clear selection
                  </Button>
                  <Button
                    leftSection={<IconPrinter size={18} />}
                    onClick={() =>
                      setPrintRequest({
                        title: `Print ${selected.size} selected ${selected.size === 1 ? 'card' : 'cards'}`,
                        params: { ids: [...selected].join(',') },
                      })
                    }
                  >
                    Print selected
                  </Button>
                </Group>
              </Paper>
            </Center>
          )}
        </Transition>
      </Affix>

      <EntityFormModal
        resource={resource}
        target={formTarget}
        defaults={formDefaults}
        onClose={() => setFormTarget(null)}
      />
      <PrintDialog resource={resource} request={printRequest} onClose={() => setPrintRequest(null)} />
    </Stack>
  )
}
