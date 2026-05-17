<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { animate, createTimeline, stagger } from 'animejs'
import { HeatmapChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { getInstanceByDom, init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { api } from '../api/client'
import type { AnalysisTask, FeatureImportance, ImageRecord, ModelMetric, Patient } from '../api/types'
import PageHeader from '../components/PageHeader.vue'
import MetricCard from '../components/MetricCard.vue'
import CountUp from '../components/CountUp.vue'
import StatusPill from '../components/StatusPill.vue'
import AnalysisDetailDialog from '../components/AnalysisDetailDialog.vue'
import { currentUserRole, isDoctorRole, roleProfiles } from '../rolePolicy'

use([HeatmapChart, LineChart, GridComponent, TooltipComponent, VisualMapComponent, CanvasRenderer])

const patients = ref<Patient[]>([])
const images = ref<ImageRecord[]>([])
const tasks = ref<AnalysisTask[]>([])
const metrics = ref<ModelMetric[]>([])
const featureImp = ref<FeatureImportance[]>([])
const patientId = ref<number>()
const imageId = ref<number>()
const activeTab = ref('metrics')
const detailTaskId = ref<number | null>(null)
const showDetail = ref(false)

const role = computed(() => currentUserRole())
const canCreate = computed(() => isDoctorRole(role.value))
const roleProfile = computed(() => (role.value ? roleProfiles[role.value] : undefined))
const knownPcrCount = computed(() => patients.value.filter(p => p.latest_clinical?.pcr_label != null).length)
const localMetrics = computed(() => metrics.value.filter(m => (m.data_source || '').includes('local')))

const confusionEl = ref<HTMLDivElement>()
const importanceEl = ref<HTMLDivElement>()

async function load() {
  patients.value = await api.patients()
  tasks.value = await api.analysisTasks()
  metrics.value = await api.modelMetrics()
  try { featureImp.value = await api.featureImportance() } catch { /* 模型文件可能不存在 */ }
  if (!patientId.value && patients.value[0]) { patientId.value = patients.value[0].id; await loadImages() }
}

async function loadImages() {
  images.value = await api.images(patientId.value)
  if (!imageId.value || !images.value.some(i => i.id === imageId.value)) imageId.value = images.value[0]?.id
}

async function createTask() {
  if (!canCreate.value) return ElMessage.warning('当前角色只能查看分析结果和统计指标')
  if (!patientId.value) return ElMessage.warning('请选择患者')
  const task = await api.createAnalysis({ patient_id: patientId.value, image_id: imageId.value, task_type: '规则pCR辅助分析' })
  tasks.value.unshift(task)
  ElMessage.success(`分析完成 · ${task.risk_level || '中等'} · ${task.molecular_subtype || ''}`)
}

async function exportReport(task: AnalysisTask) {
  await api.downloadReport(task.id); ElMessage.success('报告导出请求已完成')
}

function openDetail(task: AnalysisTask) { detailTaskId.value = task.id; showDetail.value = true }

function renderConfusionMatrix(metric: ModelMetric) {
  if (!confusionEl.value || !metric.confusion_matrix?.length) return
  const cm = metric.confusion_matrix
  const labels = ['non-pCR', 'pCR']
  const data: [number, number, number][] = []
  for (let i = 0; i < cm.length; i++) for (let j = 0; j < cm[i].length; j++) data.push([j, i, cm[i][j]])
  const chart = getInstanceByDom(confusionEl.value) || init(confusionEl.value)
  chart.setOption({
    tooltip: { backgroundColor: 'rgba(15,23,42,0.85)', borderColor: 'transparent', textStyle: { color: '#e2e8f0' } },
    xAxis: { type: 'category', data: labels, position: 'top', axisLabel: { color: '#64748b' } },
    yAxis: { type: 'category', data: labels, axisLabel: { color: '#64748b' } },
    visualMap: { min: 0, max: Math.max(...cm.flat(), 1), inRange: { color: ['#eff6ff', '#3b82f6', '#1e3a8a'] }, show: false },
    series: [{ type: 'heatmap', data, label: { show: true, color: '#fff', fontSize: 16, fontWeight: 700 }, itemStyle: { borderRadius: 4 } }],
    grid: { left: 60, right: 20, top: 40, bottom: 20 },
  })
  chart.resize()
}

function renderFeatureImportance() {
  if (!importanceEl.value || !featureImp.value.length) return
  const fi = featureImp.value[0]
  const chart = getInstanceByDom(importanceEl.value) || init(importanceEl.value)
  chart.setOption({
    tooltip: { backgroundColor: 'rgba(15,23,42,0.85)', borderColor: 'transparent', textStyle: { color: '#e2e8f0' } },
    xAxis: { type: 'value', axisLabel: { color: '#64748b' } },
    yAxis: { type: 'category', data: fi.features.map(f => f.name).reverse(), axisLabel: { color: '#64748b', fontSize: 11 } },
    grid: { left: '35%', right: 20, top: 10, bottom: 30 },
    series: [{ type: 'bar', data: fi.features.map(f => f.importance).reverse(), itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#059669' }, { offset: 1, color: '#0d9488' }] }, borderRadius: [0, 4, 4, 0] } }],
  })
  chart.resize()
}

// Tab 切换后等 DOM 更新再 resize 图表
watch(activeTab, async (tab) => {
  await nextTick()
  setTimeout(() => {
    if (tab === 'confusion' && confusionEl.value) {
      const c = getInstanceByDom(confusionEl.value); c?.resize()
      if (!c && localMetrics.value[0]) renderConfusionMatrix(localMetrics.value[0])
    }
    if (tab === 'importance' && importanceEl.value) {
      const c = getInstanceByDom(importanceEl.value); c?.resize()
      if (!c) renderFeatureImportance()
    }
  }, 100)
})

onMounted(async () => {
  await load()
  const tl = createTimeline({ defaults: { ease: 'outCubic', duration: 400 } })
  tl.add('.page-header', { opacity: { from: 0, to: 1 }, y: { from: -12, to: 0 } }, 0)
  tl.add('.metric-card', { opacity: { from: 0, to: 1 }, y: { from: 16, to: 0 }, scale: { from: 0.95, to: 1 }, delay: stagger(60, { from: 'center' }) }, 100)
  tl.add('.panel', { opacity: { from: 0, to: 1 }, y: { from: 20, to: 0 }, delay: stagger(80) }, 250)
  if (localMetrics.value[0]) renderConfusionMatrix(localMetrics.value[0])
  renderFeatureImportance()
})
</script>

<template>
  <section class="page">
    <PageHeader eyebrow="PCR ANALYSIS" title="pCR辅助分析与模型评估"
      :subtitle="role==='医生'?'基于影像与临床病理数据发起pCR辅助分析，查看详细结果。':'查看历史分析任务、模型指标和科室统计结果。'">
      <el-button v-if="canCreate" type="primary" @click="createTask">创建规则分析</el-button>
    </PageHeader>

    <div class="metric-grid">
      <MetricCard label="真实数据患者" :value="patients.length" hint="来自本地Excel与MRI图片">
        <template #value><CountUp :value="patients.length" /></template>
      </MetricCard>
      <MetricCard label="pCR有标签样本" :value="knownPcrCount" hint="用于本地模型评估" tone="green">
        <template #value><CountUp :value="knownPcrCount" /></template>
      </MetricCard>
      <MetricCard label="本地模型数量" :value="localMetrics.length" hint="仅展示真实本地数据集指标" tone="amber">
        <template #value><CountUp :value="localMetrics.length" /></template>
      </MetricCard>
      <MetricCard label="医学边界" value="课程展示" hint="不替代临床判断" tone="red" />
    </div>

    <!-- 任务创建区 -->
    <div class="panel">
      <div v-if="!canCreate" class="readonly-note">科室管理员模式：可查看任务和指标，不能发起分析。</div>
      <el-space wrap>
        <el-select v-model="patientId" class="control-select" placeholder="选择患者" @change="loadImages">
          <el-option v-for="p in patients" :key="p.id" :label="`${p.patient_code} ${p.name_masked}`" :value="p.id" />
        </el-select>
        <el-select v-model="imageId" class="control-select" placeholder="选择影像">
          <el-option v-for="i in images" :key="i.id" :label="i.filename" :value="i.id" />
        </el-select>
      </el-space>
    </div>

    <!-- 分析任务列表 -->
    <div class="panel">
      <h3 class="section-title">分析任务</h3>
      <el-table :data="tasks" height="400" @row-click="openDetail" class="clickable-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="patient_id" label="患者" width="80" />
        <el-table-column label="分子分型" min-width="120">
          <template #default="{ row }">{{ row.molecular_subtype || '—' }}</template>
        </el-table-column>
        <el-table-column label="pCR概率" width="120">
          <template #default="{ row }">
            <span class="prob-value">{{ (row.pcr_probability * 100).toFixed(1) }}%</span>
          </template>
        </el-table-column>
        <el-table-column label="风险" width="100">
          <template #default="{ row }">
            <span class="risk-tag" :class="`risk-${row.risk_level}`">{{ row.risk_level || '中等' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }"><StatusPill :value="row.task_status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click.stop="openDetail(row)">详情</el-button>
            <el-button v-if="canCreate" size="small" @click.stop="exportReport(row)">导出PDF</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!tasks.length" class="empty-task">暂无分析任务。选择患者后创建规则pCR辅助分析。</div>
    </div>

    <!-- 模型评估 Tabs -->
    <div class="panel">
      <div class="tab-bar">
        <button class="tab-btn" :class="{active: activeTab==='metrics'}" @click="activeTab='metrics'">模型指标</button>
        <button class="tab-btn" :class="{active: activeTab==='confusion'}" @click="activeTab='confusion'">混淆矩阵</button>
        <button class="tab-btn" :class="{active: activeTab==='importance'}" @click="activeTab='importance'">特征重要性</button>
      </div>

      <div v-show="activeTab==='metrics'">
        <el-table :data="localMetrics">
          <el-table-column prop="model_name" label="模型" min-width="200" />
          <el-table-column label="数据来源" min-width="140"><template #default="{ row }">{{ row.data_source || '数据库记录' }}</template></el-table-column>
          <el-table-column label="样本数" width="80"><template #default="{ row }">{{ row.sample_count ?? '—' }}</template></el-table-column>
          <el-table-column label="Acc" width="80"><template #default="{ row }">{{ row.accuracy.toFixed(3) }}</template></el-table-column>
          <el-table-column label="Prec" width="80"><template #default="{ row }">{{ row.precision.toFixed(3) }}</template></el-table-column>
          <el-table-column label="Recall" width="80"><template #default="{ row }">{{ row.recall.toFixed(3) }}</template></el-table-column>
          <el-table-column label="F1" width="80"><template #default="{ row }">{{ row.f1.toFixed(3) }}</template></el-table-column>
          <el-table-column label="AUC" width="80"><template #default="{ row }">{{ row.auc.toFixed(3) }}</template></el-table-column>
        </el-table>
      </div>

      <div v-show="activeTab==='confusion'" class="chart-area">
        <div class="chart-header">
          <span>选择模型：</span>
          <el-select v-if="localMetrics.length>1" class="control-select-sm" :model-value="localMetrics[0]?.model_name" @change="(v:string) => { const m = localMetrics.find(x=>x.model_name===v); if(m) renderConfusionMatrix(m) }">
            <el-option v-for="m in localMetrics" :key="m.model_name" :label="m.model_name" :value="m.model_name" />
          </el-select>
        </div>
        <div ref="confusionEl" class="heatmap-chart"></div>
      </div>

      <div v-show="activeTab==='importance'" class="chart-area">
        <div v-if="!featureImp.length" class="empty-task">暂无特征重要性数据。请先执行模型训练脚本。</div>
        <div ref="importanceEl" class="importance-chart"></div>
      </div>
    </div>

    <AnalysisDetailDialog :task-id="detailTaskId" :visible="showDetail" @close="showDetail = false" />
  </section>
</template>

<style scoped>
.section-title { margin: 0 0 12px; font-size: 16px; font-weight: 600; color: var(--color-foreground); }
.readonly-note, .empty-task { padding: 10px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-strong); color: var(--color-muted); line-height: 1.6; margin-bottom: 12px; }

.prob-value { font-weight: 700; font-variant-numeric: tabular-nums; color: var(--color-foreground); }
.risk-tag { padding: 2px 10px; border-radius: var(--radius-full); font-size: 12px; font-weight: 600; }
.risk-高概率 { background: rgba(239,68,68,0.1); color: #dc2626; }
.risk-中等 { background: rgba(245,158,11,0.1); color: #d97706; }
.risk-低概率 { background: rgba(34,197,94,0.1); color: #059669; }

.clickable-table :deep(.el-table__row) { cursor: pointer; transition: background 150ms ease; }
.clickable-table :deep(.el-table__row:hover td) { background: rgba(59,130,246,0.04) !important; }

/* Tabs */
.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; padding: 4px; background: var(--color-surface-strong); border-radius: var(--radius-sm); border: 1px solid var(--color-border); }
.tab-btn { flex: 1; padding: 8px 16px; border: none; border-radius: 6px; background: transparent; color: var(--color-muted); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 200ms ease; }
.tab-btn:hover { color: var(--color-foreground); }
.tab-btn.active { background: var(--color-surface); color: var(--color-foreground); font-weight: 600; box-shadow: var(--shadow-sm); }

.chart-area { min-height: 200px; }
.chart-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: var(--color-muted); font-size: 13px; }
.heatmap-chart { height: 260px; }
.importance-chart { height: 300px; }
</style>
