import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { accountApi } from '../api/accountApi'
import { ApiError } from '../api/http'
import { DEFAULT_BACKGROUND, type Master } from '../domain/types'

export const ME_QUERY_KEY = ['account', 'me'] as const

export interface AuthState {
  master: Master | null
  loading: boolean
  /** Forget everything cached for the previous session (after login/logout). */
  reset(master: Master | null): void
}

/** The signed-in Master, or `null` when the API answers 401. */
export function useAuth(): AuthState {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: async () => {
      try {
        return await accountApi.me()
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null
        throw error
      }
    },
    staleTime: Infinity,
    retry: false,
  })
  const reset = useCallback(
    (master: Master | null) => {
      queryClient.clear()
      queryClient.setQueryData(ME_QUERY_KEY, master)
    },
    [queryClient],
  )
  return { master: query.data ?? null, loading: query.isPending, reset }
}

/** Defaults for new cards; falls back to white before the account loads. */
export function useCardDefaults() {
  const { master } = useAuth()
  return { backgroundColor: master?.default_background_color ?? DEFAULT_BACKGROUND }
}
