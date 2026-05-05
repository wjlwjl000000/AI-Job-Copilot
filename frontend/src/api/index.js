const BASE = 'http://localhost:8080'

async function request(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } }
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

  // Resumes
  uploadResume: (formData) => fetch(`${BASE}/api/resumes/upload`, { method: 'POST', body: formData }).then(r => r.json()),
  listResumes: () => request('GET', '/api/resumes'),
  deleteResume: (id) => request('DELETE', `/api/resumes/${id}`),

  // Jobs
  getJob: (id) => request('GET', `/api/jobs/${id}`),
  createJob: (data) => request('POST', '/api/jobs', data),

  // Applications
  listApplications: (status) => request('GET', `/api/applications${status ? `?status=${status}` : ''}`),
  createApplication: (data) => request('POST', '/api/applications', data),
  updateApplication: (id, data) => request('PUT', `/api/applications/${id}`, data),
  getStats: () => request('GET', '/api/applications/stats'),

  // Agent Chat
  sendChatMessage: (message, turnId) => fetch(`${BASE}/api/agent/chat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, turn_id: turnId }),
  }),
  resumeChat: (message, turnId) => fetch(`${BASE}/api/agent/chat/resume`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, turn_id: turnId }),
  }),

  // Agent Registry
  listAgents: () => request('GET', '/api/agent/registry'),
  registerAgent: (url) => request('POST', '/api/agent/registry', { agent_url: url }),
  deleteAgent: (name) => request('DELETE', `/api/agent/registry/${name}`),
}
