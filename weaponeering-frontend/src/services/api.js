import { apiFetch } from './auth'
import { notifyDataChanged } from './dataSync'

const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export function apiUrl(path) {
  if (!path) return apiBase
  if (path.startsWith('http')) return path
  return `${apiBase}${path.startsWith('/') ? path : `/${path}`}`
}

async function parseResponse(response) {
  if (response.status === 204) return null
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export async function apiJson(path, options = {}) {
  const response = await apiFetch(apiUrl(path), {
    ...options,
    body: options.body != null ? JSON.stringify(options.body) : undefined,
  })
  const data = await parseResponse(response)
  if (!response.ok) {
    const detail = data?.detail || data?.message || response.statusText || 'คำขอไม่สำเร็จ'
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  const method = (options.method || 'GET').toUpperCase()
  if (method !== 'GET' && method !== 'HEAD') {
    notifyDataChanged(path)
  }
  return data
}

export function listResource(path, query = {}) {
  const params = new URLSearchParams()
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.set(key, value)
    }
  })
  const qs = params.toString()
  return apiJson(`${path}${qs ? `?${qs}` : ''}`)
}

export function createResource(path, body) {
  return apiJson(path, { method: 'POST', body })
}

export function updateResource(path, id, body) {
  return apiJson(`${path}/${id}`, { method: 'PATCH', body })
}

export function putResource(path, body) {
  return apiJson(path, { method: 'PUT', body })
}

export function deleteResource(path, id) {
  return apiJson(`${path}/${id}`, { method: 'DELETE' })
}

export async function uploadForm(path, formData) {
  const response = await apiFetch(apiUrl(path), {
    method: 'POST',
    body: formData,
  })
  const data = await parseResponse(response)
  if (!response.ok) {
    const detail = data?.detail || data?.message || response.statusText || 'อัปโหลดไม่สำเร็จ'
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  notifyDataChanged(path)
  return data
}
