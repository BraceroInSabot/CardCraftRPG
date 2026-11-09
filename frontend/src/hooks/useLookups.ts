import { useQueries } from '@tanstack/react-query'
import { api } from '../api/clients'
import type { BaseEntity } from '../domain/types'

export type LookupKey = 'systems' | 'campaigns' | 'races' | 'classes'

export interface LookupOption {
  value: string
  label: string
  systemId?: number
}

export interface Lookups {
  options: Record<LookupKey, LookupOption[]>
  label(key: LookupKey, id: number | null | undefined): string | undefined
  systemOf(key: LookupKey, id: number | null | undefined): number | undefined
  loading: boolean
}

export const LOOKUP_QUERY_KEY = 'lookup'

type Row = BaseEntity & { system_id?: number }

const sources: Record<LookupKey, () => Promise<Row[]>> = {
  systems: () => api.systems.listAll(),
  campaigns: () => api.campaigns.listAll(),
  races: () => api.races.listAll(),
  classes: () => api.classes.listAll(),
}

const KEYS = Object.keys(sources) as LookupKey[]

function buildLookups(results: { data?: Row[]; isLoading: boolean }[]): Lookups {
  const options = {} as Record<LookupKey, LookupOption[]>
  const index = {} as Record<LookupKey, Map<number, LookupOption>>
  KEYS.forEach((key, position) => {
    const rows = results[position].data ?? []
    options[key] = rows.map((row) => ({ value: String(row.id), label: row.name, systemId: row.system_id }))
    index[key] = new Map(options[key].map((option) => [Number(option.value), option]))
  })
  return {
    options,
    loading: results.some((result) => result.isLoading),
    label: (key, id) => (id == null ? undefined : index[key].get(id)?.label),
    systemOf: (key, id) => (id == null ? undefined : index[key].get(id)?.systemId),
  }
}

/** Small reference lists (systems, campaigns, races, classes) used by selects and cards. */
export function useLookups(): Lookups {
  return useQueries({
    queries: KEYS.map((key) => ({
      queryKey: [LOOKUP_QUERY_KEY, key],
      queryFn: sources[key],
      staleTime: 60_000,
    })),
    combine: buildLookups,
  })
}
