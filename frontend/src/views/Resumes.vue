<template>
  <div class="resumes">
    <div class="header">
      <h1>简历管理</h1>
      <button class="btn-refresh" @click="load">刷新</button>
    </div>

    <div v-if="resumes.length" class="list">
      <div v-for="r in resumes" :key="r.id" class="card">
        <div class="info">
          <div class="title-row">
            <strong>{{ r.title || '未命名' }}</strong>
            <span v-if="r.base_version" class="badge">基础版</span>
            <span class="chars">{{ r.char_count || 0 }} 字</span>
          </div>
          <div v-if="expanded === r.id" class="raw-text">{{ rawText }}</div>
        </div>
        <div class="actions">
          <button class="btn-view" @click="toggleView(r)">{{ expanded === r.id ? '收起' : '查看原文' }}</button>
          <a v-if="r.file_path" class="btn-download" :href="'http://localhost:8080/api/resumes/' + r.id + '/file'" target="_blank">打开附件</a>
          <button class="btn-del" @click="remove(r.id)">删除</button>
        </div>
      </div>
    </div>
    <p v-else class="empty">暂无简历。在「智能对话」中上传简历并构建画像后自动存入。</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const resumes = ref([])
const expanded = ref(null)
const rawText = ref('')

onMounted(load)

async function load() {
  try { resumes.value = await api.listResumes() } catch (e) {}
}

async function toggleView(r) {
  if (expanded.value === r.id) {
    expanded.value = null
    rawText.value = ''
  } else {
    try {
      const data = await api.getResume(r.id)
      rawText.value = data.raw_text || '(无内容)'
      expanded.value = r.id
    } catch (e) {
      rawText.value = '(加载失败)'
    }
  }
}

async function remove(id) {
  if (!confirm('确定删除该简历？')) return
  try {
    await api.deleteResume(id)
    expanded.value = null
    await load()
  } catch (e) {}
}
</script>

<style scoped>
.header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.header h1 { margin: 0; }
.btn-refresh { padding: 6px 14px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.list { display: flex; flex-direction: column; gap: 10px; }
.card { background: white; padding: 14px 16px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.badge { background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
.chars { color: #999; font-size: 12px; }
.raw-text { background: #fafafa; border: 1px solid #eee; border-radius: 6px; padding: 12px; margin: 8px 0; font-size: 13px; line-height: 1.8; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
.actions { display: flex; gap: 8px; margin-top: 6px; }
.btn-view, .btn-download { padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; background: #f5f5f5; color: #1976d2; border: 1px solid #ddd; text-decoration: none; }
.btn-view:hover, .btn-download:hover { background: #e3f2fd; }
.btn-del { padding: 4px 12px; background: #ef5350; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.btn-del:hover { background: #c62828; }
.empty { color: #999; text-align: center; padding: 40px 0; }
</style>
