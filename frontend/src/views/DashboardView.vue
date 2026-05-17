<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { animate, createTimeline, stagger } from 'animejs'
import { api } from '../api/client'
import type { StatsSummary } from '../api/types'
import PageHeader from '../components/PageHeader.vue'
import MetricCard from '../components/MetricCard.vue'
import CountUp from '../components/CountUp.vue'
import SkeletonLoader from '../components/SkeletonLoader.vue'
import { currentUserRole, roleProfiles } from '../rolePolicy'

use([BarChart, PieChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const stats = ref<StatsSummary | null>(null)
const loading = ref(true)
const tumorChart = ref<HTMLDivElement>()
const probChart = ref<HTMLDivElement>()
const ageChart = ref<HTMLDivElement>()
const role = computed(() => currentUserRole())
const roleProfile = computed(() => (role.value ? roleProfiles[role.value] : undefined))

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
  // anime.js v4 createTimeline 编排入场动画
  const tl = createTimeline({
    defaults: { ease: 'outCubic', duration: 500 },
  })
  tl.add('.page-header', { opacity: { from: 0, to: 1 }, y: { from: -16, to: 0 }, duration: 400 }, 0)
  tl.add('.metric-card', { opacity: { from: 0, to: 1 }, y: { from: 20, to: 0 }, scale: { from: 0.95, to: 1 }, delay: stagger(60, { from: 'center' }) }, 100)
  tl.add('.quick-action', { opacity: { from: 0, to: 1 }, x: { from: -20, to: 0 }, delay: stagger(80) }, 300)
  tl.add('.disclaimer', { opacity: { from: 0, to: 1 }, y: { from: 10, to: 0 } }, 500)
  tl.add('.workflow-step', { opacity: { from: 0, to: 1 }, y: { from: 16, to: 0 }, delay: stagger(60) }, 600)
  tl.add('.chart-panel', { opacity: { from: 0, to: 1 }, y: { from: 24, to: 0 }, scale: { from: 0.97, to: 1 }, delay: stagger(100) }, 800)
  if (role.value === '系统管理员') { loading.value = false; return }
  stats.value = await api.stats()
  loading.value = false
  await nextTick()
  // 等待 CSS 动画完成后再初始化 ECharts，避免容器宽度为 0
  setTimeout(() => {
  if (!stats.value) return
  if (tumorChart.value) {
    init(tumorChart.value).setOption({
      tooltip: { trigger: 'item', backgroundColor: 'rgba(15,23,42,0.85)', borderColor: 'transparent', textStyle: { color: '#e2e8f0' } },
      legend: { bottom: 0, textStyle: { color: '#64748b' } },
      series: [{
        type: 'pie', radius: ['45%', '72%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { color: '#64748b' },
        data: stats.value.tumor_type_distribution,
      }],
    })
  }

  if (probChart.value && stats.value.model_task_probabilities.length) {
    init(probChart.value).setOption({
      tooltip: { backgroundColor: 'rgba(15,23,42,0.85)', borderColor: 'transparent', textStyle: { color: '#e2e8f0' } },
      xAxis: { type: 'category', data: stats.value.model_task_probabilities.map((_, i) => `任务${i + 1}`), axisLabel: { color: '#64748b' } },
      yAxis: { type: 'value', min: 0, max: 1, axisLabel: { color: '#64748b' } },
      series: [{
        type: 'bar', data: stats.value.model_task_probabilities,
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#3b82f6' }, { offset: 1, color: '#0e7490' }] }, borderRadius: [4, 4, 0, 0] },
      }],
    })
  }

  if (ageChart.value && stats.value.age_distribution.length) {
    init(ageChart.value).setOption({
      tooltip: { backgroundColor: 'rgba(15,23,42,0.85)', borderColor: 'transparent', textStyle: { color: '#e2e8f0' } },
      xAxis: { type: 'category', data: stats.value.age_distribution.map(d => d.name), axisLabel: { color: '#64748b' } },
      yAxis: { type: 'value', axisLabel: { color: '#64748b' } },
      series: [{
        type: 'bar', data: stats.value.age_distribution.map(d => d.value),
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#059669' }, { offset: 1, color: '#0d9488' }] }, borderRadius: [4, 4, 0, 0] },
      }],
    })
  }
  }, 500)
})
</script>

<template>
  <section class="page" @mousemove="handleMouseMove">
    <!-- 高级交互背景 (Aceternity 风格点阵) -->
    <div class="bg-dot-pattern"></div>

    <PageHeader
      eyebrow="CLINICAL AI WORKBENCH"
      :title="roleProfile?.title || '数据总览'"
      :subtitle="roleProfile?.scope || '把患者、影像、ROI、模型任务和审核状态放在同一个临床数据工作台里。'"
    >
      <template v-if="role === '医生'">
        <el-button type="primary" @click="$router.push('/patients')">新增患者</el-button>
        <el-button @click="$router.push('/imaging')">进入标注</el-button>
      </template>
      <template v-else-if="role === '科室管理员'">
        <el-button type="primary" @click="$router.push('/audit')">进入审核</el-button>
        <el-button @click="$router.push('/analysis')">查看统计</el-button>
      </template>
      <template v-else-if="role === '系统管理员'">
        <el-button type="primary" @click="$router.push('/users')">用户管理</el-button>
      </template>
    </PageHeader>

    <div v-if="role !== '系统管理员'" class="metric-grid">
      <MetricCard label="患者数" :value="stats?.patient_count ?? 0" hint="真实本地数据集" tone="blue">
        <template #value><CountUp :value="stats?.patient_count ?? 0" /></template>
      </MetricCard>
      <MetricCard label="影像数" :value="stats?.image_count ?? 0" hint="真实数据集MRI PNG" tone="green">
        <template #value><CountUp :value="stats?.image_count ?? 0" /></template>
      </MetricCard>
      <MetricCard label="ROI标注" :value="stats?.annotation_count ?? 0" hint="支持矩形/椭圆/多边形" tone="amber">
        <template #value><CountUp :value="stats?.annotation_count ?? 0" /></template>
      </MetricCard>
      <MetricCard label="pCR比例" :value="stats?.pcr_ratio == null ? '待积累' : `${Math.round(stats.pcr_ratio * 100)}%`" hint="仅统计有标签样本" tone="red">
        <template v-if="stats?.pcr_ratio != null" #value><CountUp :value="Math.round(stats.pcr_ratio * 100)" suffix="%" /></template>
      </MetricCard>
    </div>

    <!-- 快速操作面板 -->
    <div v-if="role !== '系统管理员'" class="quick-actions">
      <div class="quick-action glow-card" @click="$router.push('/patients')">
        <div class="qa-icon qa-blue">📋</div>
        <div>
          <strong>患者建档</strong>
          <span>录入临床病理信息</span>
        </div>
      </div>
      <div class="quick-action glow-card" @click="$router.push('/imaging')">
        <div class="qa-icon qa-green">🔬</div>
        <div>
          <strong>影像标注</strong>
          <span>ROI绘制与特征提取</span>
        </div>
      </div>
      <div class="quick-action glow-card" @click="$router.push('/analysis')">
        <div class="qa-icon qa-amber">📊</div>
        <div>
          <strong>pCR分析</strong>
          <span>辅助分析与模型评估</span>
        </div>
      </div>
      <div v-if="role === '医生'" class="quick-action info-action glow-card">
        <div class="qa-icon qa-red">🏥</div>
        <div>
          <strong>{{ stats?.task_count ?? 0 }} 个分析任务</strong>
          <span>pCR阳性 {{ stats?.pcr_positive_count ?? 0 }} 例 / 阴性 {{ stats?.pcr_negative_count ?? 0 }} 例</span>
        </div>
      </div>
    </div>

    <div v-if="role !== '系统管理员'" class="panel disclaimer">{{ stats?.disclaimer }}</div>

    <div v-if="role !== '系统管理员'" class="workflow">
      <div class="workflow-step"><strong>1 患者建档</strong><span>临床病理信息结构化录入</span></div>
      <div class="workflow-step"><strong>2 影像上传</strong><span>PNG/JPG浏览，预留DICOM/NIfTI</span></div>
      <div class="workflow-step"><strong>3 ROI标注</strong><span>矩形/椭圆/多边形标注</span></div>
      <div class="workflow-step"><strong>4 辅助分析</strong><span>规则模型与传统ML指标</span></div>
      <div class="workflow-step"><strong>5 审核展示</strong><span>科室审核与图表统计</span></div>
    </div>

    <div v-if="role !== '系统管理员'" class="charts">
      <div class="panel chart-panel">
        <h3>肿瘤类型分布</h3>
        <SkeletonLoader v-if="loading" type="chart" />
        <div v-show="!loading" ref="tumorChart" class="chart"></div>
      </div>
      <div class="panel chart-panel">
        <h3>年龄段分布</h3>
        <SkeletonLoader v-if="loading" type="chart" />
        <div v-show="!loading" ref="ageChart" class="chart"></div>
      </div>
      <div class="panel chart-panel">
        <h3>分析任务pCR概率</h3>
        <SkeletonLoader v-if="loading" type="chart" />
        <div v-show="!loading" ref="probChart" class="chart"></div>
      </div>
    </div>

    <div v-if="role === '系统管理员'" class="panel sys-admin-guide border-beam">
      <div class="sys-icon">⚙️</div>
      <strong>系统管理员入口</strong>
      <p>当前账号仅负责账号创建、角色分配和系统权限维护。患者业务数据、影像标注、pCR分析和科室审核由对应角色完成。</p>
      <el-button type="primary" size="large" @click="$router.push('/users')">进入用户管理</el-button>
    </div>
  </section>
</template>

<style scoped>
.charts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.chart-panel h3 {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-foreground);
}

.chart {
  height: 300px;
}

/* ── 快速操作面板 ── */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-surface-glass);
  backdrop-filter: blur(8px);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-spring);
}

.quick-action:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-hover);
}

.qa-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 20px;
  flex-shrink: 0;
}

.qa-blue { background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(59,130,246,0.05)); }
.qa-green { background: linear-gradient(135deg, rgba(5,150,105,0.15), rgba(5,150,105,0.05)); }
.qa-amber { background: linear-gradient(135deg, rgba(217,119,6,0.15), rgba(217,119,6,0.05)); }
.qa-red { background: linear-gradient(135deg, rgba(220,38,38,0.15), rgba(220,38,38,0.05)); }

.quick-action strong {
  display: block;
  font-size: 14px;
  color: var(--color-foreground);
}

.quick-action span {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-muted);
}

.info-action {
  cursor: default;
}

/* ── 系统管理员引导 ── */
.sys-admin-guide {
  max-width: 720px;
  text-align: center;
  padding: 40px;
}

.sys-icon {
  font-size: 40px;
  margin-bottom: 16px;
}

.sys-admin-guide strong {
  display: block;
  font-size: 22px;
  color: var(--color-foreground);
}

.sys-admin-guide p {
  color: var(--color-muted);
  line-height: 1.7;
  margin: 12px 0 24px;
}

@media (max-width: 1200px) {
  .charts {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 1000px) {
  .charts {
    grid-template-columns: 1fr;
  }
  .quick-actions {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 620px) {
  .quick-actions {
    grid-template-columns: 1fr;
  }
}
</style>
