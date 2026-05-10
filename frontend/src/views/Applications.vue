<template>
  <div class="apps">
    <h1>投递追踪</h1>

    <div class="add-form">
      <select v-model="form.job_id">
        <option value="">-- 选择职位 --</option>
        <option v-for="j in jobs" :key="j.id" :value="j.id">{{ j.company }} - {{ j.jd_content?.slice(0, 40) }}</option>
      </select>
      <select v-model="form.resume_id">
        <option value="">-- 选择简历（可选）--</option>
        <option v-for="r in resumes" :key="r.id" :value="r.id">{{ r.title }}</option>
      </select>
      <button @click="addApp" :disabled="!form.job_id || adding">添加投递</button>
    </div>

    <div class="kanban">
      <div v-for="col in columns" :key="col.key" class="column">
        <h3>{{ col.label }} <span class="count">{{ apps.filter(a => a.status === col.key).length }}</span></h3>
        <div v-if="apps.filter(a => a.status === col.key).length === 0" class="empty-col">暂无</div>
        <div v-for="app in apps.filter(a => a.status === col.key)" :key="app.id" class="card">
          <p class="company">{{ app.company || '未知公司' }}</p>
          <p class="jd-snippet">{{ (app.jd_content || '暂无职位描述').slice(0, 60) }}</p>
          <p class="time" v-if="app.timeline?.length">{{ lastTime(app.timeline) }}</p>
          <select
            :value="app.status"
            :disabled="moving === app.id"
            @change="move(app.id, $event.target.value)"
          >
            <option v-for="c in columns" :key="c.key" :value="c.key">{{ c.label }}</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { api } from '../api'

const apps = ref([])
const jobs = ref([])
const resumes = ref([])
const adding = ref(false)
const moving = ref(null)
const form = reactive({ job_id: '', resume_id: '' })

const columns = [
  { key: 'planned', label: '待投递' },
  { key: 'applied', label: '已投递' },
  { key: 'screening', label: '初筛中' },
  { key: 'interview', label: '面试中' },
  { key: 'offer', label: '已获Offer' },
  { key: 'rejected', label: '已拒绝' },
]

function lastTime(timeline) {
  const last = timeline[timeline.length - 1]
  if (!last?.time) return ''
  const d = new Date(last.time)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(async () => {
  try { apps.value = await api.listApplications() } catch (e) {}
  try { jobs.value = await api.listJobs() } catch (e) {}
  try { resumes.value = await api.listResumes() } catch (e) {}
})

async function addApp() {
  if (!form.job_id) return
  adding.value = true
  try {
    await api.createApplication({ job_id: form.job_id, resume_id: form.resume_id || null })
    apps.value = await api.listApplications()
    form.job_id = ''
    form.resume_id = ''
  } catch (e) {}
  adding.value = false
}

async function move(id, status) {
  moving.value = id
  try {
    await api.updateApplication(id, { status })
    apps.value = await api.listApplications()
  } catch (e) {}
  moving.value = null
}
</script>

<style scoped>
.add-form { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.add-form select { padding: 8px; border: 1px solid #ccc; border-radius: 6px; min-width: 200px; background: white; }
.add-form button { padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.add-form button:disabled { background: #90caf9; cursor: not-allowed; }
.kanban { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 16px; }
.column { min-width: 200px; max-width: 240px; background: #f0f0f0; border-radius: 8px; padding: 12px; }
.column h3 { font-size: 14px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
.count { background: #1976d2; color: white; border-radius: 10px; padding: 1px 8px; font-size: 12px; }
.empty-col { color: #bbb; font-size: 12px; text-align: center; padding: 16px 0; }
.card { background: white; padding: 12px; border-radius: 6px; margin-bottom: 8px; font-size: 13px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card .company { font-weight: 600; color: #333; margin-bottom: 4px; }
.card .jd-snippet { color: #666; font-size: 12px; margin-bottom: 4px; line-height: 1.4; }
.card .time { color: #999; font-size: 11px; margin-bottom: 4px; }
.card select { margin-top: 4px; width: 100%; padding: 4px 6px; font-size: 12px; border-radius: 4px; border: 1px solid #ddd; background: white; }
</style>
