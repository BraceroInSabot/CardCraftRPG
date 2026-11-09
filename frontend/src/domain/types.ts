export interface BaseEntity {
  id: number
  name: string
  description: string
}

export type RpgSystem = BaseEntity

export interface Campaign extends BaseEntity {
  system_id: number
}

export interface SystemScoped extends BaseEntity {
  system_id: number
  campaign_id: number | null
}

export type Rarity = 'common' | 'uncommon' | 'rare' | 'very_rare' | 'legendary' | 'artifact'
export type SkillKind = 'passive' | 'active' | 'reaction'

export interface Item extends SystemScoped {
  item_type: string
  rarity: Rarity
  cost: string
  weight: string
}

export type Race = SystemScoped
export type CharacterClass = SystemScoped

export interface Skill extends BaseEntity {
  kind: SkillKind
  level: number | null
  cost: string
}

export interface RaceSkill extends Skill {
  race_id: number
}

export interface ClassSkill extends Skill {
  class_id: number
}

export interface Page<T> {
  count: number
  page: number
  page_size: number
  total_pages: number
  results: T[]
}

export interface Choice<V extends string = string> {
  value: V
  label: string
  color: string
}

export const RARITIES: Choice<Rarity>[] = [
  { value: 'common', label: 'Common', color: '#6b7280' },
  { value: 'uncommon', label: 'Uncommon', color: '#2f855a' },
  { value: 'rare', label: 'Rare', color: '#2b6cb0' },
  { value: 'very_rare', label: 'Very rare', color: '#6b46c1' },
  { value: 'legendary', label: 'Legendary', color: '#c05621' },
  { value: 'artifact', label: 'Artifact', color: '#9b2c2c' },
]

export const SKILL_KINDS: Choice<SkillKind>[] = [
  { value: 'passive', label: 'Passive', color: '#4a5568' },
  { value: 'active', label: 'Active', color: '#2c4f8a' },
  { value: 'reaction', label: 'Reaction', color: '#975a16' },
]

export function choiceFor<V extends string>(choices: Choice<V>[], value: V): Choice<V> | undefined {
  return choices.find((choice) => choice.value === value)
}
