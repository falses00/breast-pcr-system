<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { init, use } from 'echarts/core'
import { GaugeChart, RadarChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, RadarComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { api } from '../api/client'
import type { AnalysisDetail } from '../api/types'
import StatusPill from './StatusPill.vue'

use([GaugeChart, RadarChart, BarChart, GridComponent, TooltipComponent, RadarComponent, CanvasRenderer])

const props = defineProps<{ taskId: number | null; visible: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const detail = ref<AnalysisDetail | null>(null)
const loading = ref(false)
const gaugeEl = ref<HTMLDivElement>()
const factorEl = ref<HTMLDivElement>()

const riskColor = computed(() => {
  const r = detail.value?.risk_level
  if (r === '高概率') return '#ef4444'
  if (r === '低概率') return '#22c55e'
  return '#f59e0b'
})

async function loadDetail() {
  if (!props.taskId) return
  loading.value = true
  try {
    detail.value = await api.analysisDetail(props.taskId)
    renderCharts()
  } finally { loading.value = false }
}

function renderCharts() {
  if (!detail.value) return
  setTimeout(() => {
    if (gaugeEl.value) {
      const prob = detail.value!.pcr_probability
      init(gaugeEl.value).setOption({
        series: [{
          type: 'gauge', startAngle: 200, endAngle: -20, min: 0, max: 1,
          pointer: { show: true, length: '60%', width: 4, itemStyle: { color: riskColor.value } },
          axisLine: { lineStyle: { width: 14, color: [[0.35, '#22c55e'], [0.6, '#f59e0b'], [1, '#ef4444']] } },
          axisTick: { show: false }, splitLine: { show: false },
          axisLabel: { distance: 20, color: '#64748b', fontSize: 11, formatter: (v: number) => `${Math.round(v * 100)}%` },
          detail: { valueAnimation: true, formatter: (v: number) => `${(v * 100).toFixed(1)}%`, color: riskColor.value, fontSize: 24, fontWeight: 700, offsetCenter: [0, '70%'] },
          data: [{ value: prob }],
        }],
      })
    }
    if (factorEl.value && detail.value!.key_factors?.length) {
      const factors = detail.value!.key_factors!
      init(factorEl.value).setOption({
        tooltip: { backgroundColor: 'rgba(15,23,42,0.85)', borderColor: 'transparent', textStyle: { color: '#e2e8f0' } },
        xAxis: { type: 'value', axisLabel: { show: false } },
        yAxis: { type: 'category', data: factors, axisLabel: { color: '#64748b', fontSize: 12 } },
        grid: { left: '40%', right: 20, top: 10, bottom: 10 },
        series: [{ type: 'bar', data: factors.map(() => 1), itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#3b82f6' }, { offset: 1, color: '#0ea5e9' }] }, borderRadius: [0, 4, 4, 0] } }],
      })
    }
  }, 100)
}

watch(() => props.visible, (v) => { if (v) loadDetail() })
</script>

<template>
  <el-dialog :model-value="visible" title="pCR 分析详情" width="860px" @close="emit('close')" destroy-on-close>
    <div v-if="loading" class="loading-state">正在加载分析详情…</div>
    <div v-else-if="detail" class="detail-layout">
      <!-- 顶部概览 -->
      <div class="detail-header">
        <div class="risk-badge" :style="{ background: riskColor, boxShadow: `0 0 16px ${riskColor}40` }">
          {{ detail.risk_level }}
        </div>
        <div>
          <strong>{{ detail.molecular_subtype }}</strong>
          <span>pCR 辅助概率：{{ (detail.pcr_probability * 100).toFixed(1) }}%</span>
        </div>
        <StatusPill :value="detail.task_status" />
      </div>

      <div class="detail-grid">
        <!-- 左列 -->
        <div class="detail-col">
          <!-- pCR 仪表盘 -->
          <div class="detail-card">
            <h4>pCR 辅助概率</h4>
            <div ref="gaugeEl" class="gauge-chart"></div>
          </div>

          <!-- 关键因素 -->
          <div v-if="detail.key_factors?.length" class="detail-card">
            <h4>关键影响因素</h4>
            <div ref="factorEl" class="factor-chart"></div>
          </div>
        </div>

        <!-- 右列 -->
        <div class="detail-col">
          <!-- 患者信息 -->
          <div v-if="detail.patient" class="detail-card">
            <h4>患者信息</h4>
            <div class="info-grid">
              <div><span>编号</span><strong>{{ detail.patient.patient_code }}</strong></div>
              <div><span>姓名</span><strong>{{ detail.patient.name_masked }}</strong></div>
              <div><span>年龄</span><strong>{{ detail.patient.age }}岁</strong></div>
              <div><span>性别</span><strong>{{ detail.patient.gender }}</strong></div>
            </div>
          </div>

          <!-- 临床信息 -->
          <div v-if="detail.clinical" class="detail-card">
            <h4>临床病理</h4>
            <div class="info-grid">
              <div><span>分型</span><strong>{{ detail.clinical.tumor_type }}</strong></div>
              <div><span>ER/PR/HER2</span><strong>{{ detail.clinical.er_status }}/{{ detail.clinical.pr_status }}/{{ detail.clinical.her2_status }}</strong></div>
              <div><span>Ki-67</span><strong>{{ detail.clinical.ki67 ?? '未知' }}%</strong></div>
              <div><span>Nottingham</span><strong>{{ detail.clinical.nottingham_grade || '未知' }}</strong></div>
              <div><span>pCR标签</span><strong>{{ detail.clinical.pcr_label === true ? '达到' : detail.clinical.pcr_label === false ? '未达到' : '未知' }}</strong></div>
              <div><span>治疗方案</span><strong>{{ detail.clinical.treatment_plan || '未记录' }}</strong></div>
            </div>
          </div>

          <!-- ROI 特征 -->
          <div v-if="detail.roi_features" class="detail-card">
            <h4>ROI 特征</h4>
            <div class="info-grid dense">
              <div><span>面积</span><strong>{{ Math.round(detail.roi_features.area) }}</strong></div>
              <div><span>灰度均值</span><strong>{{ detail.roi_features.gray_mean.toFixed(1) }}</strong></div>
              <div><span>灰度标准差</span><strong>{{ detail.roi_features.gray_std.toFixed(1) }}</strong></div>
              <div><span>熵</span><strong>{{ detail.roi_features.gray_entropy.toFixed(3) }}</strong></div>
              <div><span>紧凑度</span><strong>{{ detail.roi_features.compactness.toFixed(4) }}</strong></div>
              <div><span>周长</span><strong>{{ detail.roi_features.perimeter.toFixed(1) }}</strong></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 解释因子 -->
      <div class="detail-card explanations">
        <h4>分析解释</h4>
        <ul>
          <li v-for="(exp, i) in detail.explanations" :key="i">{{ exp }}</li>
        </ul>
      </div>

      <div class="disclaimer-sm">{{ detail.disclaimer }}</div>
    </div>
  </el-dialog>
</template>

<style scoped>
.loading-state { text-align: center; padding: 40px; color: var(--color-muted); }
.detail-layout { display: grid; gap: 16px; }
.detail-header { display: flex; align-items: center; gap: 14px; padding: 16px; border-radius: var(--radius-md); background: var(--color-surface-strong); border: 1px solid var(--color-border); }
.risk-badge { padding: 6px 16px; border-radius: var(--radius-full); color: #fff; font-weight: 700; font-size: 14px; }
.detail-header strong { display: block; font-size: 16px; color: var(--color-foreground); }
.detail-header span { color: var(--color-muted); font-size: 13px; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.detail-col { display: grid; gap: 14px; align-content: start; }
.detail-card { padding: 14px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: var(--color-surface); }
.detail-card h4 { margin: 0 0 10px; font-size: 13px; font-weight: 600; color: var(--color-primary); text-transform: uppercase; letter-spacing: 0.04em; }
.gauge-chart { height: 200px; }
.factor-chart { height: 120px; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.info-grid.dense { grid-template-columns: 1fr 1fr 1fr; }
.info-grid div { padding: 6px 8px; border-radius: 6px; background: var(--color-surface-strong); }
.info-grid span { display: block; font-size: 11px; color: var(--color-muted); }
.info-grid strong { display: block; font-size: 13px; color: var(--color-foreground); font-weight: 600; }
.explanations ul { margin: 0; padding-left: 18px; }
.explanations li { color: var(--color-muted); font-size: 13px; line-height: 1.7; }
.disclaimer-sm { font-size: 12px; color: #a16207; background: rgba(255,251,235,0.7); border: 1px solid rgba(253,230,138,0.3); border-radius: var(--radius-sm); padding: 8px 12px; }
@media (max-width: 700px) { .detail-grid { grid-template-columns: 1fr; } }
</style>
