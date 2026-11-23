import { Center, Loader } from '@mantine/core'
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, type ReactNode } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { onUnauthorized } from '../api/http'
import { ME_QUERY_KEY, useAuth } from './useAuth'

/** Management pages: anonymous visitors go to /login and come back after signing in. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { master, loading } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // A session that expires mid-use makes any request answer 401: send the user to login.
  useEffect(() => {
    onUnauthorized(() => {
      queryClient.clear()
      queryClient.setQueryData(ME_QUERY_KEY, null)
      navigate('/login', { replace: true, state: { from: location.pathname } })
    })
    return () => onUnauthorized(null)
  }, [navigate, location.pathname, queryClient])

  if (loading) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    )
  }
  if (!master) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return children
}
