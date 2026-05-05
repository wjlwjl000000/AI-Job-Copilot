<template>
  <div class="interview">
    <h1>面试备战</h1>
    <div class="setup">
      <input v-model="jobId" placeholder="输入职位ID" />
      <button @click="generate">生成面试题</button>
      <span v-if="generating">生成中...</span>
    </div>
    <div v-if="questions.length" class="questions">
      <div v-for="(q, i) in questions" :key="i" class="q-card">
        <h4>第{{ i + 1 }}题：{{ q.question }}</h4>
        <p class="tip">考察点：{{ q.focus }}</p>
        <textarea v-model="answers[i]" placeholder="在这里输入你的回答..." rows="3"></textarea>
        <button @click="evaluate(i)">提交评估</button>
        <div v-if="evals[i]" class="eval">{{ evals[i] }}</div>
      </div>
    </div>
    <p v-else class="hint">输入职位ID并点击生成面试题，或前往 <router-link to="/chat">智能对话</router-link> 进行交互式面试准备。</p>
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
  const r = await api.sendChatMessage(`为职位 ${jobId.value} 生成面试题`, null)
  const reader = r.body.getReader(), decoder = new TextDecoder(); let buf = ''
  while (true) {
    const { done, value } = await reader.read(); if (done) break
    buf += decoder.decode(value, { stream: true })
    const lines = buf.split('\n'); buf = lines.pop() || ''
    for (const l of lines) {
      if (l.startsWith('data: ')) {
        try { const d = JSON.parse(l.slice(6)); if (d.type === 'chunk') {} else if (d.type === 'done') { generating.value = false } } catch(e) {}
      }
    }
  }
}
function extractQuestions(text) { try { return JSON.parse(text).questions || [] } catch { return [] } }
async function evaluate(i) {
  if (!answers[i]) return
  const r = await api.sendChatMessage(`请评估这道面试题的回答。题目："${questions.value[i].question}"，我的回答："${answers[i]}"`, null)
  const reader = r.body.getReader(), decoder = new TextDecoder(); let buf = ''
  while (true) {
    const { done, value } = await reader.read(); if (done) break
    buf += decoder.decode(value, { stream: true })
    const lines = buf.split('\n'); buf = lines.pop() || ''
    for (const l of lines) {
      if (l.startsWith('data: ')) {
        try { const d = JSON.parse(l.slice(6)); if (d.type === 'chunk') { evals[i] = (evals[i] || '') + d.content } } catch(e) {}
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
