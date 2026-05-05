const BASE = 'http://localhost:8080'

export async function sendChatMessage(message, turnId) {
  const response = await fetch(`${BASE}/api/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, turn_id: turnId }),
  })
  return response
}

export async function resumeInterruptedChat(message, turnId) {
  const response = await fetch(`${BASE}/api/agent/chat/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, turn_id: turnId }),
  })
  return response
}

export async function login(email, password) {
  const response = await fetch(`${BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return response.json()
}
