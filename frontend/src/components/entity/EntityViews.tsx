import { ActionIcon, Checkbox, Group, Table, Tooltip } from '@mantine/core'
import { IconPencil, IconTrash } from '@tabler/icons-react'
import type { BaseEntity } from '../../domain/types'
import type { Lookups } from '../../hooks/useLookups'
import type { ResourceDefinition } from '../../resources/types'
import { cardFor } from '../../resources/cards'
import { GameCard } from '../cards/GameCard'
import classes from './EntityViews.module.css'

interface ViewProps {
  resource: ResourceDefinition
  rows: BaseEntity[]
  lookups: Lookups
  selected: Set<number>
  onToggle(id: number): void
  onToggleAll(ids: number[], select: boolean): void
  onEdit(entity: BaseEntity): void
  onDelete(entity: BaseEntity): void
}

function RowActions({ entity, resource, onEdit, onDelete }: Pick<ViewProps, 'resource' | 'onEdit' | 'onDelete'> & { entity: BaseEntity }) {
  return (
    <Group gap={4} wrap="nowrap">
      <Tooltip label={`Edit ${resource.singular}`}>
        <ActionIcon variant="subtle" color="gray" onClick={() => onEdit(entity)} aria-label={`Edit ${entity.name}`}>
          <IconPencil size={18} />
        </ActionIcon>
      </Tooltip>
      <Tooltip label={`Delete ${resource.singular}`}>
        <ActionIcon variant="subtle" color="red" onClick={() => onDelete(entity)} aria-label={`Delete ${entity.name}`}>
          <IconTrash size={18} />
        </ActionIcon>
      </Tooltip>
    </Group>
  )
}

export function CardGridView(props: ViewProps) {
  const { resource, rows, lookups, selected, onToggle } = props
  return (
    <div className={classes.grid}>
      {rows.map((entity) => {
        const isSelected = selected.has(entity.id)
        return (
          <div key={entity.id} className={classes.slot} data-selected={isSelected || undefined}>
            <div className={classes.cardFrame} onClick={() => onToggle(entity.id)}>
              <GameCard card={cardFor(resource, entity, lookups)} />
            </div>
            <Group justify="space-between" mt={6} px={2}>
              <Checkbox
                size="xs"
                label="Select"
                checked={isSelected}
                onChange={() => onToggle(entity.id)}
                aria-label={`Select ${entity.name}`}
              />
              <RowActions entity={entity} {...props} />
            </Group>
          </div>
        )
      })}
    </div>
  )
}

export function TableView(props: ViewProps) {
  const { resource, rows, lookups, selected, onToggle, onToggleAll } = props
  const ids = rows.map((row) => row.id)
  const selectedOnPage = ids.filter((id) => selected.has(id)).length

  return (
    <Table.ScrollContainer minWidth={640}>
      <Table highlightOnHover verticalSpacing="sm" className={classes.table}>
        <Table.Thead>
          <Table.Tr>
            <Table.Th w={40}>
              <Checkbox
                aria-label="Select all on this page"
                checked={selectedOnPage > 0 && selectedOnPage === ids.length}
                indeterminate={selectedOnPage > 0 && selectedOnPage < ids.length}
                onChange={() => onToggleAll(ids, selectedOnPage < ids.length)}
              />
            </Table.Th>
            {resource.columns.map((column) => (
              <Table.Th key={column.key}>{column.label}</Table.Th>
            ))}
            <Table.Th w={90} />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((entity) => (
            <Table.Tr key={entity.id} bg={selected.has(entity.id) ? 'var(--mantine-primary-color-light)' : undefined}>
              <Table.Td>
                <Checkbox
                  aria-label={`Select ${entity.name}`}
                  checked={selected.has(entity.id)}
                  onChange={() => onToggle(entity.id)}
                />
              </Table.Td>
              {resource.columns.map((column) => (
                <Table.Td key={column.key}>{column.render(entity, lookups)}</Table.Td>
              ))}
              <Table.Td>
                <RowActions entity={entity} {...props} />
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  )
}
