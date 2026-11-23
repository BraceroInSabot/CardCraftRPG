const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api'

export type FieldErrors = Record<string, string[]>

export class ApiError extends Error {
  readonly status: number
  readonly fieldErrors: FieldErrors

  constructor(status: number, message: string, fieldErrors: FieldErrors = {}) {
    super(message)
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown = null
  try {
    body = await response.json()
  } catch {
    // Non-JSON error bodies (e.g. a proxy error page) fall through.
  }
  if (body && typeof body === 'object') {
    const record = body as Record<string, unknown>
    if (typeof record.detail === 'string') return new ApiError(response.status, record.detail)
    const fieldErrors: FieldErrors = {}
    for (const [field, messages] of Object.entries(record)) {
      fieldErrors[field] = Array.isArray(messages) ? messages.map(String) : [String(messages)]
    }
    return new ApiError(response.status, 'Some fields need attention.', fieldErrors)
  }
  return new ApiError(response.status, `The server answered with status ${response.status}.`)
}

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])
const CSRF_COOKIE = 'csrftoken'

let unauthorizedHandler: (() => void) | null = null

/** Called whenever the API answers 401 (session missing or expired). */
export function onUnauthorized(handler: (() => void) | null) {
  unauthorizedHandler = handler
}

function readCookie(name: string): string | null {
  const match = document.cookie.split('; ').find((part) => part.startsWith(`${name}=`))
  return match ? decodeURIComponent(match.slice(name.length + 1)) : null
}

/** Django only accepts unsafe requests that echo the CSRF cookie; fetch it once if missing. */
async function csrfToken(): Promise<string | null> {
  if (!readCookie(CSRF_COOKIE)) await fetch(`${API_BASE}/auth/csrf/`, { credentials: 'same-origin' })
  return readCookie(CSRF_COOKIE)
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    // FormData bodies (file uploads) need the browser to set the multipart boundary.
    const headers = new Headers(init.headers)
    headers.set('Accept', 'application/json')
    if (!(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
    if (!SAFE_METHODS.has((init.method ?? 'GET').toUpperCase())) {
      const token = await csrfToken()
      if (token) headers.set('X-CSRFToken', token)
    }
    response = await fetch(`${API_BASE}${path}`, { ...init, headers, credentials: 'same-origin' })
  } catch {
    throw new ApiError(0, 'Could not reach the API. Check that the backend is running.')
  }
  if (response.status === 401) unauthorizedHandler?.()
  if (!response.ok) throw await toApiError(response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export type QueryParams = Record<string, string | number | undefined | null>

export function toQueryString(params: QueryParams): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}
