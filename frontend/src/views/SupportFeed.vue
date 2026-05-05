<template>
  <div class="support">
    <h1>Support & Encouragement</h1>
    <p class="sub">Everyone needs support during job hunting. Click a button to get encouragement.</p>
    <div class="triggers">
      <button @click="getSupport('I feel discouraged')">Need Encouragement</button>
      <button @click="getSupport('I just got rejected')">Got Rejected</button>
      <button @click="getSupport('I have an interview coming up')">Interview Anxiety</button>
      <button @click="getSupport('daily checkin')">Daily Check-in</button>
    </div>
    <div v-if="messages.length" class="feed">
      <div v-for="(m, i) in messages" :key="i" class="msg">
        <div class="role">{{ m.role === 'user' ? 'You' : 'Support' }}</div>
        <div class="text">{{ m.content }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../api'
const messages = ref([])
async function getSupport(prompt) {
  messages.value.push({ role: 'user', content: prompt })
  const r = await api.sendChatMessage(prompt, null)
  const reader = r.body.getReader(), decoder = new TextDecoder(); let buf = ''
  while (true) {
    const { done, value } = await reader.read(); if (done) break
    buf += decoder.decode(value, { stream: true })
    const lines = buf.split('\n'); buf = lines.pop() || ''
    for (const l of lines) {
      if (l.startsWith('data: ')) {
        try { const d = JSON.parse(l.slice(6)); if (d.type === 'response') messages.value.push({ role: 'agent', content: d.content }) } catch(e) {}
      }
    }
  }
}
</script>

<style scoped>
.sub { color: #666; margin-bottom: 20px; }
.triggers { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px; }
.triggers button { padding: 10px 18px; border: none; border-radius: 8px; cursor: pointer; background: #e94560; color: white; font-size: 14px; }
.triggers button:hover { opacity: 0.9; }
.feed { display: flex; flex-direction: column; gap: 12px; }
.msg { background: white; padding: 12px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.role { font-weight: bold; font-size: 12px; color: #1976d2; margin-bottom: 4px; }
.text { line-height: 1.5; }
</style>
