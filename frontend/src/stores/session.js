import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api'
import { getClientId } from '../utils/clientId'

export const useSessionStore = defineStore('session', () => {
  const clientId = ref(getClientId())
  const sessions = ref([])
  const currentId = ref(null)
  const messages = ref([])
  const fileList = ref([])
  const profile = ref({})
  const resumes = ref([])

  async function fetchSessions() {
    const data = await api.getSessions()
    sessions.value = data
    if (data.length > 0) {
      await switchSession(data[0].id)
    } else {
      await createSession()
    }
  }

  async function createSession(title) {
    const data = await api.createSession(title)
    sessions.value.unshift(data)
    await switchSession(data.id)
  }

  async function deleteSession(id) {
    await api.deleteSession(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentId.value === id) {
      messages.value = []
      fileList.value = []
      currentId.value = null
      if (sessions.value.length > 0) {
        await switchSession(sessions.value[0].id)
      } else {
        await createSession()
      }
    }
  }

  async function switchSession(id) {
    currentId.value = id
    fileList.value = []
    const data = await api.getMessages(id)
    messages.value = data.map(m => ({ role: m.role, content: m.content, id: m.id }))
  }

  function addMessage(role, content, attachment = null) {
    const msg = { role, content, id: Date.now() }
    if (attachment) msg.attachment = attachment
    messages.value.push(msg)
  }

  async function fetchProfile() {
    try {
      const data = await api.getProfile()
      if (data && data.id) profile.value = data
    } catch (e) {}
  }

  async function fetchResumes() {
    try {
      const data = await api.listResumes()
      resumes.value = Array.isArray(data) ? data : []
    } catch (e) {}
  }

  return {
    clientId,
    sessions,
    currentId,
    messages,
    fileList,
    profile,
    resumes,
    fetchSessions,
    createSession,
    deleteSession,
    switchSession,
    addMessage,
    fetchProfile,
    fetchResumes,
  }
})
