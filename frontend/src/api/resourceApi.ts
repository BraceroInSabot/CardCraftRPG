import type { BaseEntity, Page } from '../domain/types'
import { request, toQueryString, type QueryParams } from './http'

export const MAX_PAGE_SIZE = 500

export interface ResourceApi<T extends BaseEntity> {
  list(params?: QueryParams): Promise<Page<T>>
  listAll(params?: QueryParams): Promise<T[]>
  get(id: number): Promise<T>
  create(payload: Partial<T>): Promise<T>
  update(id: number, payload: Partial<T>): Promise<T>
  remove(id: number): Promise<void>
}

/** REST client for one backend resource (``/api/<path>/``). */
export function createResourceApi<T extends BaseEntity>(path: string): ResourceApi<T> {
  const base = `/${path}/`

  const list = (params: QueryParams = {}) => request<Page<T>>(`${base}${toQueryString(params)}`)

  return {
    list,
    async listAll(params = {}) {
      const results: T[] = []
      for (let page = 1; ; page += 1) {
        const batch = await list({ ...params, page, page_size: MAX_PAGE_SIZE })
        results.push(...batch.results)
        if (page >= batch.total_pages) return results
      }
    },
    get: (id) => request<T>(`${base}${id}/`),
    create: (payload) => request<T>(base, { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request<T>(`${base}${id}/`, { method: 'PUT', body: JSON.stringify(payload) }),
    remove: (id) => request<void>(`${base}${id}/`, { method: 'DELETE' }),
  }
}
