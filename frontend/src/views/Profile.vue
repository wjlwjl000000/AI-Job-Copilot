<template>
  <div class="profile">
    <div class="header">
      <h1>求职画像</h1>
      <div class="actions" v-if="store.profile.id">
        <template v-if="editing">
          <button class="btn-cancel" @click="cancelEdit">取消</button>
          <button class="btn-submit" @click="submitEdit">提交</button>
        </template>
        <button class="btn-edit" @click="startEdit" :disabled="editing">编辑</button>
        <button class="btn-delete" @click="showDeleteConfirm = true" :disabled="editing">删除</button>
      </div>
    </div>

    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal">
        <p>此操作会导致后续重构画像，您是否确认删除？</p>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-delete" @click="confirmDelete">确认</button>
        </div>
      </div>
    </div>

    <div v-if="!store.profile.id" class="card empty">
      <p>暂无画像数据</p>
      <p class="hint">在「智能对话」中上传简历并说"帮我构建求职画像"即可自动生成</p>
    </div>

    <template v-else>
      <!-- 姓名 + 联系方式 + 基本信息 + 工作年限（简单字段） -->
      <div class="card"><h3>姓名</h3>
        <input v-if="editing" v-model="editForm.name" /><span v-else>{{ store.profile.name || '--' }}</span></div>

      <div class="card"><h3>联系方式</h3>
        <div class="grid col2">
          <div><label>手机</label><input v-if="editing" v-model="editForm.contact.phone" /><span v-else>{{ store.profile.contact?.phone || '--' }}</span></div>
          <div><label>邮箱</label><input v-if="editing" v-model="editForm.contact.email" /><span v-else>{{ store.profile.contact?.email || '--' }}</span></div>
        </div></div>

      <div class="card"><h3>基本信息</h3>
        <div class="grid">
          <div><label>年龄</label><input v-if="editing" v-model.number="editForm.basic.age" type="number" /><span v-else>{{ store.profile.basic?.age || '--' }}</span></div>
          <div><label>性别</label><input v-if="editing" v-model="editForm.basic.gender" /><span v-else>{{ store.profile.basic?.gender || '--' }}</span></div>
          <div><label>民族</label><input v-if="editing" v-model="editForm.basic.ethnicity" /><span v-else>{{ store.profile.basic?.ethnicity || '--' }}</span></div>
          <div><label>籍贯</label><input v-if="editing" v-model="editForm.basic.hometown" /><span v-else>{{ store.profile.basic?.hometown || '--' }}</span></div>
          <div><label>政治面貌</label><input v-if="editing" v-model="editForm.basic.political" /><span v-else>{{ store.profile.basic?.political || '--' }}</span></div>
        </div></div>

      <div class="card"><h3>工作年限</h3>
        <input v-if="editing" v-model.number="editForm.work_years" type="number" /><span v-else>{{ store.profile.work_years || 0 }} 年</span></div>

      <!-- 教育经历（数组编辑） -->
      <div class="card"><h3>教育经历</h3>
        <template v-if="editing">
          <div v-for="(e, i) in editForm.education" :key="i" class="array-item">
            <div class="array-row"><input v-model="e.degree" placeholder="学位" /><input v-model="e.school" placeholder="学校" /><input v-model="e.major" placeholder="专业" /><input v-model="e.period" placeholder="时间段" /><button class="btn-sm-del" @click="editForm.education.splice(i,1)">×</button></div>
          </div>
          <button class="btn-add" @click="editForm.education.push({degree:'',school:'',major:'',period:''})">+ 添加</button>
        </template>
        <div v-else v-for="(e, i) in store.profile.education" :key="i" class="edu-item">
          <span class="school">{{ e.school }}</span><span class="degree">{{ e.degree }} · {{ e.major }}</span><span class="period" v-if="e.period">{{ e.period }}</span>
        </div>
        <span v-if="!editing && !store.profile.education?.length">--</span>
      </div>

      <!-- 技能（数组编辑） -->
      <div class="card"><h3>技能</h3>
        <template v-if="editing">
          <div v-for="(s, i) in editForm.skills" :key="i" class="array-item">
            <div class="array-row"><input v-model="s.name" placeholder="技能名" /><select v-model="s.level"><option>初级</option><option>中级</option><option>高级</option><option>专家</option></select><input v-model="s.evidence" placeholder="技能证明/项目描述" /><button class="btn-sm-del" @click="editForm.skills.splice(i,1)">×</button></div>
          </div>
          <button class="btn-add" @click="editForm.skills.push({name:'',level:'中级',evidence:''})">+ 添加</button>
        </template>
        <div v-else class="tags">
          <span v-for="(s, i) in store.profile.skills" :key="i" class="tag">{{ s.name }} <em>{{ s.level }}</em><div class="evidence" v-if="s.evidence">{{ s.evidence }}</div></span>
          <span v-if="!store.profile.skills?.length">--</span>
        </div>
      </div>

      <!-- 项目经历（数组编辑） -->
      <div class="card"><h3>项目经历</h3>
        <template v-if="editing">
          <div v-for="(p, i) in editForm.projects" :key="i" class="array-item">
            <div class="array-row"><input v-model="p.name" placeholder="项目名称" /><input v-model="p.role" placeholder="担任角色" /></div>
            <input v-model="p.description" placeholder="项目简介" class="array-full" />
            <textarea v-model="p.content" placeholder="具体项目内容" rows="3" class="array-full"></textarea>
            <div class="array-row"><input v-model="p.techStackText" placeholder="技术栈(逗号分隔)" /><input v-model="p.achievements" placeholder="成果指标" /></div>
            <button class="btn-sm-del" @click="editForm.projects.splice(i,1)">× 删除此项目</button>
          </div>
          <button class="btn-add" @click="editForm.projects.push({name:'',role:'',description:'',content:'',tech_stack:[],techStackText:'',achievements:''})">+ 添加</button>
        </template>
        <div v-else>
          <div v-for="(p, i) in store.profile.projects" :key="i" class="project-item">
            <div class="project-name">{{ p.name }} <span class="role">{{ p.role }}</span></div>
            <p class="desc">{{ p.description }}</p>
            <p class="content" v-if="p.content">{{ p.content }}</p>
            <div class="tech-stack"><span v-for="t in p.tech_stack" :key="t" class="tech-tag">{{ t }}</span></div>
            <p class="achievements" v-if="p.achievements">{{ p.achievements }}</p>
          </div>
          <span v-if="!store.profile.projects?.length">--</span>
        </div>
      </div>

      <!-- 组织/社团经历（数组编辑） -->
      <div class="card"><h3>组织/社团经历</h3>
        <template v-if="editing">
          <div v-for="(o, i) in editForm.organization" :key="i" class="array-item">
            <input v-model="o.name" placeholder="组织名称" class="array-full" />
            <input v-model="o.duties" placeholder="具体工作内容" class="array-full" />
            <input v-model="o.achievements" placeholder="工作成果指标" class="array-full" />
            <button class="btn-sm-del" @click="editForm.organization.splice(i,1)">× 删除</button>
          </div>
          <button class="btn-add" @click="editForm.organization.push({name:'',duties:'',achievements:''})">+ 添加</button>
        </template>
        <div v-else>
          <div v-for="(o, i) in store.profile.organization" :key="i" class="org-item">
            <span class="org-name">{{ o.name }}</span><p class="desc">{{ o.duties }}</p><p class="achievements" v-if="o.achievements">{{ o.achievements }}</p>
          </div>
          <span v-if="!store.profile.organization?.length">--</span>
        </div>
      </div>

      <!-- 求职目标 -->
      <div class="card"><h3>求职目标</h3>
        <div class="grid">
          <div><label>意向岗位</label><input v-if="editing" v-model="editForm.target.rolesText" placeholder="逗号分隔" /><span v-else>{{ (store.profile.target?.roles || []).join('、') || '--' }}</span></div>
          <div><label>意向城市</label><input v-if="editing" v-model="editForm.target.citiesText" placeholder="逗号分隔" /><span v-else>{{ (store.profile.target?.cities || []).join('、') || '--' }}</span></div>
          <div><label>期望薪资</label><input v-if="editing" v-model="editForm.target.salary_range" /><span v-else>{{ store.profile.target?.salary_range || '--' }}</span></div>
          <div><label>意向行业</label><input v-if="editing" v-model="editForm.target.industry" /><span v-else>{{ store.profile.target?.industry || '--' }}</span></div>
        </div></div>

      <!-- 评分 -->
      <div class="card scores" v-if="store.profile.scores"><h3>能力评分</h3>
        <div class="score-bar"><label>竞争力</label><div class="bar"><div class="fill" :style="{width:(store.profile.scores.competitiveness||0)*100+'%'}"></div></div><span>{{ ((store.profile.scores.competitiveness||0)*100).toFixed(0) }}%</span></div>
        <div class="score-bar"><label>市场匹配</label><div class="bar"><div class="fill" :style="{width:(store.profile.scores.market_match||0)*100+'%'}"></div></div><span>{{ ((store.profile.scores.market_match||0)*100).toFixed(0) }}%</span></div>
        <div class="score-bar"><label>资料完整度</label><div class="bar"><div class="fill" :style="{width:(store.profile.scores.completeness||0)*100+'%'}"></div></div><span>{{ ((store.profile.scores.completeness||0)*100).toFixed(0) }}%</span></div>
      </div>

      <div class="card"><h3>个人总结</h3>
        <textarea v-if="editing" v-model="editForm.summary" rows="4" class="array-full"></textarea>
        <p v-else>{{ store.profile.summary || '--' }}</p></div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSessionStore } from '../stores/session'
import { api } from '../api'

const store = useSessionStore()
const editing = ref(false)
const showDeleteConfirm = ref(false)
const editForm = ref({})

onMounted(() => { store.fetchProfile() })

function startEdit() {
  const p = JSON.parse(JSON.stringify(store.profile))
  if (!p.contact) p.contact = { phone: '', email: '' }
  if (!p.basic) p.basic = { age: '', gender: '', ethnicity: '', hometown: '', political: '' }
  if (!p.education) p.education = []
  if (!p.skills) p.skills = []
  if (!p.projects) p.projects = []
  if (!p.organization) p.organization = []
  if (!p.target) p.target = { roles: [], cities: [], salary_range: '', industry: '' }
  p.target.rolesText = (p.target.roles || []).join('、')
  p.target.citiesText = (p.target.cities || []).join('、')
  for (const pr of p.projects) {
    pr.techStackText = (pr.tech_stack || []).join('、')
  }
  editForm.value = p
  editing.value = true
}

function cancelEdit() { editing.value = false }

async function submitEdit() {
  const data = JSON.parse(JSON.stringify(editForm.value))
  // target text → array
  if (data.target) {
    data.target.roles = (data.target.rolesText || '').split(/[,，、]/).map(s => s.trim()).filter(Boolean)
    data.target.cities = (data.target.citiesText || '').split(/[,，、]/).map(s => s.trim()).filter(Boolean)
    delete data.target.rolesText; delete data.target.citiesText
  }
  // projects techStackText → tech_stack
  for (const pr of data.projects || []) {
    pr.tech_stack = (pr.techStackText || '').split(/[,，、]/).map(s => s.trim()).filter(Boolean)
    delete pr.techStackText
  }
  delete data.id
  try {
    const r = await api.updateProfile(data)
    if (r.id) { store.profile = r; editing.value = false }
  } catch (e) {}
}

async function confirmDelete() {
  try { await api.deleteProfile(); store.profile = {}; showDeleteConfirm.value = false } catch (e) {}
}
</script>

<style scoped>
.header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.header h1 { margin: 0; }
.actions { display: flex; gap: 8px; }
.btn-edit, .btn-submit { padding: 6px 16px; background: #1976d2; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-edit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel { padding: 6px 16px; background: #f5f5f5; color: #666; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-delete { padding: 6px 16px; background: #f44336; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-delete:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-add { padding: 4px 12px; background: #e3f2fd; color: #1976d2; border: 1px dashed #1976d2; border-radius: 4px; cursor: pointer; font-size: 12px; margin-top: 8px; }
.btn-sm-del { padding: 2px 8px; background: none; color: #f44336; border: 1px solid #f44336; border-radius: 4px; cursor: pointer; font-size: 12px; }
.card { background: white; padding: 16px; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.card input, .card select { padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.card textarea { padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; resize: vertical; }
.empty { text-align: center; color: #999; }
.hint { font-size: 13px; margin-top: 8px; color: #bbb; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
.grid.col2 { grid-template-columns: 1fr 1fr; }
.grid label { font-size: 12px; color: #999; display: block; }
.grid input, .grid span { width: 100%; }
.array-item { background: #fafafa; padding: 10px; border-radius: 6px; margin-bottom: 8px; border: 1px solid #eee; }
.array-row { display: flex; gap: 8px; margin-bottom: 6px; }
.array-row input, .array-row select { flex: 1; }
.array-full { width: 100%; margin-bottom: 6px; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tag { background: #e3f2fd; padding: 6px 12px; border-radius: 12px; font-size: 13px; }
.tag em { font-style: normal; color: #1976d2; font-size: 11px; margin-left: 4px; }
.evidence { font-size: 11px; color: #888; margin-top: 2px; }
.project-item, .org-item { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.project-item:last-child, .org-item:last-child { border-bottom: none; }
.project-name, .org-name { font-weight: 600; }
.role { color: #1976d2; font-size: 12px; margin-left: 8px; }
.desc { font-size: 13px; color: #666; margin: 4px 0; }
.content { font-size: 13px; color: #444; margin: 4px 0; white-space: pre-wrap; line-height: 1.5; }
.tech-stack { display: flex; gap: 4px; margin-top: 4px; }
.tech-tag { background: #f5f5f5; padding: 2px 8px; border-radius: 4px; font-size: 12px; color: #666; }
.achievements { font-size: 12px; color: #2e7d32; margin-top: 4px; }
.edu-item { padding: 6px 0; display: flex; gap: 12px; align-items: center; font-size: 14px; border-bottom: 1px solid #f8f8f8; }
.edu-item:last-child { border-bottom: none; }
.edu-item .school { font-weight: 600; }
.edu-item .degree { color: #666; }
.edu-item .period { color: #999; font-size: 12px; margin-left: auto; }
.scores { }
.score-bar { display: flex; align-items: center; gap: 10px; margin: 6px 0; }
.score-bar label { width: 70px; font-size: 13px; color: #666; }
.bar { flex: 1; height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden; }
.fill { height: 100%; background: #1976d2; border-radius: 4px; transition: width 0.5s; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: white; padding: 24px; border-radius: 8px; max-width: 400px; text-align: center; }
.modal p { margin-bottom: 20px; font-size: 15px; }
.modal-actions { display: flex; gap: 12px; justify-content: center; }
</style>
