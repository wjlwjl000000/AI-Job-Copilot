<template>
  <div class="registry">
    <h1>Agent Registry</h1>
    <div class="add-form">
      <input v-model="newUrl" placeholder="Agent URL (e.g. http://localhost:8001)" />
      <button @click="register">Register</button>
      <span v-if="regMsg">{{ regMsg }}</span>
    </div>
    <div class="list">
      <div v-for="a in agents" :key="a.name" class="card">
        <div class="info">
          <strong>{{ a.name }}</strong>
          <span class="sys" v-if="isSystem(a.name)">System</span>
          <span class="desc" v-if="a.card?.description">{{ a.card.description?.substring(0, 80) }}</span>
        </div>
        <button v-if="!isSystem(a.name)" @click="remove(a.name)" class="del">Remove</button>
        <span v-else class="locked">Locked</span>
      </div>
    </div>
    <p v-if="!agents.length" class="empty">No agents registered. Add one to get started.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const agents = ref([])
const newUrl = ref('')
const regMsg = ref('')
const SYS = ['profile-agent','matching-agent','interview-agent','support-agent']
function isSystem(n) { return SYS.includes(n) }
onMounted(async () => { await refresh() })
async function refresh() { try { agents.value = await api.listAgents() } catch(e) {} }
async function register() {
  if (!newUrl.value) return
  const r = await api.registerAgent(newUrl.value)
  regMsg.value = r.status === 'registered' ? `Registered: ${r.name}` : r.message || 'Failed'
  newUrl.value = ''
  await refresh()
}
async function remove(name) { await api.deleteAgent(name); await refresh() }
</script>

<style scoped>
.add-form { display: flex; gap: 8px; align-items: center; margin-bottom: 20px; }
.add-form input { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 6px; max-width: 400px; }
.add-form button { padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; }
.list { display: flex; flex-direction: column; gap: 8px; }
.card { background: white; padding: 14px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.info { display: flex; flex-direction: column; gap: 2px; }
.sys { background: #fff3e0; padding: 1px 6px; border-radius: 8px; font-size: 11px; color: #e65100; display: inline-block; width: fit-content; }
.desc { font-size: 12px; color: #888; }
.del { padding: 6px 12px; background: #ef5350; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.locked { color: #999; font-size: 12px; }
.empty { color: #999; }
</style>
