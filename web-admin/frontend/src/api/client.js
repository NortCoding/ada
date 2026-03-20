export async function api(path, options = {}) {
  const url = path && path.startsWith('http') ? path : `/api${path || ''}`

  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })

  const text = await res.text()
  const isJson = text && text.trim().startsWith('{')

  const data = isJson ? safeJsonParse(text) : text

  if (!res.ok) {
    const detail =
      (data && typeof data === 'object' && (data.detail || data.error)) ||
      (typeof data === 'string' ? data.slice(0, 400) : res.statusText)
    const err = new Error(`API ${res.status}: ${detail || res.statusText}`)
    err.status = res.status
    err.data = data
    throw err
  }

  return data
}

function safeJsonParse(s) {
  try {
    return JSON.parse(s)
  } catch (e) {
    return null
  }
}

