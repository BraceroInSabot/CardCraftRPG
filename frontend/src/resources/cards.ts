import type { BaseEntity } from '../domain/types'
import type { Lookups } from '../hooks/useLookups'
import type { CardModel, ResourceDefinition } from './types'

/** Resource-specific card content plus the appearance every card shares. */
export function cardFor(resource: ResourceDefinition, entity: BaseEntity, lookups: Lookups): CardModel {
  return {
    ...resource.toCard(entity, lookups),
    background: entity.background_color,
    imageUrl: entity.image_url,
  }
}
