<template>
  <div class="job-match">
    <h1>职位匹配</h1>

    <h2>添加新职位</h2>
    <div class="add-job">
      <input v-model="company" placeholder="公司名称" />
      <input v-model="city" placeholder="城市" />
      <input v-model="salary" placeholder="薪资范围（如 18-30K）" />
      <textarea v-model="jd" placeholder="粘贴职位描述（JD）到这里..." rows="5"></textarea>
      <button @click="addJob" :disabled="!jd.trim()">添加职位</button>
      <p v-if="msg" :class="msgType">{{ msg }}</p>
    </div>

    <h2>已有职位</h2>
    <div v-if="jobs.length === 0" class="empty">暂无职位，请先添加</div>
    <div class="job-list">
      <div v-for="job in jobs" :key="job.id" class="job-card">
        <div class="job-header">
          <strong>{{ job.company || '未知公司' }}</strong>
          <span class="job-city" v-if="job.city">{{ job.city }}</span>
        </div>
        <p class="job-jd">{{ (job.jd_content || '').slice(0, 150) }}</p>
        <div class="job-footer">
          <span class="job-salary" v-if="job.salary_range">{{ job.salary_range }}</span>
          <div class="job-actions">
            <select v-model="selectedResume[job.id]" class="resume-select">
              <option value="">-- 选择简历 --</option>
              <option v-for="r in resumes" :key="r.id" :value="r.id">{{ r.title }}</option>
            </select>
            <button
              class="eval-btn"
              :disabled="!selectedResume[job.id]"
              @click="goEvaluate(job.id)"
            >评估匹配度</button>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-link">
      <h3>或直接在对话中输入 JD：</h3>
      <router-link to="/chat" class="btn">打开智能对话</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const company = ref('')
const city = ref('')
const salary = ref('')
const jd = ref('')
const msg = ref('')
const msgType = ref('')
const jobs = ref([])
const resumes = ref([])
const selectedResume = ref({})

async function fetchJobs() {
  try { jobs.value = await api.listJobs() } catch (e) {}
}

async function fetchResumes() {
  try { resumes.value = await api.listResumes() } catch (e) {}
}

async function addJob() {
  if (!jd.value.trim()) return
  try {
    await api.createJob({
      source: 'manual',
      jd_content: jd.value,
      company: company.value,
      city: city.value,
      salary_range: salary.value,
    })
    msg.value = '职位已添加！'
    msgType.value = 'ok'
    jd.value = ''; company.value = ''; city.value = ''; salary.value = ''
    await fetchJobs()
  } catch (e) {
    msg.value = '添加失败'
    msgType.value = 'err'
  }
}

function goEvaluate(jobId) {
  const resumeId = selectedResume.value[jobId]
  router.push({ path: '/chat', query: { job_id: jobId, resume_id: resumeId } })
}

onMounted(() => {
  fetchJobs()
  fetchResumes()
})
</script>

<style scoped>
.add-job { display: flex; flex-direction: column; gap: 8px; max-width: 500px; margin-bottom: 24px; }
.add-job input, .add-job textarea { padding: 8px 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
.add-job button { padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.add-job button:disabled { background: #90caf9; cursor: not-allowed; }
p.ok { color: #2e7d32; }
p.err { color: #c62828; }

.empty { color: #bbb; font-size: 13px; padding: 16px 0; }

.job-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
.job-card { background: white; padding: 14px 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.job-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.job-city { font-size: 12px; color: #888; background: #f0f0f0; padding: 1px 6px; border-radius: 4px; }
.job-jd { color: #555; font-size: 13px; line-height: 1.5; margin-bottom: 8px; }
.job-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.job-salary { font-size: 13px; color: #1976d2; font-weight: 500; white-space: nowrap; }
.job-actions { display: flex; gap: 8px; align-items: center; }
.resume-select { padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px; background: white; }
.eval-btn { padding: 5px 14px; background: #2e7d32; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; white-space: nowrap; }
.eval-btn:disabled { background: #a5d6a7; cursor: not-allowed; }
.eval-btn:hover:not(:disabled) { background: #1b5e20; }

h2 { font-size: 18px; margin-bottom: 12px; margin-top: 8px; }

.chat-link { margin-top: 16px; }
.btn { display: inline-block; padding: 10px 20px; background: #2e7d32; color: white; text-decoration: none; border-radius: 6px; }
</style>
