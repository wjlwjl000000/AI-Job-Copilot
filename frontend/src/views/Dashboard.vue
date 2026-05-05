<template>
  <div class="dashboard">
    <h1>AI Job Copilot</h1>
    <p class="subtitle">你的智能求职助手</p>
    <div class="stats">
      <div class="stat-card"><div class="num">{{ stats.total }}</div><div class="label">总投递数</div></div>
      <div class="stat-card"><div class="num">{{ stats.screening }}</div><div class="label">初筛中</div></div>
      <div class="stat-card"><div class="num">{{ stats.interview }}</div><div class="label">面试中</div></div>
      <div class="stat-card"><div class="num">{{ stats.offer }}</div><div class="label">已获Offer</div></div>
    </div>
    <h2>快捷操作</h2>
    <div class="actions">
      <router-link to="/resumes" class="action-btn">上传简历</router-link>
      <router-link to="/jobs" class="action-btn">搜索职位</router-link>
      <router-link to="/chat" class="action-btn">智能对话</router-link>
      <router-link to="/interview" class="action-btn">面试备战</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const stats = ref({ total: 0, screening: 0, interview: 0, offer: 0 })
onMounted(async () => { try { stats.value = await api.getStats() } catch (e) {} })
</script>

<style scoped>
.dashboard h1 { font-size: 28px; margin-bottom: 4px; }
.subtitle { color: #666; margin-bottom: 32px; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
.stat-card { background: white; padding: 24px; border-radius: 12px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.stat-card .num { font-size: 32px; font-weight: bold; color: #1976d2; }
.stat-card .label { font-size: 13px; color: #888; margin-top: 4px; }
h2 { font-size: 20px; margin-bottom: 16px; }
.actions { display: flex; gap: 12px; flex-wrap: wrap; }
.action-btn { padding: 12px 24px; background: #1976d2; color: white; text-decoration: none; border-radius: 8px; font-size: 14px; }
.action-btn:hover { background: #1565c0; }
</style>
