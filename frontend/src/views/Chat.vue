<template>
  <div class="chat-container">
    <div class="messages" ref="msgContainer">
      <div v-for="msg in messages" :key="msg.id" v-memo="[msg.id]" :class="['message', msg.role, { thinking: msg.thinking }]">
        <div class="avatar">{{ msg.role === 'user' ? 'U' : 'AI' }}</div>
        <div class="content">
          <div v-if="msg.attachment" class="msg-attach">📄 {{ msg.attachment.name }} ({{ msg.attachment.chars }}字)</div>
          {{ msg.content }}
        </div>
      </div>
    </div>

    <!-- File upload queue -->
    <div v-if="fileQueue" class="file-queue">
      <div class="file-item">
        <div class="file-icon">
          <span>📄</span>
          <div v-if="fileQueue.parsing" class="spinner"></div>
          <span v-else class="check">✓</span>
        </div>
        <div class="file-info">
          <div class="file-name">{{ fileQueue.name }}</div>
          <div class="file-status">
            {{ fileQueue.parsing ? '解析中...' : `解析完成 (${fileQueue.charCount}字)` }}
          </div>
        </div>
        <button class="file-cancel" @click="clearFile" title="取消上传">⊗</button>
      </div>
    </div>

    <div v-if="interrupt" class="interrupt-banner">
      <p>{{ interrupt.question }}</p>
      <input v-model="userAnswer" placeholder="请输入..." @keyup.enter="resumeChat" />
      <button @click="resumeChat">确认</button>
    </div>
    <div class="input-area">
      <button class="upload-btn" @click="$refs.fileUpload.click()" :disabled="thinking || !!fileQueue" title="上传简历">
        📎
      </button>
      <input type="file" ref="fileUpload" @change="handleFilePicked" accept=".pdf,.docx,.doc,.txt" style="display:none" />
      <input v-model="input" @keyup.enter="sendMessage" placeholder="输入消息..." :disabled="thinking" />
      <button @click="sendMessage" :disabled="thinking || (fileQueue && fileQueue.parsing)">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick } from 'vue'
import { api } from '../api'
const { sendChatMessage, resumeChat: resumeInterruptedChat } = api

const messages = ref([])
const input = ref('')
const userAnswer = ref('')
const interrupt = ref(null)
const thinking = ref(false)
const msgContainer = ref(null)
const fileQueue = ref(null)
let currentTurnId = null
let msgIdCounter = 0
const MAX_MESSAGES = 200
const TRIM_COUNT = 50

function addMessage(role, content, attachment = null) {
  messages.value.push({ role, content, attachment, id: ++msgIdCounter })
  if (messages.value.length > MAX_MESSAGES) {
    const trimmed = messages.value.splice(0, TRIM_COUNT)
    // 查找并移除旧的归档提示
    const archiveIdx = messages.value.findIndex(m => m.id === 'archive')
    if (archiveIdx >= 0) messages.value.splice(archiveIdx, 1)
    messages.value.unshift({
      role: 'system', content: `[... 已自动归档 ${trimmed.length} 条更早的消息 ...]`,
      archived: true, id: 'archive',
    })
  }
}

function scrollDown() {
  nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight })
}

async function handleFilePicked(e) {
  const file = e.target.files[0]
  if (!file) return
  fileQueue.value = { name: file.name, parsing: true, charCount: 0, text: '' }

  const fd = new FormData()
  fd.append('file', file)
  try {
    const r = await fetch('http://localhost:8080/api/agent/parse-file', { method: 'POST', body: fd })
    const data = await r.json()
    if (data.status === 'ok') {
      fileQueue.value.parsing = false
      fileQueue.value.text = data.text
      fileQueue.value.charCount = data.text.length
    } else {
      fileQueue.value = null
    }
  } catch (e) {
    fileQueue.value = null
  }
}

function clearFile() {
  fileQueue.value = null
}

async function sendMessage() {
  if ((!input.value.trim() && !fileQueue.value) || thinking.value) return
  if (fileQueue.value && fileQueue.value.parsing) return

  const displayText = input.value.trim() || (fileQueue.value ? '请分析我的简历' : '')
  input.value = ''

  const attachment = fileQueue.value
    ? { name: fileQueue.value.name, chars: fileQueue.value.charCount }
    : null

  // Display shows user's original input; send includes parsed resume text
  const sendText = fileQueue.value?.text
    ? `${displayText}\n\n[附件简历内容]:\n${fileQueue.value.text}`
    : displayText

  addMessage('user', displayText, attachment)
  fileQueue.value = null  // 立即清除附件队列

  const thinkingMsg = { role: 'agent', content: '思考中', thinking: true, id: ++msgIdCounter }
  messages.value.push(thinkingMsg)
  scrollDown()

  const response = await sendChatMessage(sendText, currentTurnId)
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
          if (!agentMsg) {
            // 收到第一个chunk时移除思考气泡，创建回复气泡
            messages.value = messages.value.filter(m => m.id !== thinkingMsg.id)
            agentMsg = { role: 'agent', content: '', id: ++msgIdCounter }
            messages.value.push(agentMsg)
          }
          agentMsg.content += data.content
          currentTurnId = data.turn_id
          scrollDown()
        } else if (data.type === 'done') {
          messages.value = messages.value.filter(m => m.id !== thinkingMsg.id)
          interrupt.value = null
        } else if (data.question) {
          messages.value = messages.value.filter(m => m.id !== thinkingMsg.id)
          interrupt.value = data
        }
      } catch (e) {}
    }
  }
  messages.value = messages.value.filter(m => m.id !== thinkingMsg.id)
}

async function resumeChat() {
  if (!userAnswer.value.trim()) return
  addMessage('user', userAnswer.value)
  const text = userAnswer.value; userAnswer.value = ''
  scrollDown()

  const thinkingMsg = { role: 'agent', content: '思考中', thinking: true, id: ++msgIdCounter }
  messages.value.push(thinkingMsg)
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
          if (!agentMsg) {
            messages.value = messages.value.filter(m => m.id !== thinkingMsg.id)
            agentMsg = { role: 'agent', content: '', id: ++msgIdCounter }
            messages.value.push(agentMsg)
          }
          agentMsg.content += data.content
          scrollDown()
        } else if (data.type === 'done') {
          messages.value = messages.value.filter(m => m.id !== thinkingMsg.id)
          interrupt.value = null
        }
      } catch (e) {}
    }
  }
  messages.value = messages.value.filter(m => m.id !== thinkingMsg.id)
}
</script>

<style scoped>
.chat-container { display: flex; flex-direction: column; height: 100%; }
.messages { flex: 1; overflow-y: auto; padding: 16px; }
.message.system .content { background: #f5f5f5; color: #999; font-size: 12px; text-align: center; border: 1px dashed #e0e0e0; max-width: 80%; margin: 0 auto; }
.message { display: flex; margin: 12px 0; }
.message.user { flex-direction: row-reverse; }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #e0e0e0; font-size: 12px; margin: 0 8px; flex-shrink: 0; }
.content { max-width: 70%; padding: 10px 14px; border-radius: 12px; background: #f0f0f0; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.msg-attach { font-size: 11px; color: #888; margin-bottom: 6px; display: flex; align-items: center; gap: 4px; padding-bottom: 6px; border-bottom: 1px solid #e0e0e0; }
.message.user .msg-attach { color: rgba(255,255,255,0.8); border-bottom-color: rgba(255,255,255,0.3); }
.message.user .content { background: #1976d2; color: white; }
.message.thinking .content { color: #999; font-style: italic; background: #fafafa; border: 1px dashed #e0e0e0; }
.message.thinking .content::after { content: '...'; animation: thinkDots 1.5s steps(4, end) infinite; }
@keyframes thinkDots { 0% { content: '.'; } 25% { content: '..'; } 50% { content: '...'; } 75% { content: '....'; } }

/* File queue */
.file-queue { padding: 8px 16px; background: #fafafa; border-top: 1px solid #eee; flex-shrink: 0; }
.file-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: white; border: 1px solid #e0e0e0; border-radius: 8px; max-width: 400px; }
.file-icon { position: relative; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.file-icon .spinner { position: absolute; inset: 0; border: 3px solid #e0e0e0; border-top-color: #1976d2; border-radius: 50%; animation: spin 0.8s linear infinite; }
.file-icon .check { position: absolute; bottom: -4px; right: -4px; background: #2e7d32; color: white; border-radius: 50%; width: 16px; height: 16px; font-size: 10px; display: flex; align-items: center; justify-content: center; }
@keyframes spin { to { transform: rotate(360deg); } }
.file-info { flex: 1; }
.file-name { font-size: 13px; font-weight: 500; }
.file-status { font-size: 12px; color: #888; margin-top: 2px; }
.file-cancel { width: 24px; height: 24px; border-radius: 50%; border: 1px solid #ccc; background: none; color: #999; font-size: 14px; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0; }
.file-cancel:hover { background: #f44336; color: white; border-color: #f44336; }

.interrupt-banner { background: #fff3e0; padding: 12px 16px; margin: 0 16px; border-radius: 8px; display: flex; align-items: center; gap: 8px; }
.interrupt-banner input { flex: 1; padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; }
.interrupt-banner button { padding: 6px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.input-area { display: flex; padding: 12px 16px; border-top: 1px solid #e0e0e0; background: white; gap: 8px; }
.upload-btn { width: 40px; height: 40px; border: 1px solid #ccc; border-radius: 8px; background: none; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.upload-btn:hover { background: #e3f2fd; border-color: #1976d2; }
.upload-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.input-area input { flex: 1; padding: 10px 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 14px; }
.input-area input:disabled { background: #f5f5f5; }
.input-area > button { padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 8px; cursor: pointer; }
.input-area > button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
