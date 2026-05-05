<template>
  <div class="interview">
    <h1>Interview Preparation</h1>
    <div class="setup">
      <input v-model="jobId" placeholder="Job ID" />
      <button @click="generate">Generate Questions</button>
      <span v-if="generating">Generating...</span>
    </div>
    <div v-if="questions.length" class="questions">
      <div v-for="(q, i) in questions" :key="i" class="q-card">
        <h4>Q{{ i + 1 }}: {{ q.question }}</h4>
        <p class="tip">Focus: {{ q.focus }}</p>
        <textarea v-model="answers[i]" placeholder="Type your answer here..." rows="3"></textarea>
        <button @click="evaluate(i)">Evaluate</button>
        <div v-if="evals[i]" class="eval">{{ evals[i] }}</div>
      </div>
    </div>
    <p v-else class="hint">Enter a Job ID and click Generate. Or go to <router-link to="/chat">Agent Chat</router-link> to prepare interactively.</p>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { api } from '../api'
const jobId = ref('')
const generating = ref(false)
const questions = ref([])
const answers = reactive({})
const evals = reactive({})
async function generate() {
  if (!jobId.value) return
  generating.value = true
  const r = await api.sendChatMessage(`Generate interview questions for job ${jobId.value}`, null)
  const reader = r.body.getReader(), decoder = new TextDecoder(); let buf = ''
  while (true) {
    const { done, value } = await reader.read(); if (done) break
    buf += decoder.decode(value, { stream: true })
    const lines = buf.split('\n'); buf = lines.pop() || ''
    for (const l of lines) {
      if (l.startsWith('data: ')) {
        try { const d = JSON.parse(l.slice(6)); if (d.type === 'response' && d.content) questions.value = extractQuestions(d.content) } catch(e) {}
      }
    }
  }
  generating.value = false
}
function extractQuestions(text) { try { return JSON.parse(text).questions || [] } catch { return [] } }
async function evaluate(i) {
  if (!answers[i]) return
  const r = await api.sendChatMessage(`Evaluate this interview answer for question: "${questions.value[i].question}". My answer: "${answers[i]}"`, null)
  const reader = r.body.getReader(), decoder = new TextDecoder(); let buf = ''
  while (true) {
    const { done, value } = await reader.read(); if (done) break
    buf += decoder.decode(value, { stream: true })
    const lines = buf.split('\n'); buf = lines.pop() || ''
    for (const l of lines) {
      if (l.startsWith('data: ')) {
        try { const d = JSON.parse(l.slice(6)); if (d.type === 'response' && d.content) evals[i] = d.content } catch(e) {}
      }
    }
  }
}
</script>

<style scoped>
.setup { display: flex; gap: 8px; align-items: center; margin-bottom: 20px; }
.setup input { padding: 8px; border: 1px solid #ccc; border-radius: 6px; }
.setup button { padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.q-card { background: white; padding: 14px; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.tip { color: #1976d2; font-size: 13px; margin: 4px 0; }
.q-card textarea { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 6px; margin: 8px 0; }
.q-card button { padding: 6px 14px; background: #2e7d32; color: white; border: none; border-radius: 4px; cursor: pointer; }
.eval { margin-top: 8px; padding: 10px; background: #f5f5f5; border-radius: 6px; font-size: 13px; white-space: pre-wrap; }
.hint { color: #999; margin-top: 40px; }
</style>
