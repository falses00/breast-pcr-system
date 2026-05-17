<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { animate, createTimeline, stagger } from 'animejs'
import { api } from '../api/client'
import type { Patient } from '../api/types'
import PageHeader from '../components/PageHeader.vue'
import StatusPill from '../components/StatusPill.vue'
import { currentUserRole, isDoctorRole, roleProfiles } from '../rolePolicy'

const patients = ref<Patient[]>([])
const form = reactive({ patient_code: '', name_masked: '', age: 45, gender: '女', visit_no: '' })
const clinical = reactive({ tumor_type: '浸润性导管癌', er_status: '阳性', pr_status: '阳性', her2_status: '阳性', ki67: 30, treatment_plan: '新辅助治疗方案A' })
const selected = ref<Patient | null>(null)
const keyword = ref('')
const loading = ref(false)
const role = computed(() => currentUserRole())
const canEdit = computed(() => isDoctorRole(role.value))
const roleProfile = computed(() => (role.value ? roleProfiles[role.value] : undefined))
const knownPcr = computed(() => patients.value.filter((p) => p.latest_clinical?.pcr_label !== null && p.latest_clinical?.pcr_label !== undefined))
const pcrPositive = computed(() => knownPcr.value.filter((p) => p.latest_clinical?.pcr_label === true).length)
const pcrRatio = computed(() => (knownPcr.value.length ? Math.round((pcrPositive.value / knownPcr.value.length) * 100) : 0))
const subtypeCount = computed(() => {
  const map = new Map<string, number>()
  patients.value.forEach((p) => {
    const key = p.latest_clinical?.tumor_type || '未知'
    map.set(key, (map.get(key) || 0) + 1)
  })
  return Array.from(map.entries()).sort((a, b) => b[1] - a[1]).slice(0, 4)
})
const selectedClinical = computed(() => selected.value?.latest_clinical)

async function load() {
  loading.value = true
  try {
    patients.value = await api.patients(keyword.value.trim())
    if (!selected.value && patients.value[0]) selected.value = patients.value[0]
    if (selected.value && !patients.value.some((p) => p.id === selected.value?.id)) selected.value = patients.value[0] || null
    if (!patients.value.length) selected.value = null
  } finally {
    loading.value = false
  }
}

async function savePatient() {
  if (!canEdit.value) return ElMessage.warning('当前角色只能查看患者数据')
  const patient = await api.createPatient(form)
  ElMessage.success('患者已创建')
  selected.value = patient
  await load()
}

async function saveClinical() {
  if (!canEdit.value) return ElMessage.warning('当前角色不能录入临床病理信息')
  if (!selected.value) return ElMessage.warning('请选择患者')
  await api.createClinical(selected.value.id, clinical)
  ElMessage.success('临床病理信息已保存')
}

function handleMouseMove(e: MouseEvent) {
  const cards = document.querySelectorAll('.glow-card') as NodeListOf<HTMLElement>
  cards.forEach(card => {
    const rect = card.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    card.style.setProperty('--mouse-x', `${x}px`)
    card.style.setProperty('--mouse-y', `${y}px`)
  })
}

onMounted(async () => {
  await load()
  const tl = createTimeline({ defaults: { ease: 'outCubic', duration: 400 } })
  tl.add('.page-header', { opacity: { from: 0, to: 1 }, y: { from: -12, to: 0 } }, 0)
  tl.add('.data-metric', { opacity: { from: 0, to: 1 }, y: { from: 16, to: 0 }, scale: { from: 0.95, to: 1 }, delay: stagger(60, { from: 'center' }) }, 100)
  tl.add('.role-banner', { opacity: { from: 0, to: 1 }, y: { from: 8, to: 0 } }, 300)
  tl.add('.panel', { opacity: { from: 0, to: 1 }, y: { from: 16, to: 0 }, delay: stagger(80) }, 400)
})
</script>

<template>
  <section class="page" @mousemove="handleMouseMove">
    <!-- 高级动感背景 -->
    <div class="bg-dot-pattern"></div>
    <PageHeader
      eyebrow="PATIENT REGISTRY"
      title="患者与临床病理信息"
      :subtitle="role === '医生' ? '医生维护患者主档、分子分型、治疗方案和pCR标签。' : '科室管理员可查看本科室患者资料，用于审核和质量管理。'"
    />
    <div class="data-strip">
      <div class="data-metric glow-card"><span>真实数据集患者</span><strong>{{ patients.length }}</strong><em>来自本地Excel临床表</em></div>
      <div class="data-metric glow-card"><span>pCR已知样本</span><strong>{{ knownPcr.length }}</strong><em>{{ pcrPositive }} 例达到pCR</em></div>
      <div class="data-metric glow-card"><span>pCR比例</span><strong>{{ pcrRatio }}%</strong><em>仅统计已标注pCR标签</em></div>
      <div class="data-metric glow-card"><span>主要分型</span><strong>{{ subtypeCount[0]?.[0] || '暂无' }}</strong><em>{{ subtypeCount.map(([k, v]) => `${k}${v}`).join(' / ') }}</em></div>
    </div>
    <div class="role-banner">
      <strong>{{ roleProfile?.title }}</strong>
      <span>{{ roleProfile?.limits }}</span>
    </div>
    <div class="grid">
      <div class="panel">
        <h3>患者列表</h3>
        <div class="search-row">
          <el-input v-model="keyword" placeholder="按患者编号、脱敏姓名或门诊号检索" clearable @keyup.enter="load" />
          <el-button type="primary" @click="load">检索</el-button>
        </div>
        <div v-if="!patients.length" class="empty-state">未找到符合条件的患者</div>
        <div v-if="loading" class="empty-state">正在读取真实数据集患者...</div>
        <el-table :data="patients" height="520" highlight-current-row @current-change="(row: Patient) => (selected = row)">
          <el-table-column prop="patient_code" label="患者编号" width="150" />
          <el-table-column prop="name_masked" label="脱敏姓名" />
          <el-table-column prop="age" label="年龄" width="80" />
          <el-table-column label="分子分型" min-width="120">
            <template #default="{ row }">{{ row.latest_clinical?.tumor_type || '未录入' }}</template>
          </el-table-column>
          <el-table-column label="ER/PR/HER2" width="150">
            <template #default="{ row }">{{ row.latest_clinical ? `${row.latest_clinical.er_status}/${row.latest_clinical.pr_status}/${row.latest_clinical.her2_status}` : '未录入' }}</template>
          </el-table-column>
          <el-table-column label="pCR标签" width="100">
            <template #default="{ row }">{{ row.latest_clinical?.pcr_label === true ? '达到' : row.latest_clinical?.pcr_label === false ? '未达到' : '未知' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="{ row }"><StatusPill :value="row.status" /></template>
          </el-table-column>
        </el-table>
      </div>
      <div v-if="canEdit" class="panel">
        <h3>新增患者</h3>
        <el-form label-position="top">
          <el-form-item label="患者编号"><el-input v-model="form.patient_code" placeholder="P-2026-001" /></el-form-item>
          <el-form-item label="脱敏姓名"><el-input v-model="form.name_masked" placeholder="患者001" /></el-form-item>
          <el-form-item label="年龄"><el-input-number v-model="form.age" :min="0" :max="120" /></el-form-item>
          <el-form-item label="性别"><el-select v-model="form.gender" class="full-control"><el-option label="女" value="女" /><el-option label="男" value="男" /></el-select></el-form-item>
          <el-button type="primary" @click="savePatient">保存患者</el-button>
        </el-form>
        <h3>临床病理信息</h3>
        <div v-if="selectedClinical" class="clinical-real">
          <strong>{{ selected?.patient_code }} 当前真实数据</strong>
          <span>分型：{{ selectedClinical.tumor_type }}；Nottingham：{{ selectedClinical.nottingham_grade || '未知' }}</span>
          <span>HR/ER/PR/HER2：{{ selectedClinical.hr_status }}/{{ selectedClinical.er_status }}/{{ selectedClinical.pr_status }}/{{ selectedClinical.her2_status }}</span>
          <span>绝经状态：{{ selectedClinical.menopause || '未知' }}；种族：{{ selectedClinical.ethnicity || '未知' }}</span>
        </div>
        <el-form label-position="top">
          <el-form-item label="当前患者"><el-input :model-value="selected?.patient_code || '未选择'" disabled /></el-form-item>
          <el-form-item label="肿瘤类型"><el-input v-model="clinical.tumor_type" /></el-form-item>
          <el-form-item label="ER / PR / HER2">
            <el-space>
              <el-select v-model="clinical.er_status" class="control-select-sm"><el-option label="阳性" value="阳性" /><el-option label="阴性" value="阴性" /></el-select>
              <el-select v-model="clinical.pr_status" class="control-select-sm"><el-option label="阳性" value="阳性" /><el-option label="阴性" value="阴性" /></el-select>
              <el-select v-model="clinical.her2_status" class="control-select-sm"><el-option label="阳性" value="阳性" /><el-option label="阴性" value="阴性" /></el-select>
            </el-space>
          </el-form-item>
          <el-form-item label="Ki-67"><el-input-number v-model="clinical.ki67" :min="0" :max="100" /></el-form-item>
          <el-button type="primary" @click="saveClinical">保存临床记录</el-button>
        </el-form>
      </div>
      <div v-else class="panel readonly-panel">
        <h3>科室管理员查看区</h3>
        <p>当前角色用于审核和科室数据质量管理，不能直接创建患者、修改临床病理信息或替医生发起录入操作。</p>
        <div class="selected-card">
          <span>当前患者</span>
          <strong>{{ selected?.patient_code || '未选择' }}</strong>
          <p>{{ selected ? `${selected.name_masked} · ${selected.age}岁 · ${selected.status || '待审核'}` : '请在左侧患者列表中选择一条记录。' }}</p>
          <p v-if="selectedClinical">分型：{{ selectedClinical.tumor_type }}；pCR：{{ selectedClinical.pcr_label === true ? '达到' : selectedClinical.pcr_label === false ? '未达到' : '未知' }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: 1.2fr 420px; gap: 16px; }
.search-row { display: grid; grid-template-columns: 1fr 88px; gap: 10px; margin-bottom: 12px; }
.empty-state { margin-bottom: 12px; padding: 12px; border: 1px dashed var(--color-border); border-radius: var(--radius-sm); color: var(--color-muted); background: var(--color-surface-strong); }
.data-strip { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; }
.data-metric { padding: 14px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-glass); backdrop-filter: blur(8px); box-shadow: var(--shadow-sm); }
.data-metric span, .data-metric em { display: block; color: var(--color-muted); font-size: 13px; font-style: normal; }
.data-metric strong { display: block; margin: 6px 0; color: var(--color-foreground); font-size: 20px; font-weight: 700; }
.role-banner, .selected-card, .clinical-real { display: grid; gap: 6px; padding: 12px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-strong); }
.role-banner strong, .selected-card strong, .clinical-real strong { color: var(--color-foreground); }
.role-banner span, .readonly-panel p, .selected-card span, .selected-card p, .clinical-real span { margin: 0; color: var(--color-muted); line-height: 1.6; }
@media (max-width: 1000px) { .grid { grid-template-columns: 1fr; } .data-strip { grid-template-columns: repeat(2, minmax(140px, 1fr)); } }
@media (max-width: 620px) { .data-strip { grid-template-columns: 1fr; } }
</style>
