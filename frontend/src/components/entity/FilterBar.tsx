import { Button, Group, NumberInput, Select, TextInput } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { IconFilterOff, IconSearch } from '@tabler/icons-react'
import { useEffect, useEffectEvent, useState } from 'react'
import { useLookups } from '../../hooks/useLookups'
import type { ResourceDefinition } from '../../resources/types'

interface Props {
  resource: ResourceDefinition
  values: Record<string, string>
  onChange(changes: Record<string, string | null>): void
  onClear(): void
}

export function FilterBar({ resource, values, onChange, onClear }: Props) {
  const lookups = useLookups()
  const [search, setSearch] = useState(values.search ?? '')
  const [debouncedSearch] = useDebouncedValue(search, 300)

  const pushSearch = useEffectEvent((text: string) => {
    if ((values.search ?? '') !== text) onChange({ search: text || null })
  })
  useEffect(() => pushSearch(debouncedSearch), [debouncedSearch])

  /** Changing a scope (system) clears filters that depend on it (campaign, race...). */
  const set = (param: string, value: string | null) => {
    const changes: Record<string, string | null> = { [param]: value }
    for (const filter of resource.filters) {
      if (filter.kind === 'reference' && filter.scopedBy === param) changes[filter.param] = null
    }
    onChange(changes)
  }

  const active = Object.keys(values).some((key) => key !== 'ordering' && key !== 'view' && values[key])

  return (
    <Group gap="sm" align="flex-end" wrap="wrap">
      <TextInput
        label="Search"
        placeholder="Name or description"
        leftSection={<IconSearch size={16} />}
        value={search}
        onChange={(event) => setSearch(event.currentTarget.value)}
        w={240}
      />
      {resource.filters.map((filter) => {
        switch (filter.kind) {
          case 'reference': {
            const scope = filter.scopedBy ? values[filter.scopedBy] : undefined
            const options = lookups.options[filter.lookup].filter(
              (option) => !scope || option.systemId === Number(scope),
            )
            return (
              <Select
                key={filter.param}
                label={filter.label}
                placeholder="Any"
                data={options.map(({ value, label }) => ({ value, label }))}
                value={values[filter.param] ?? null}
                onChange={(value) => set(filter.param, value)}
                searchable
                clearable
                w={190}
              />
            )
          }
          case 'choice':
            return (
              <Select
                key={filter.param}
                label={filter.label}
                placeholder="Any"
                data={filter.choices.map(({ value, label }) => ({ value, label }))}
                value={values[filter.param] ?? null}
                onChange={(value) => set(filter.param, value)}
                clearable
                w={150}
              />
            )
          case 'number':
            return (
              <NumberInput
                key={filter.param}
                label={filter.label}
                placeholder="Any"
                min={filter.min}
                max={filter.max}
                allowDecimal={false}
                value={values[filter.param] ?? ''}
                onChange={(value) => set(filter.param, value === '' ? null : String(value))}
                w={110}
              />
            )
          case 'text':
            return (
              <TextInput
                key={`${filter.param}:${values[filter.param] ?? ''}`}
                label={filter.label}
                placeholder={filter.placeholder}
                defaultValue={values[filter.param] ?? ''}
                onBlur={(event) => set(filter.param, event.currentTarget.value.trim() || null)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') set(filter.param, event.currentTarget.value.trim() || null)
                }}
                w={150}
              />
            )
        }
      })}
      <Select
        label="Sort by"
        data={resource.sortOptions}
        value={values.ordering ?? 'name'}
        onChange={(value) => onChange({ ordering: value === 'name' ? null : value })}
        allowDeselect={false}
        w={170}
      />
      {active && (
        <Button
          variant="subtle"
          color="gray"
          leftSection={<IconFilterOff size={16} />}
          onClick={() => {
            setSearch('')
            onClear()
          }}
        >
          Clear filters
        </Button>
      )}
    </Group>
  )
}
