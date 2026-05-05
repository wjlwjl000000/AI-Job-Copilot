<template>
  <div class="profile">
    <h1>求职画像</h1>
    <div v-if="profile.skill_tags" class="card">
      <h3>技能标签</h3>
      <div class="tags">
        <span v-for="s in profile.skill_tags" :key="s.name" class="tag">{{ s.name }} {{ s.level ? `(${s.level})` : '' }}</span>
      </div>
    </div>
    <div class="grid">
      <div class="card"><h3>工作年限</h3><p>{{ profile.work_years || 0 }} 年</p></div>
      <div class="card"><h3>教育背景</h3><p>{{ profile.education?.school || '暂无' }}</p></div>
    </div>
    <div class="card" v-if="profile.scores">
      <h3>能力评分</h3>
      <p>竞争力：{{ (profile.scores.competitiveness * 100).toFixed(0) }}%</p>
      <p>市场匹配：{{ (profile.scores.market_match * 100).toFixed(0) }}%</p>
      <p>资料完整度：{{ (profile.scores.completeness * 100).toFixed(0) }}%</p>
    </div>
    <div class="upload-section">
      <h3>上传简历</h3>
      <input type="file" ref="fileInput" @change="handleUpload" accept=".pdf,.docx,.doc,.txt" />
      <button @click="$refs.fileInput.click()">选择文件</button>
      <span v-if="uploadMsg">{{ uploadMsg }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const profile = ref({})
const uploadMsg = ref('')
onMounted(async () => { try { const r = await api.getProfile(); if (r && !r.detail) profile.value = r } catch(e) {} })
async function handleUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  const fd = new FormData(); fd.append('file', file)
  const r = await api.uploadResume(fd)
  uploadMsg.value = r.status === 'ok' ? '上传成功！去智能对话中描述你的需求吧。' : '上传失败'
}
</script>

<style scoped>
.card { background: white; padding: 16px; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { background: #e3f2fd; padding: 4px 10px; border-radius: 12px; font-size: 13px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.upload-section { margin-top: 20px; }
.upload-section input[type=file] { display: none; }
.upload-section button { padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
</style>
