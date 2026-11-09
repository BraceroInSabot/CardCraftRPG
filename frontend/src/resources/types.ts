import type { Icon } from '@tabler/icons-react'
import type { ReactNode } from 'react'
import type { ResourceApi } from '../api/resourceApi'
import type { BaseEntity, Choice } from '../domain/types'
import type { LookupKey, Lookups } from '../hooks/useLookups'

/** Everything a printed card shows, independent of the entity it came from. */
export interface CardModel {
  category: string
  title: string
  frameColor: string
  tags: { label: string; color: string }[]
  body: string
  stats: { label: string; value: string }[]
  /** Shown in the frame band, usually the RPG system. */
  origin?: string
  /** Small closing line, usually the campaign or parent race/class. */
  footnote?: string
}

interface BaseField {
  name: string
  label: string
  required?: boolean
  description?: string
}

export type FieldDef =
  | (BaseField & { kind: 'text' | 'textarea'; maxLength: number; placeholder?: string })
  | (BaseField & { kind: 'choice'; choices: Choice[] })
  | (BaseField & { kind: 'number'; min: number; max: number; placeholder?: string })
  | (BaseField & {
      kind: 'reference'
      lookup: LookupKey
      /** Only show options whose system matches the value of this form field. */
      scopedBy?: string
      /** The backend refuses changes after creation. */
      lockedOnEdit?: boolean
    })

export type FilterDef =
  | { kind: 'reference'; param: string; label: string; lookup: LookupKey; scopedBy?: string }
  | { kind: 'choice'; param: string; label: string; choices: Choice[] }
  | { kind: 'text'; param: string; label: string; placeholder?: string }
  | { kind: 'number'; param: string; label: string; min: number; max: number }

export interface ColumnDef<T> {
  key: string
  label: string
  render(entity: T, lookups: Lookups): ReactNode
}

export interface ResourceDefinition<T extends BaseEntity = BaseEntity> {
  key: string
  label: string
  singular: string
  summary: string
  icon: Icon
  color: string
  api: ResourceApi<T>
  fields: FieldDef[]
  filters: FilterDef[]
  columns: ColumnDef<T>[]
  sortOptions: { value: string; label: string }[]
  defaultView: 'cards' | 'table'
  deleteWarning?: string
  toCard(entity: T, lookups: Lookups): CardModel
}
