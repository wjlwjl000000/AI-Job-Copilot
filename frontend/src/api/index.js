import { getClientId } from '../utils/clientId'

const BASE = 'http://localhost:8080'

async function request(method, path, body) {
  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'x-client-id': getClientId(),
    },
  }
  if (body) opts.body = JSON.stringify(body)
  const r = await fetch(`${BASE}${path}`, opts)
  return r.json()
}

export const api = {
  // Auth
  register: (email, pwd) => request('POST', '/api/auth/register', { email, password: pwd }),
  login: (email, pwd) => request('POST', '/api/auth/login', { email, password: pwd }),

  // Profile
  getProfile: () => request('GET', '/api/profile'),
  updateProfile: (data) => request('PUT', '/api/profile', data),
  deleteProfile: () => request('DELETE', '/api/profile'),

  // Resumes
  listResumes: () => request('GET', '/api/resumes'),
  getResume: (id) => request('GET', `/api/resumes/${id}`),
  deleteResume: (id) => request('DELETE', `/api/resumes/${id}`),

  // Jobs
  getJob: (id) => request('GET', `/api/jobs/${id}`),
  createJob: (data) => request('POST', '/api/jobs', data),

  // Applications
  listApplications: (status) => request('GET', `/api/applications${status ? `?status=${status}` : ''}`),
  createApplication: (data) => request('POST', '/api/applications', data),
  updateApplication: (id, data) => request('PUT', `/api/applications/${id}`, data),
  getStats: () => request('GET', '/api/applications/stats'),

  // Sessions
  getSessions: () => request('GET', '/api/sessions'),
  createSession: (title) => request('POST', '/api/sessions', title ? { title } : {}),
  deleteSession: (id) => request('DELETE', `/api/sessions/${id}`),
  updateSession: (id, title) => request('PATCH', `/api/sessions/${id}`, { title }),
  getMessages: (sessionId) => request('GET', `/api/sessions/${sessionId}/messages`),

  // Agent Chat
  sendChatMessage: (message, sessionId) => {
    const body = { message }
    if (sessionId) body.session_id = sessionId
    return fetch(`${BASE}/api/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-client-id': getClientId(),
      },
      body: JSON.stringify(body),
    })
  },
  resumeChat: (message, sessionId) => {
    const body = { message }
    if (sessionId) body.session_id = sessionId
    return fetch(`${BASE}/api/agent/chat/resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-client-id': getClientId(),
      },
      body: JSON.stringify(body),
    })
  },

  // File parsing (MinerU)
  uploadFile: (formData, sessionId) => {
    if (sessionId) formData.append('session_id', sessionId)
    return fetch(`${BASE}/api/agent/parse-file`, { method: 'POST', body: formData }).then(r => r.json())
  },
  deleteFile: (fileId, sessionId) => request('DELETE', `/api/agent/parse-file/${fileId}?session_id=${encodeURIComponent(sessionId || '')}`),
  getFile: (fileId, sessionId) => request('GET', `/api/agent/parse-file/${fileId}?session_id=${encodeURIComponent(sessionId || '')}`),

  // Agent Registry
  listAgents: () => request('GET', '/api/agent/registry'),
  registerAgent: (url) => request('POST', '/api/agent/registry', { agent_url: url }),
  deleteAgent: (name) => request('DELETE', `/api/agent/registry/${name}`),
}
