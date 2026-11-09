export interface BaseEntity {
  id: number
  name: string
  description: string
  /** Card background, hex like `#ffffff`. */
  background_color: string
  /** Absolute URL of the card illustration, or null. */
  image_url: string | null
}

export const DEFAULT_BACKGROUND = '#ffffff'

/** Preset card backgrounds offered in the color picker. */
export const BACKGROUND_SWATCHES = [
  '#ffffff',
  '#f6ecd6',
  '#efe4cf',
  '#e8f1f2',
  '#e6efe3',
  '#f6e4e4',
  '#ece6f5',
  '#2b3242',
  '#1f2430',
]

export const IMAGE_RULES = {
  accept: 'image/png,image/jpeg,image/webp,image/gif',
  types: ['image/png', 'image/jpeg', 'image/webp', 'image/gif'],
  maxBytes: 5 * 1024 * 1024,
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
  /** Only kept for weapons (see `isWeapon`). */
  damage: string
}

/** Item types that carry a damage value. Mirrors the backend rule. */
const WEAPON_ITEM_TYPES = ['arma']

export function isWeapon(itemType: unknown): boolean {
  return typeof itemType === 'string' && WEAPON_ITEM_TYPES.includes(itemType.trim().toLowerCase())
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
  { value: 'common', label: 'Comum', color: '#6b7280' },
  { value: 'uncommon', label: 'Incomum', color: '#2f855a' },
  { value: 'rare', label: 'Raro', color: '#2b6cb0' },
  { value: 'very_rare', label: 'Muito raro', color: '#6b46c1' },
  { value: 'legendary', label: 'Lendário', color: '#c05621' },
  { value: 'artifact', label: 'Artefato', color: '#9b2c2c' },
]

export const SKILL_KINDS: Choice<SkillKind>[] = [
  { value: 'passive', label: 'Passive', color: '#4a5568' },
  { value: 'active', label: 'Active', color: '#2c4f8a' },
  { value: 'reaction', label: 'Reaction', color: '#975a16' },
]

export function choiceFor<V extends string>(choices: Choice<V>[], value: V): Choice<V> | undefined {
  return choices.find((choice) => choice.value === value)
}
