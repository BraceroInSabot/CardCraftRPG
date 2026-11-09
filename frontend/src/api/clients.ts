import type {
  Campaign,
  CharacterClass,
  ClassSkill,
  Item,
  Race,
  RaceSkill,
  RpgSystem,
} from '../domain/types'
import { createResourceApi } from './resourceApi'

export const api = {
  systems: createResourceApi<RpgSystem>('systems'),
  campaigns: createResourceApi<Campaign>('campaigns'),
  items: createResourceApi<Item>('items'),
  races: createResourceApi<Race>('races'),
  raceSkills: createResourceApi<RaceSkill>('race-skills'),
  classes: createResourceApi<CharacterClass>('classes'),
  classSkills: createResourceApi<ClassSkill>('class-skills'),
}
