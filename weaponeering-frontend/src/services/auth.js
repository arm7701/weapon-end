const AUTH_KEY = 'weaponeering-authenticated'
const USER_KEY = 'weaponeering-user'
const TOKEN_KEY = 'weaponeering-token'
const PROFILE_KEY = 'weaponeering-profile'

export function isAuthenticated() {
  return sessionStorage.getItem(AUTH_KEY) === 'true'
}

export function getAuthUser() {
  return sessionStorage.getItem(USER_KEY) || ''
}

export function getAuthToken() {
  return sessionStorage.getItem(TOKEN_KEY) || ''
}

export function getAuthProfile() {
  try {
    return JSON.parse(sessionStorage.getItem(PROFILE_KEY) || 'null')
  } catch {
    return null
  }
}

export function setAuth(user = 'super-app-user', profile = null) {
  sessionStorage.setItem(AUTH_KEY, 'true')
  sessionStorage.setItem(USER_KEY, user)
  if (profile?.token) {
    sessionStorage.setItem(TOKEN_KEY, profile.token)
  }
  if (profile) {
    sessionStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
  }
}

export function clearAuth() {
  sessionStorage.removeItem(AUTH_KEY)
  sessionStorage.removeItem(USER_KEY)
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(PROFILE_KEY)
}

export function authHeaders(extra = {}) {
  const token = getAuthToken()
  const headers = { ...extra }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return headers
}

export async function apiFetch(path, options = {}) {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  const headers = authHeaders({
    Accept: 'application/json',
    ...(options.body && !isFormData ? { 'Content-Type': 'application/json' } : {}),
    ...(options.headers || {}),
  })
  const response = await fetch(path, { ...options, headers })
  if (response.status === 401) {
    clearAuth()
    window.location.replace(`${import.meta.env.BASE_URL || '/'}login`)
    throw new Error('เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่')
  }
  return response
}
