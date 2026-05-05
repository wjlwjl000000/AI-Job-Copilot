<template>
  <div class="chat-container">
    <div class="messages" ref="msgContainer">
      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
        <div class="avatar">{{ msg.role === 'user' ? 'U' : 'AI' }}</div>
        <div class="content">{{ msg.content }}</div>
      </div>
      <div v-if="thinking" class="message agent">
        <div class="avatar">AI</div>
        <div class="content thinking">思考中<span class="dots"><span>.</span><span>.</span><span>.</span></span></div>
      </div>
    </div>
    <div v-if="interrupt" class="interrupt-banner">
      <p>{{ interrupt.question }}</p>
      <input v-model="userAnswer" placeholder="请输入..." @keyup.enter="resumeChat" />
      <button @click="resumeChat">确认</button>
    </div>
    <div class="input-area">
      <input v-model="input" @keyup.enter="sendMessage" placeholder="输入消息..." :disabled="thinking" />
      <button @click="sendMessage" :disabled="thinking">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { api } from '../api'
const { sendChatMessage, resumeChat: resumeInterruptedChat } = api

const messages = ref([])
const input = ref('')
const userAnswer = ref('')
const interrupt = ref(null)
const thinking = ref(false)
const msgContainer = ref(null)
let currentTurnId = null

function scrollDown() {
  nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight })
}

async function sendMessage() {
  if (!input.value.trim() || thinking.value) return
  const text = input.value; input.value = ''
  messages.value.push({ role: 'user', content: text })
  thinking.value = true
  scrollDown()

  const response = await sendChatMessage(text, currentTurnId)
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let agentMsg = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n'); buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'chunk') {
          if (!agentMsg) { agentMsg = { role: 'agent', content: '' }; messages.value.push(agentMsg) }
          agentMsg.content += data.content
          currentTurnId = data.turn_id
          scrollDown()
        } else if (data.type === 'done') {
          thinking.value = false
          interrupt.value = null
        } else if (data.question) {
          interrupt.value = data
          thinking.value = false
        }
      } catch (e) { /* skip */ }
    }
  }
  thinking.value = false
}

async function resumeChat() {
  if (!userAnswer.value.trim()) return
  messages.value.push({ role: 'user', content: userAnswer.value })
  const text = userAnswer.value; userAnswer.value = ''
  thinking.value = true
  scrollDown()

  const response = await resumeInterruptedChat(text, currentTurnId)
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let agentMsg = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n'); buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'chunk') {
          if (!agentMsg) { agentMsg = { role: 'agent', content: '' }; messages.value.push(agentMsg) }
          agentMsg.content += data.content
          scrollDown()
        } else if (data.type === 'done') {
          thinking.value = false
          interrupt.value = null
        }
      } catch (e) {}
    }
  }
  thinking.value = false
}
</script>

<style scoped>
.chat-container { display: flex; flex-direction: column; height: 100vh; }
.messages { flex: 1; overflow-y: auto; padding: 16px; }
.message { display: flex; margin: 12px 0; }
.message.user { flex-direction: row-reverse; }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #e0e0e0; font-size: 12px; margin: 0 8px; flex-shrink: 0; }
.content { max-width: 70%; padding: 10px 14px; border-radius: 12px; background: #f0f0f0; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.message.user .content { background: #1976d2; color: white; }
.thinking { color: #999; font-style: italic; }
.thinking .dots span { animation: blink 1.4s infinite; }
.thinking .dots span:nth-child(2) { animation-delay: 0.2s; }
.thinking .dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100% { opacity: 0; } 40% { opacity: 1; } }
.interrupt-banner { background: #fff3e0; padding: 12px 16px; margin: 0 16px; border-radius: 8px; display: flex; align-items: center; gap: 8px; }
.interrupt-banner input { flex: 1; padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; }
.interrupt-banner button { padding: 6px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.input-area { display: flex; padding: 12px 16px; border-top: 1px solid #e0e0e0; background: white; }
.input-area input { flex: 1; padding: 10px 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 14px; }
.input-area input:disabled { background: #f5f5f5; }
.input-area button { margin-left: 8px; padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 8px; cursor: pointer; }
.input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
