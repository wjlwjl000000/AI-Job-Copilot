<template>
  <div class="job-match">
    <h1>职位匹配</h1>
    <div class="add-job">
      <input v-model="title" placeholder="岗位名称" />
      <input v-model="company" placeholder="公司名称" />
      <textarea v-model="jd" placeholder="粘贴职位描述（JD）到这里..." rows="4"></textarea>
      <button @click="addJob">添加并匹配</button>
      <p v-if="msg">{{ msg }}</p>
    </div>
    <div class="chat-link">
      <h3>或使用智能对话进行精准匹配：</h3>
      <router-link to="/chat" class="btn">打开智能对话</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../api'
const title = ref(''), company = ref(''), jd = ref(''), msg = ref('')
async function addJob() {
  if (!jd.value.trim()) return
  try {
    await api.createJob({ source: 'manual', jd_content: jd.value, company: company.value, title: title.value })
    msg.value = '职位已添加！去智能对话中说"帮我分析这个岗位的匹配度"即可。'
  } catch(e) { msg.value = '添加失败' }
}
</script>

<style scoped>
.add-job { display: flex; flex-direction: column; gap: 8px; max-width: 500px; margin-bottom: 20px; }
.add-job input, .add-job textarea { padding: 8px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
.add-job button { padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.chat-link { margin-top: 24px; }
.btn { display: inline-block; padding: 10px 20px; background: #2e7d32; color: white; text-decoration: none; border-radius: 6px; }
</style>
