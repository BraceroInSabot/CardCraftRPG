import type { Master } from '../domain/types'
import { request } from './http'

export interface Credentials {
  username: string
  password: string
}

export interface ProfileChanges {
  display_name?: string
  email?: string
}

export interface PasswordChange {
  current_password: string
  new_password: string
}

/** Session login/logout and the signed-in Master's settings. */
export const accountApi = {
  login: (credentials: Credentials) =>
    request<Master>('/auth/login/', { method: 'POST', body: JSON.stringify(credentials) }),
  logout: () => request<void>('/auth/logout/', { method: 'POST' }),
  me: () => request<Master>('/account/'),
  updateProfile: (changes: ProfileChanges) =>
    request<Master>('/account/profile/', { method: 'PATCH', body: JSON.stringify(changes) }),
  updateCardDefaults: (default_background_color: string) =>
    request<Master>('/account/card-defaults/', {
      method: 'PATCH',
      body: JSON.stringify({ default_background_color }),
    }),
  changePassword: (change: PasswordChange) =>
    request<void>('/account/password/', { method: 'POST', body: JSON.stringify(change) }),
}
