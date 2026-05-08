<template>
  <div class="chat-page">
    <!-- Session sidebar -->
    <aside class="session-sidebar">
      <div class="sidebar-header">
        <button class="new-session-btn" @click="handleCreateSession">+ 新建会话</button>
      </div>
      <div class="session-list">
        <div
          v-for="s in store.sessions"
          :key="s.id"
          :class="['session-item', { active: s.id === store.currentId }]"
          @click="handleSwitchSession(s.id)"
        >
          <div class="session-info">
            <span class="session-title">{{ s.title }}</span>
            <span class="session-time">{{ fmtTime(s.updated_at) }}</span>
          </div>
          <button
            class="session-delete"
            @click.stop="handleDeleteSession(s.id)"
            title="删除会话"
          >×</button>
        </div>
        <div v-if="store.sessions.length === 0" class="no-sessions">暂无会话</div>
      </div>
    </aside>

    <!-- Chat main -->
    <div class="chat-main">
      <div class="messages" ref="msgContainer">
        <div
          v-for="msg in store.messages"
          :key="msg.id"
          :class="['message', msg.role, { thinking: msg.thinking, system: msg.role === 'system' }]"
        >
          <div class="avatar">{{ msg.role === 'user' ? 'U' : msg.role === 'system' ? '!' : 'AI' }}</div>
          <div class="content">
            <div v-if="msg.attachment" class="msg-attach">📄 {{ msg.attachment.name }} ({{ msg.attachment.chars }}字)</div>
            {{ msg.content }}
          </div>
        </div>
      </div>

      <!-- File upload queue -->
      <div v-if="store.fileList.length" class="file-queue">
        <div v-for="(f, i) in store.fileList" :key="i" class="file-item">
          <div class="file-icon">
            <span>📄</span>
            <div v-if="f.parsing" class="spinner"></div>
            <span v-else class="check">✓</span>
          </div>
          <div class="file-info">
            <div class="file-name">{{ f.name }}</div>
            <div class="file-status">
              {{ f.parsing ? '解析中...' : `解析完成 (${f.charCount}字)` }}
            </div>
          </div>
          <button class="file-cancel" @click="removeFile(i)" title="移除文件">⊗</button>
        </div>
      </div>

      <div v-if="interrupt" class="interrupt-banner">
        <p>{{ interrupt.question }}</p>
        <input v-model="userAnswer" placeholder="请输入..." @keyup.enter="resumeChat" />
        <button @click="resumeChat">确认</button>
      </div>
      <div class="input-area">
        <button class="upload-btn" @click="$refs.fileUpload.click()" :disabled="thinking" title="上传简历">
          📎
        </button>
        <input type="file" ref="fileUpload" @change="handleFilePicked" accept=".pdf,.docx,.doc,.txt" style="display:none" />
        <input v-model="input" @keyup.enter="sendMessage" placeholder="输入消息..." :disabled="thinking" />
        <button @click="sendMessage" :disabled="thinking || store.fileList.some(f => f.parsing)">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { api } from '../api'
import { useSessionStore } from '../stores/session'

const store = useSessionStore()

const input = ref('')
const userAnswer = ref('')
const interrupt = ref(null)
const thinking = ref(false)
const msgContainer = ref(null)
let localMsgId = 0

function nextMsgId() {
  return 'local-' + (++localMsgId)
}

function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return d.toLocaleDateString()
}

function scrollDown() {
  nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight })
}

// Session actions
async function handleCreateSession() {
  await store.createSession()
}

async function handleSwitchSession(id) {
  if (id === store.currentId || thinking.value) return
  await store.switchSession(id)
  scrollDown()
}

async function handleDeleteSession(id) {
  if (thinking.value) return
  await store.deleteSession(id)
}

// File handling
async function handleFilePicked(e) {
  const file = e.target.files[0]
  if (!file) return
  const idx = store.fileList.length
  store.fileList.push({ name: file.name, parsing: true, charCount: 0, file_id: null })

  const fd = new FormData()
  fd.append('file', file)
  try {
    const data = await api.uploadFile(fd, store.currentId)
    if (data.status === 'ok') {
      store.fileList[idx].file_id = data.file_id
      store.fileList[idx].charCount = data.char_count
      store.fileList[idx].parsing = false
    } else {
      alert('文件解析失败: ' + (data.message || JSON.stringify(data)))
      store.fileList.splice(idx, 1)
    }
  } catch (e) {
    alert('文件上传失败: ' + e.message)
    store.fileList.splice(idx, 1)
  }
  e.target.value = ''
}

async function removeFile(idx) {
  const f = store.fileList[idx]
  if (f && f.file_id) await api.deleteFile(f.file_id, store.currentId)
  store.fileList.splice(idx, 1)
}

// Chat
async function sendMessage() {
  const hasFiles = store.fileList.some(f => !f.parsing)
  if ((!input.value.trim() && !hasFiles) || thinking.value) return
  if (store.fileList.some(f => f.parsing)) return
  if (!store.currentId) return

  const displayText = input.value.trim() || (hasFiles ? '请分析我的简历' : '')
  input.value = ''

  const attachment = hasFiles ? { name: store.fileList.find(f => !f.parsing)?.name, chars: store.fileList.find(f => !f.parsing)?.charCount } : null
  store.addMessage('user', displayText, attachment)
  store.fileList = []

  const thinkingMsg = { role: 'agent', content: '思考中', thinking: true, id: nextMsgId() }
  store.messages.push(thinkingMsg)
  thinking.value = true
  scrollDown()

  const response = await api.sendChatMessage(displayText, store.currentId)
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n'); buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'response') {
          store.messages = store.messages.filter(m => m.id !== thinkingMsg.id)
          store.addMessage('agent', data.content)
          scrollDown()
        } else if (data.type === 'done') {
          store.messages = store.messages.filter(m => m.id !== thinkingMsg.id)
          interrupt.value = null
          store.fetchProfile()
        } else if (data.question) {
          store.messages = store.messages.filter(m => m.id !== thinkingMsg.id)
          interrupt.value = data
        }
      } catch (e) {}
    }
  }
  store.messages = store.messages.filter(m => m.id !== thinkingMsg.id)
  thinking.value = false
  store.fetchProfile()
}

async function resumeChat() {
  if (!userAnswer.value.trim()) return
  store.addMessage('user', userAnswer.value)
  const text = userAnswer.value; userAnswer.value = ''
  scrollDown()

  const thinkingMsg = { role: 'agent', content: '思考中', thinking: true, id: nextMsgId() }
  store.messages.push(thinkingMsg)
  thinking.value = true
  scrollDown()

  const response = await api.resumeChat(text, store.currentId)
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
            store.messages = store.messages.filter(m => m.id !== thinkingMsg.id)
            agentMsg = { role: 'agent', content: '', id: nextMsgId() }
            store.messages.push(agentMsg)
          }
          agentMsg.content += data.content
          scrollDown()
        } else if (data.type === 'done') {
          store.messages = store.messages.filter(m => m.id !== thinkingMsg.id)
          interrupt.value = null
          store.fetchProfile()
        }
      } catch (e) {}
    }
  }
  store.messages = store.messages.filter(m => m.id !== thinkingMsg.id)
  thinking.value = false
  store.fetchProfile()
}

onMounted(async () => {
  await store.fetchSessions()
  scrollDown()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100%;
}

/* Session sidebar */
.session-sidebar {
  width: 260px;
  flex-shrink: 0;
  background: #f7f8fa;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid #e8e8e8;
}

.new-session-btn {
  width: 100%;
  padding: 8px 12px;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.new-session-btn:hover {
  background: #1565c0;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.15s;
}

.session-item:hover {
  background: #e8ecf1;
}

.session-item.active {
  background: #e3f2fd;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  display: block;
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

.session-delete {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: none;
  color: #bbb;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s, background 0.15s;
}

.session-item:hover .session-delete {
  opacity: 1;
}

.session-delete:hover {
  color: white;
  background: #f44336;
}

.no-sessions {
  text-align: center;
  color: #bbb;
  font-size: 13px;
  padding: 24px 0;
}

/* Chat main */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.message {
  display: flex;
  margin: 12px 0;
}

.message.user {
  flex-direction: row-reverse;
}

.message.system .content {
  background: #f5f5f5;
  color: #999;
  font-size: 12px;
  text-align: center;
  border: 1px dashed #e0e0e0;
  max-width: 80%;
  margin: 0 auto;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e0e0e0;
  font-size: 12px;
  margin: 0 8px;
  flex-shrink: 0;
}

.content {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  background: #f0f0f0;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg-attach {
  font-size: 11px;
  color: #888;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e0e0e0;
}

.message.user .msg-attach {
  color: rgba(255,255,255,0.8);
  border-bottom-color: rgba(255,255,255,0.3);
}

.message.user .content {
  background: #1976d2;
  color: white;
}

.message.thinking .content {
  color: #999;
  font-style: italic;
  background: #fafafa;
  border: 1px dashed #e0e0e0;
}

.message.thinking .content::after {
  content: '...';
  animation: thinkDots 1.5s steps(4, end) infinite;
}

@keyframes thinkDots {
  0% { content: '.'; }
  25% { content: '..'; }
  50% { content: '...'; }
  75% { content: '....'; }
}

/* File queue */
.file-queue {
  padding: 8px 16px;
  background: #fafafa;
  border-top: 1px solid #eee;
  flex-shrink: 0;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  max-width: 400px;
}

.file-icon {
  position: relative;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.file-icon .spinner {
  position: absolute;
  inset: 0;
  border: 3px solid #e0e0e0;
  border-top-color: #1976d2;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.file-icon .check {
  position: absolute;
  bottom: -4px;
  right: -4px;
  background: #2e7d32;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.file-info {
  flex: 1;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
}

.file-status {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}

.file-cancel {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid #ccc;
  background: none;
  color: #999;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.file-cancel:hover {
  background: #f44336;
  color: white;
  border-color: #f44336;
}

.interrupt-banner {
  background: #fff3e0;
  padding: 12px 16px;
  margin: 0 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.interrupt-banner input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
}

.interrupt-banner button {
  padding: 6px 16px;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.input-area {
  display: flex;
  padding: 12px 16px;
  border-top: 1px solid #e0e0e0;
  background: white;
  gap: 8px;
}

.upload-btn {
  width: 40px;
  height: 40px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: none;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.upload-btn:hover {
  background: #e3f2fd;
  border-color: #1976d2;
}

.upload-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.input-area input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 14px;
}

.input-area input:disabled {
  background: #f5f5f5;
}

.input-area > button {
  padding: 10px 20px;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.input-area > button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
