<template>
  <div class="apps">
    <h1>Application Tracking</h1>
    <div class="add-form">
      <input v-model="form.job_id" placeholder="Job ID" />
      <input v-model="form.resume_id" placeholder="Resume ID (optional)" />
      <button @click="addApp">Add Application</button>
    </div>
    <div class="kanban">
      <div v-for="col in columns" :key="col.key" class="column">
        <h3>{{ col.label }} <span class="count">{{ apps.filter(a => a.status === col.key).length }}</span></h3>
        <div v-for="app in apps.filter(a => a.status === col.key)" :key="app.id" class="card">
          <p><strong>Job:</strong> {{ app.job_id }}</p>
          <p class="notes">{{ app.notes || 'No notes' }}</p>
          <select :value="app.status" @change="move(app.id, $event.target.value)">
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
const form = reactive({ job_id: '', resume_id: '' })
const columns = [
  { key: 'planned', label: 'Planned' },
  { key: 'applied', label: 'Applied' },
  { key: 'screening', label: 'Screening' },
  { key: 'interview', label: 'Interview' },
  { key: 'offer', label: 'Offer' },
  { key: 'rejected', label: 'Rejected' },
]
onMounted(async () => { try { apps.value = await api.listApplications() } catch(e) {} })
async function addApp() {
  if (!form.job_id) return
  await api.createApplication({ job_id: form.job_id, resume_id: form.resume_id || null })
  apps.value = await api.listApplications()
  form.job_id = ''; form.resume_id = ''
}
async function move(id, status) {
  await api.updateApplication(id, { status })
  apps.value = await api.listApplications()
}
</script>

<style scoped>
.add-form { display: flex; gap: 8px; margin-bottom: 20px; }
.add-form input { padding: 8px; border: 1px solid #ccc; border-radius: 6px; }
.add-form button { padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.kanban { display: flex; gap: 12px; overflow-x: auto; }
.column { min-width: 180px; background: #f0f0f0; border-radius: 8px; padding: 12px; }
.column h3 { font-size: 14px; margin-bottom: 8px; }
.count { background: #1976d2; color: white; border-radius: 10px; padding: 1px 7px; font-size: 11px; margin-left: 4px; }
.card { background: white; padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 13px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.card select { margin-top: 4px; width: 100%; padding: 4px; font-size: 12px; border-radius: 4px; border: 1px solid #ccc; }
.notes { color: #888; font-size: 12px; margin: 4px 0; }
</style>
