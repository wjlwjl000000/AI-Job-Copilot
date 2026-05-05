<template>
  <div class="job-match">
    <h1>Job Matching</h1>
    <div class="add-job">
      <input v-model="title" placeholder="Job title" />
      <input v-model="company" placeholder="Company" />
      <textarea v-model="jd" placeholder="Paste job description here..." rows="4"></textarea>
      <button @click="addJob">Add & Match</button>
      <p v-if="msg">{{ msg }}</p>
    </div>
    <div class="chat-link">
      <h3>Or use Agent Chat for smart matching:</h3>
      <router-link to="/chat" class="btn">Open Agent Chat</router-link>
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
    msg.value = 'Job added! Go to Agent Chat and ask: "match me with this job"'
  } catch(e) { msg.value = 'Failed to add job' }
}
</script>

<style scoped>
.add-job { display: flex; flex-direction: column; gap: 8px; max-width: 500px; margin-bottom: 20px; }
.add-job input, .add-job textarea { padding: 8px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
.add-job button { padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.chat-link { margin-top: 24px; }
.btn { display: inline-block; padding: 10px 20px; background: #2e7d32; color: white; text-decoration: none; border-radius: 6px; }
</style>
