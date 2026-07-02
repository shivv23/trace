const API_BASE = '/api'

function getToken() {
  return localStorage.getItem('trace_token')
}

function authHeaders() {
  const token = getToken()
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

function handleAuthError(response) {
  if (response.status === 401) {
    localStorage.removeItem('trace_token')
    localStorage.removeItem('trace_user')
    window.location.reload()
  }
  return response
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  const config = {
    headers: { 'Content-Type': 'application/json', ...authHeaders(), ...options.headers },
    ...options,
  }

  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
    config.body = JSON.stringify(config.body)
  }

  const response = await fetch(url, config)
  handleAuthError(response)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Request failed: ${response.status}`)
  }
  return response.json()
}

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: { username, password },
  })
  localStorage.setItem('trace_token', data.token)
  localStorage.setItem('trace_user', JSON.stringify({ id: data.user_id, username: data.username, isAdmin: data.is_admin }))
  return data
}

export async function register(username, password) {
  const data = await request('/auth/register', {
    method: 'POST',
    body: { username, password },
  })
  localStorage.setItem('trace_token', data.token)
  localStorage.setItem('trace_user', JSON.stringify({ id: data.user_id, username: data.username, isAdmin: data.is_admin }))
  return data
}

export async function getMe() {
  return request('/auth/me')
}

export function logout() {
  localStorage.removeItem('trace_token')
  localStorage.removeItem('trace_user')
}

export function getStoredUser() {
  const raw = localStorage.getItem('trace_user')
  return raw ? JSON.parse(raw) : null
}

export function isAuthenticated() {
  return !!getToken()
}

export async function sendMessage(message, conversationId = null, documentIds = null) {
  return request('/chat', {
    method: 'POST',
    body: { message, conversation_id: conversationId, document_ids: documentIds },
  })
}

export async function getConversation(conversationId) {
  return request(`/chat/${conversationId}`)
}

export async function uploadDocument(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const xhr = new XMLHttpRequest()
  return new Promise((resolve, reject) => {
    xhr.timeout = 120000
    xhr.upload.addEventListener('progress', (e) => {
      if (onProgress && e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })
    xhr.addEventListener('load', () => {
      if (xhr.status === 401) {
        handleAuthError({ status: 401 })
        reject(new Error('Session expired'))
        return
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        try {
          const err = JSON.parse(xhr.responseText)
          reject(new Error(err.detail || 'Upload failed'))
        } catch {
          reject(new Error('Upload failed'))
        }
      }
    })
    xhr.addEventListener('error', () => reject(new Error('Network error')))
    xhr.addEventListener('timeout', () => reject(new Error('Upload timed out')))
    xhr.open('POST', `${API_BASE}/documents/upload`)
    const token = getToken()
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.send(formData)
  })
}

export async function listDocuments() {
  return request('/documents')
}

export async function deleteDocument(docId) {
  return request(`/documents/${docId}`, { method: 'DELETE' })
}

export async function getDocumentInfo(docId) {
  return request(`/documents/${docId}`)
}

export async function submitFeedback(conversationId, messageIndex, rating, correctedAnswer = null) {
  return request('/feedback', {
    method: 'POST',
    body: {
      conversation_id: conversationId,
      message_index: messageIndex,
      rating,
      corrected_answer: correctedAnswer,
    },
  })
}

export async function listConversations() {
  return request('/chat/conversations/list')
}

export async function getConversationHistory(conversationId) {
  return request(`/chat/${conversationId}`)
}

export async function deleteConversation(conversationId) {
  return request(`/chat/${conversationId}`, { method: 'DELETE' })
}

export async function getAdminStats() {
  return request('/admin/stats')
}

export async function healthCheck() {
  return request('/health')
}
