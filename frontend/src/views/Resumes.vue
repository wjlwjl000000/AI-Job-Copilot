<template>
  <div class="resumes">
    <h1>My Resumes</h1>
    <div class="upload-area">
      <input type="file" ref="fileInput" @change="handleUpload" accept=".pdf,.docx,.doc,.txt" />
      <button @click="$refs.fileInput.click()">Upload New Resume</button>
      <span v-if="msg">{{ msg }}</span>
    </div>
    <div v-if="resumes.length" class="list">
      <div v-for="r in resumes" :key="r.id" class="card">
        <div class="info">
          <strong>{{ r.title || 'Untitled' }}</strong>
          <span v-if="r.target_role">Target: {{ r.target_role }}</span>
          <span v-if="r.base_version" class="badge">Base</span>
        </div>
        <button class="del" @click="remove(r.id)">Delete</button>
      </div>
    </div>
    <p v-else class="empty">No resumes yet. Upload one to get started.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const resumes = ref([])
const msg = ref('')
onMounted(async () => { try { resumes.value = await api.listResumes() } catch(e) {} })
async function handleUpload(e) {
  const file = e.target.files[0]; if (!file) return
  const fd = new FormData(); fd.append('file', file)
  const r = await api.uploadResume(fd)
  msg.value = r.status === 'ok' ? 'Uploaded!' : 'Failed'
  if (r.status === 'ok') { resumes.value = await api.listResumes() }
}
async function remove(id) { await api.deleteResume(id); resumes.value = await api.listResumes() }
</script>

<style scoped>
.upload-area { margin-bottom: 24px; }
.upload-area input[type=file] { display: none; }
.upload-area button { padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.list { display: flex; flex-direction: column; gap: 8px; }
.card { background: white; padding: 14px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.info { display: flex; gap: 12px; align-items: center; }
.badge { background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
.del { padding: 4px 12px; background: #ef5350; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.empty { color: #999; }
</style>
