import { Badge, Text } from '@mantine/core'
import {
  IconBook2,
  IconBolt,
  IconDiamond,
  IconFlag3,
  IconShieldHalf,
  IconSparkles,
  IconUsersGroup,
} from '@tabler/icons-react'
import { api } from '../api/clients'
import {
  RARITIES,
  SKILL_KINDS,
  choiceFor,
  isWeapon,
  type BaseEntity,
  type Campaign,
  type CharacterClass,
  type ClassSkill,
  type Item,
  type Race,
  type RaceSkill,
  type RpgSystem,
  type Skill,
  type SystemScoped,
} from '../domain/types'
import type { Lookups } from '../hooks/useLookups'
import type { CardModel, ColumnDef, FieldDef, FilterDef, ResourceDefinition } from './types'

const COLORS = {
  system: '#3d4a5c',
  campaign: '#6a4c93',
  race: '#2f7d6d',
  class: '#a23b3b',
}

// ---------------------------------------------------------------------------
// Reusable building blocks
// ---------------------------------------------------------------------------

const nameField: FieldDef = { kind: 'text', name: 'name', label: 'Name', required: true, maxLength: 120 }
const descriptionField: FieldDef = {
  kind: 'textarea',
  name: 'description',
  label: 'Description',
  maxLength: 1200,
  description: 'Printed on the card. Long texts shrink to fit the 6 × 9 cm card.',
}
const systemField: FieldDef = { kind: 'reference', name: 'system_id', label: 'RPG system', lookup: 'systems', required: true }
const campaignField: FieldDef = {
  kind: 'reference',
  name: 'campaign_id',
  label: 'Campaign',
  lookup: 'campaigns',
  scopedBy: 'system_id',
  description: 'Leave empty if it belongs to the whole system.',
}
const skillFields: FieldDef[] = [
  { kind: 'choice', name: 'kind', label: 'Kind', choices: SKILL_KINDS, required: true },
  { kind: 'number', name: 'level', label: 'Required level', min: 0, max: 100, placeholder: 'Any level' },
  { kind: 'text', name: 'cost', label: 'Cost', maxLength: 60, placeholder: '2 mana, 1/rest…' },
]

const systemFilter: FilterDef = { kind: 'reference', param: 'system', label: 'System', lookup: 'systems' }
const campaignFilter: FilterDef = {
  kind: 'reference',
  param: 'campaign',
  label: 'Campaign',
  lookup: 'campaigns',
  scopedBy: 'system',
}
const skillFilters: FilterDef[] = [
  { kind: 'choice', param: 'kind', label: 'Kind', choices: SKILL_KINDS },
  { kind: 'number', param: 'level', label: 'Level', min: 0, max: 100 },
]

const sortOptions = [
  { value: 'name', label: 'Name, A to Z' },
  { value: '-name', label: 'Name, Z to A' },
  { value: '-id', label: 'Newest first' },
  { value: 'id', label: 'Oldest first' },
]

const nameColumn: ColumnDef<BaseEntity> = {
  key: 'name',
  label: 'Name',
  render: (entity) => (
    <div>
      <Text fw={600} size="sm">
        {entity.name}
      </Text>
      {entity.description && (
        <Text size="xs" c="dimmed" lineClamp={1} maw={420}>
          {entity.description}
        </Text>
      )}
    </div>
  ),
}

const systemColumn: ColumnDef<{ system_id: number } & BaseEntity> = {
  key: 'system',
  label: 'System',
  render: (entity, lookups) => lookups.label('systems', entity.system_id) ?? '—',
}

const campaignColumn: ColumnDef<SystemScoped> = {
  key: 'campaign',
  label: 'Campaign',
  render: (entity, lookups) =>
    lookups.label('campaigns', entity.campaign_id) ?? (
      <Text size="sm" c="dimmed">
        Whole system
      </Text>
    ),
}

function choiceBadge(color: string | undefined, label: string | undefined) {
  return label ? (
    <Badge variant="light" color={color} radius="sm" tt="none">
      {label}
    </Badge>
  ) : null
}

const skillColumns: ColumnDef<Skill>[] = [
  { key: 'kind', label: 'Kind', render: (s) => choiceBadge(choiceFor(SKILL_KINDS, s.kind)?.color, choiceFor(SKILL_KINDS, s.kind)?.label) },
  { key: 'level', label: 'Level', render: (s) => s.level ?? '—' },
  { key: 'cost', label: 'Cost', render: (s) => s.cost || '—' },
]

function scopedCard(entity: SystemScoped, lookups: Lookups, category: string, frameColor: string): CardModel {
  return {
    category,
    title: entity.name,
    frameColor,
    tags: [],
    body: entity.description,
    stats: [],
    origin: lookups.label('systems', entity.system_id),
    footnote: lookups.label('campaigns', entity.campaign_id),
  }
}

function skillCard(skill: Skill, category: string, frameColor: string, parent?: string, system?: string): CardModel {
  const kind = choiceFor(SKILL_KINDS, skill.kind)
  const stats = [
    ...(skill.level != null ? [{ label: 'Level', value: String(skill.level) }] : []),
    ...(skill.cost ? [{ label: 'Cost', value: skill.cost }] : []),
  ]
  return {
    category,
    title: skill.name,
    frameColor,
    tags: kind ? [{ label: kind.label, color: kind.color }] : [],
    body: skill.description,
    stats,
    origin: system,
    footnote: parent,
  }
}

function define<T extends BaseEntity>(definition: ResourceDefinition<T>): ResourceDefinition {
  return definition as unknown as ResourceDefinition
}

// ---------------------------------------------------------------------------
// Resources
// ---------------------------------------------------------------------------

export const resources: ResourceDefinition[] = [
  define<Item>({
    key: 'items',
    label: 'Items',
    singular: 'item',
    summary: 'Weapons, potions, relics and everything your players can carry.',
    icon: IconDiamond,
    color: '#b7791f',
    api: api.items,
    defaultView: 'cards',
    fields: [
      nameField,
      systemField,
      campaignField,
      {
        kind: 'text',
        name: 'item_type',
        label: 'Type',
        maxLength: 60,
        placeholder: 'Arma, Poção, Armadura…',
        description: 'Type “Arma” to add a damage value.',
      },
      {
        kind: 'text',
        name: 'damage',
        label: 'Damage',
        maxLength: 60,
        placeholder: '1d8 cortante',
        visibleWhen: (values) => isWeapon(values.item_type),
      },
      { kind: 'choice', name: 'rarity', label: 'Rarity', choices: RARITIES, required: true },
      { kind: 'text', name: 'cost', label: 'Cost', maxLength: 60, placeholder: '50 gp' },
      { kind: 'text', name: 'weight', label: 'Weight', maxLength: 60, placeholder: '1 lb' },
      descriptionField,
    ],
    filters: [
      systemFilter,
      campaignFilter,
      { kind: 'choice', param: 'rarity', label: 'Rarity', choices: RARITIES },
      { kind: 'text', param: 'item_type', label: 'Type', placeholder: 'Exact type' },
    ],
    columns: [
      nameColumn,
      { key: 'type', label: 'Type', render: (item) => item.item_type || '—' },
      {
        key: 'rarity',
        label: 'Rarity',
        render: (item) => {
          const rarity = choiceFor(RARITIES, item.rarity)
          return choiceBadge(rarity?.color, rarity?.label)
        },
      },
      systemColumn,
      campaignColumn,
    ],
    sortOptions: [...sortOptions, { value: 'rarity', label: 'Rarity' }, { value: 'item_type', label: 'Type' }],
    toCard: (item, lookups) => {
      const rarity = choiceFor(RARITIES, item.rarity)
      return {
        ...scopedCard(item, lookups, item.item_type || 'Item', rarity?.color ?? '#6b7280'),
        tags: rarity ? [{ label: rarity.label, color: rarity.color }] : [],
        stats: [
          ...(isWeapon(item.item_type) && item.damage ? [{ label: 'Damage', value: item.damage }] : []),
          ...(item.cost ? [{ label: 'Cost', value: item.cost }] : []),
          ...(item.weight ? [{ label: 'Weight', value: item.weight }] : []),
        ],
      }
    },
  }),

  define<Race>({
    key: 'races',
    label: 'Races',
    singular: 'race',
    summary: 'Peoples and ancestries available to player characters.',
    icon: IconUsersGroup,
    color: COLORS.race,
    api: api.races,
    defaultView: 'cards',
    deleteWarning: 'Its race skills will be deleted too.',
    fields: [nameField, systemField, campaignField, descriptionField],
    filters: [systemFilter, campaignFilter],
    columns: [nameColumn, systemColumn, campaignColumn],
    sortOptions,
    toCard: (race, lookups) => scopedCard(race, lookups, 'Race', COLORS.race),
  }),

  define<RaceSkill>({
    key: 'race-skills',
    label: 'Race skills',
    singular: 'race skill',
    summary: 'Traits and abilities granted by a race.',
    icon: IconSparkles,
    color: COLORS.race,
    api: api.raceSkills,
    defaultView: 'cards',
    fields: [
      nameField,
      { kind: 'reference', name: 'race_id', label: 'Race', lookup: 'races', required: true },
      ...skillFields,
      descriptionField,
    ],
    filters: [systemFilter, { kind: 'reference', param: 'race', label: 'Race', lookup: 'races', scopedBy: 'system' }, ...skillFilters],
    columns: [
      nameColumn,
      { key: 'race', label: 'Race', render: (s, lookups) => lookups.label('races', s.race_id) ?? '—' },
      ...(skillColumns as ColumnDef<RaceSkill>[]),
    ],
    sortOptions: [...sortOptions, { value: 'level', label: 'Level' }],
    toCard: (skill, lookups) =>
      skillCard(
        skill,
        'Race skill',
        COLORS.race,
        lookups.label('races', skill.race_id),
        lookups.label('systems', lookups.systemOf('races', skill.race_id)),
      ),
  }),

  define<CharacterClass>({
    key: 'classes',
    label: 'Classes',
    singular: 'class',
    summary: 'Professions and archetypes that shape how characters play.',
    icon: IconShieldHalf,
    color: COLORS.class,
    api: api.classes,
    defaultView: 'cards',
    deleteWarning: 'Its class skills will be deleted too.',
    fields: [nameField, systemField, campaignField, descriptionField],
    filters: [systemFilter, campaignFilter],
    columns: [nameColumn, systemColumn, campaignColumn],
    sortOptions,
    toCard: (characterClass, lookups) => scopedCard(characterClass, lookups, 'Class', COLORS.class),
  }),

  define<ClassSkill>({
    key: 'class-skills',
    label: 'Class skills',
    singular: 'class skill',
    summary: 'Powers, spells and techniques learned by a class.',
    icon: IconBolt,
    color: COLORS.class,
    api: api.classSkills,
    defaultView: 'cards',
    fields: [
      nameField,
      { kind: 'reference', name: 'class_id', label: 'Class', lookup: 'classes', required: true },
      ...skillFields,
      descriptionField,
    ],
    filters: [
      systemFilter,
      { kind: 'reference', param: 'character_class', label: 'Class', lookup: 'classes', scopedBy: 'system' },
      ...skillFilters,
    ],
    columns: [
      nameColumn,
      { key: 'class', label: 'Class', render: (s, lookups) => lookups.label('classes', s.class_id) ?? '—' },
      ...(skillColumns as ColumnDef<ClassSkill>[]),
    ],
    sortOptions: [...sortOptions, { value: 'level', label: 'Level' }],
    toCard: (skill, lookups) =>
      skillCard(
        skill,
        'Class skill',
        COLORS.class,
        lookups.label('classes', skill.class_id),
        lookups.label('systems', lookups.systemOf('classes', skill.class_id)),
      ),
  }),

  define<RpgSystem>({
    key: 'systems',
    label: 'RPG systems',
    singular: 'RPG system',
    summary: 'Rule sets. Every campaign, item, race and class belongs to one.',
    icon: IconBook2,
    color: COLORS.system,
    api: api.systems,
    defaultView: 'table',
    deleteWarning: 'All its campaigns, items, races, classes and skills will be deleted too.',
    fields: [nameField, descriptionField],
    filters: [],
    columns: [nameColumn],
    sortOptions,
    toCard: (system) => ({
      category: 'RPG system',
      title: system.name,
      frameColor: COLORS.system,
      tags: [],
      body: system.description,
      stats: [],
    }),
  }),

  define<Campaign>({
    key: 'campaigns',
    label: 'Campaigns',
    singular: 'campaign',
    summary: 'Stories run in a system. Content can be tied to one campaign.',
    icon: IconFlag3,
    color: COLORS.campaign,
    api: api.campaigns,
    defaultView: 'table',
    deleteWarning: 'Content tied to it stays in the system, without a campaign.',
    fields: [{ ...systemField, lockedOnEdit: true } as FieldDef, nameField, descriptionField],
    filters: [systemFilter],
    columns: [nameColumn, systemColumn],
    sortOptions,
    toCard: (campaign, lookups) => ({
      category: 'Campaign',
      title: campaign.name,
      frameColor: COLORS.campaign,
      tags: [],
      body: campaign.description,
      stats: [],
      origin: lookups.label('systems', campaign.system_id),
    }),
  }),
]

export function findResource(key: string | undefined): ResourceDefinition | undefined {
  return resources.find((resource) => resource.key === key)
}

export const CARD_RESOURCE_KEYS = ['items', 'races', 'race-skills', 'classes', 'class-skills']
