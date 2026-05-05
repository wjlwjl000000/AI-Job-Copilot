<template>
  <div class="chat-container">
    <div class="messages" ref="msgContainer">
      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
        <div class="avatar">{{ msg.role === 'user' ? 'U' : 'AI' }}</div>
        <div class="content">{{ msg.content }}</div>
      </div>
    </div>
    <div v-if="interrupt" class="interrupt-banner">
      <p>{{ interrupt.question }}</p>
      <input v-model="userAnswer" placeholder="请输入..." @keyup.enter="resumeChat" />
      <button @click="resumeChat">确认</button>
    </div>
    <div class="input-area">
      <input v-model="input" @keyup.enter="sendMessage" placeholder="输入消息..." />
      <button @click="sendMessage">发送</button>
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
const msgContainer = ref(null)
let currentTurnId = null

function addMessage(role, content) {
  messages.value.push({ role, content })
  nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight })
}

async function sendMessage() {
  if (!input.value.trim()) return
  const text = input.value; input.value = ''
  addMessage('user', text)

  const response = await sendChatMessage(text, currentTurnId)
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n'); buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'response') {
            addMessage('agent', data.content)
            currentTurnId = data.turn_id
          } else if (data.type === 'done') {
            interrupt.value = null
          } else if (data.question) {
            interrupt.value = data
          }
        } catch (e) { /* skip parse errors */ }
      }
    }
  }
}

async function resumeChat() {
  if (!userAnswer.value.trim()) return
  addMessage('user', userAnswer.value)
  const text = userAnswer.value; userAnswer.value = ''
  const response = await resumeInterruptedChat(text, currentTurnId)
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n'); buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'response') addMessage('agent', data.content)
          else if (data.type === 'done') interrupt.value = null
        } catch (e) {}
      }
    }
  }
}
</script>

<style scoped>
.chat-container { display: flex; flex-direction: column; height: 100vh; max-width: 800px; margin: 0 auto; }
.messages { flex: 1; overflow-y: auto; padding: 16px; }
.message { display: flex; margin: 12px 0; }
.message.user { flex-direction: row-reverse; }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #e0e0e0; font-size: 12px; margin: 0 8px; }
.content { max-width: 70%; padding: 10px 14px; border-radius: 12px; background: #f0f0f0; line-height: 1.5; }
.message.user .content { background: #1976d2; color: white; }
.interrupt-banner { background: #fff3e0; padding: 12px; border-radius: 8px; margin: 8px; }
.interrupt-banner input { width: 60%; padding: 6px; margin-right: 8px; }
.input-area { display: flex; padding: 12px; border-top: 1px solid #e0e0e0; }
.input-area input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 8px; }
.input-area button { margin-left: 8px; padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 8px; cursor: pointer; }
</style>
