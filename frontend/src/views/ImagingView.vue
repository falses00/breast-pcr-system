<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { animate, createTimeline, stagger } from 'animejs'
import { api } from '../api/client'
import type { AnalysisTask, AnnotationRecord, ImageRecord, Patient, ROIFeatureDetail } from '../api/types'
import PageHeader from '../components/PageHeader.vue'
import StatusPill from '../components/StatusPill.vue'
import { currentUserRole, isDoctorRole, roleProfiles } from '../rolePolicy'

const patients = ref<Patient[]>([])
const images = ref<ImageRecord[]>([])
const patientId = ref<number>()
const image = ref<ImageRecord | null>(null)
const annotations = ref<AnnotationRecord[]>([])
const imgEl = ref<HTMLImageElement>()
const canvasEl = ref<HTMLCanvasElement>()
const drawing = ref(false)
const start = reactive({ x: 0, y: 0 })
const end = reactive({ x: 0, y: 0 })
const remark = ref('')
const polyPoints = ref<{x:number;y:number}[]>([])
const drawTool = ref<'rectangle'|'ellipse'|'polygon'>('rectangle')
const lesionType = ref('疑似病灶')
const lastFeatures = ref<ROIFeatureDetail|null>(null)
const showHistory = ref(true)
const lastAnnotationId = ref<number | null>(null)
const pcrResult = ref<AnalysisTask | null>(null)

const lesionTypes = ['疑似病灶','良性结节','恶性肿块','钙化灶','淋巴结']
const toolLabels: Record<string,string> = { rectangle:'矩形', ellipse:'椭圆', polygon:'多边形' }

const imageSrc = computed(() => image.value?.image_url || '')
const role = computed(() => currentUserRole())
const canAnnotate = computed(() => isDoctorRole(role.value))
const roleProfile = computed(() => (role.value ? roleProfiles[role.value] : undefined))
const localImageCount = computed(() => images.value.filter(i => i.source_type?.includes('本地验证数据集')).length)
const currentPatient = computed(() => patients.value.find(p => p.id === patientId.value))
const currentClinical = computed(() => currentPatient.value?.latest_clinical)

const roiColors: Record<string,string> = {
  '疑似病灶':'#ef4444','良性结节':'#22c55e','恶性肿块':'#f59e0b','钙化灶':'#8b5cf6','淋巴结':'#06b6d4'
}

function hexToRgba(hex: string, alpha: number) {
  const r = parseInt(hex.slice(1, 3), 16) || 59
  const g = parseInt(hex.slice(3, 5), 16) || 130
  const b = parseInt(hex.slice(5, 7), 16) || 246
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

async function loadPatients() {
  patients.value = await api.patients()
  if (!patientId.value) {
    const allImages = await api.images()
    const localImg = allImages.find(i => i.source_type?.includes('本地验证数据集'))
    patientId.value = localImg?.patient_id || patients.value[0]?.id
  }
  await loadImages()
}

async function loadImages() {
  images.value = await api.images(patientId.value)
  if (!image.value || !images.value.some(i => i.id === image.value?.id))
    image.value = images.value.find(i => i.source_type?.includes('本地验证数据集')) || images.value[0] || null
  setupCanvas(); await loadAnnotations()
}

async function loadAnnotations() {
  annotations.value = image.value ? await api.annotations(image.value.id) : []
}

async function handleImageChange() { setupCanvas(); await loadAnnotations() }
async function selectImage(item: ImageRecord) { image.value = item; await handleImageChange() }

async function upload(file: File) {
  if (!canAnnotate.value) return ElMessage.warning('当前角色不能上传影像')
  if (!patientId.value) return ElMessage.warning('请选择患者')
  await api.uploadImage(patientId.value, file)
  ElMessage.success('影像已上传'); await loadImages()
}

function setupCanvas() {
  nextTick(() => {
    const img = imgEl.value; const canvas = canvasEl.value
    if (!img || !canvas) return
    canvas.width = img.clientWidth; canvas.height = img.clientHeight; draw()
  })
}

function point(evt: MouseEvent) {
  const rect = canvasEl.value!.getBoundingClientRect()
  return { x: evt.clientX - rect.left, y: evt.clientY - rect.top }
}

function draw() {
  const canvas = canvasEl.value; if (!canvas) return
  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // 绘制历史标注
  if (showHistory.value) {
    for (const ann of annotations.value) {
      const pts = ann.roi_json?.points || []
      if (pts.length < 2) continue
      const color = roiColors[ann.lesion_type] || '#3b82f6'
      ctx.strokeStyle = color; ctx.lineWidth = 1.5
      ctx.fillStyle = hexToRgba(color, 0.15)
      const type = ann.roi_json?.type || 'rectangle'
      if (type === 'ellipse') {
        const cx = (pts[0].x+pts[1].x)/2, cy = (pts[0].y+pts[1].y)/2
        const rx = Math.abs(pts[1].x-pts[0].x)/2, ry = Math.abs(pts[1].y-pts[0].y)/2
        ctx.beginPath(); ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2); ctx.fill(); ctx.stroke()
      } else if (type === 'polygon' && pts.length > 2) {
        ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y)
        for (let i=1;i<pts.length;i++) ctx.lineTo(pts[i].x, pts[i].y)
        ctx.closePath(); ctx.fill(); ctx.stroke()
      } else {
        const x=Math.min(pts[0].x,pts[1].x), y=Math.min(pts[0].y,pts[1].y)
        const w=Math.abs(pts[1].x-pts[0].x), h=Math.abs(pts[1].y-pts[0].y)
        ctx.fillRect(x,y,w,h); ctx.strokeRect(x,y,w,h)
      }
      ctx.font = '11px Inter, sans-serif'; ctx.fillStyle = color
      ctx.fillText(`v${ann.version_no} ${ann.lesion_type}`, pts[0].x, pts[0].y - 4)
    }
  }

  // 绘制当前标注
  const color = roiColors[lesionType.value] || '#ef4444'
  ctx.strokeStyle = color; ctx.lineWidth = 2
  ctx.fillStyle = hexToRgba(color, 0.15)

  if (drawTool.value === 'polygon' && polyPoints.value.length > 0) {
    ctx.beginPath(); ctx.moveTo(polyPoints.value[0].x, polyPoints.value[0].y)
    for (let i=1;i<polyPoints.value.length;i++) ctx.lineTo(polyPoints.value[i].x, polyPoints.value[i].y)
    if (drawing.value) ctx.lineTo(end.x, end.y)
    ctx.stroke()
    polyPoints.value.forEach(p => { ctx.beginPath(); ctx.arc(p.x,p.y,3,0,Math.PI*2); ctx.fillStyle=color; ctx.fill() })
  } else if (drawTool.value === 'ellipse') {
    const cx=(start.x+end.x)/2, cy=(start.y+end.y)/2
    const rx=Math.abs(end.x-start.x)/2, ry=Math.abs(end.y-start.y)/2
    if (rx>0&&ry>0) { ctx.beginPath(); ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2); ctx.fill(); ctx.stroke() }
  } else {
    const x=Math.min(start.x,end.x), y=Math.min(start.y,end.y)
    const w=Math.abs(end.x-start.x), h=Math.abs(end.y-start.y)
    if (w>0&&h>0) { ctx.fillRect(x,y,w,h); ctx.strokeRect(x,y,w,h) }
  }
}

function begin(evt: MouseEvent) {
  if (!canAnnotate.value || !image.value) return
  const p = point(evt)
  if (drawTool.value === 'polygon') {
    polyPoints.value.push(p); drawing.value = true; draw(); return
  }
  start.x=p.x; start.y=p.y; end.x=p.x; end.y=p.y; drawing.value=true
}

function move(evt: MouseEvent) {
  if (!drawing.value) return
  const p = point(evt); end.x=p.x; end.y=p.y; draw()
}

function finish() { if (drawTool.value !== 'polygon') drawing.value = false }

function finishPolygon() {
  if (polyPoints.value.length < 3) return ElMessage.warning('多边形至少需要3个点')
  drawing.value = false; draw()
}

async function saveRoi() {
  if (!canAnnotate.value) return ElMessage.warning('当前角色只能查看影像与标注结果')
  if (!image.value || !patientId.value) return

  let points: {x:number;y:number}[]
  if (drawTool.value === 'polygon') {
    if (polyPoints.value.length < 3) return ElMessage.warning('多边形至少需要3个点')
    points = [...polyPoints.value]
  } else {
    points = [{x:start.x,y:start.y},{x:end.x,y:end.y}]
  }

  const res = await api.createAnnotation({
    patient_id: patientId.value, image_id: image.value.id, slice_no: 1,
    roi_json: { type: drawTool.value, points },
    lesion_type: lesionType.value, remark: remark.value,
  })
  lastFeatures.value = res.roi_features
  lastAnnotationId.value = res.id
  ElMessage.success(`ROI已保存 · 面积 ${Math.round(res.roi_features.area)} · ${lesionType.value}`)
  polyPoints.value = []; await loadImages()
  // 保存成功后用 anime.js 动画高亮特征面板
  await nextTick()
  animate('.features-panel', { scale: { from: 0.96, to: 1 }, opacity: { from: 0.5, to: 1 }, duration: 350, ease: 'outCubic' })
}

async function launchPcr() {
  if (!patientId.value) return ElMessage.warning('请先选择患者')
  try {
    const task = await api.createAnalysis({
      patient_id: patientId.value,
      image_id: image.value?.id,
      annotation_id: lastAnnotationId.value || undefined,
    })
    ElMessage.success(`pCR分析任务已创建 · 概率 ${(task.pcr_probability * 100).toFixed(1)}%`)
    pcrResult.value = task
    await nextTick()
    animate('.pcr-result-card', { scale: { from: 0.92, to: 1 }, opacity: { from: 0, to: 1 }, duration: 400, ease: 'outCubic' })
  } catch (e: any) {
    ElMessage.error(e.message || '分析失败')
  }
}

async function viewAnnotationFeatures(ann: AnnotationRecord) {
  try {
    lastFeatures.value = await api.annotationFeatures(ann.id)
    lastAnnotationId.value = ann.id
    await nextTick()
    animate('.features-panel .feat-item', { opacity: { from: 0, to: 1 }, y: { from: 8, to: 0 }, delay: stagger(30), duration: 250, ease: 'outCubic' })
  } catch { /* 忽略 */ }
}

function resetDraw() { polyPoints.value=[]; start.x=0; start.y=0; end.x=0; end.y=0; drawing.value=false; draw() }

onMounted(async () => {
  await loadPatients()
  const tl = createTimeline({ defaults: { ease: 'outCubic', duration: 400 } })
  tl.add('.data-metric', { opacity: { from: 0, to: 1 }, y: { from: 16, to: 0 }, delay: stagger(50, { from: 'center' }) }, 0)
  tl.add('.imaging-toolbar', { opacity: { from: 0, to: 1 }, y: { from: 12, to: 0 } }, 150)
  tl.add('.image-thumb', { opacity: { from: 0, to: 1 }, scale: { from: 0.9, to: 1 }, delay: stagger(40) }, 250)
  tl.add('.viewer-panel', { opacity: { from: 0, to: 1 }, x: { from: -20, to: 0 } }, 300)
  tl.add('.roi-panel', { opacity: { from: 0, to: 1 }, x: { from: 20, to: 0 } }, 350)
})
</script>

<template>
  <section class="page">
    <PageHeader eyebrow="MRI VIEWER" title="影像浏览与ROI标注"
      :subtitle="role==='医生'?'上传MRI影像，使用矩形/椭圆/多边形工具完成ROI标注和灰度特征提取。':'科室管理员查看影像、标注历史和来源。'" />

    <div class="data-strip">
      <div class="data-metric"><span>当前患者</span><strong>{{ currentPatient?.patient_code || '未选择' }}</strong><em>{{ currentClinical?.tumor_type || '临床数据待加载' }}</em></div>
      <div class="data-metric"><span>本患者影像</span><strong>{{ images.length }}</strong><em>本地真实MRI：{{ localImageCount }} 张</em></div>
      <div class="data-metric"><span>当前来源</span><strong>{{ image?.source_type || '未选择' }}</strong><em>默认优先真实数据集影像</em></div>
      <div class="data-metric"><span>标注版本</span><strong>{{ annotations.length }}</strong><em>保存后自动生成版本号</em></div>
    </div>

    <div class="panel imaging-toolbar">
      <el-space wrap>
        <el-select v-model="patientId" class="control-select" placeholder="选择患者" @change="loadImages">
          <el-option v-for="p in patients" :key="p.id" :label="`${p.patient_code} ${p.name_masked}`" :value="p.id" />
        </el-select>
        <el-upload v-if="canAnnotate" :auto-upload="false" :show-file-list="false" accept=".png,.jpg,.jpeg" :on-change="(f: any) => upload(f.raw)">
          <el-button type="primary">上传PNG/JPG影像</el-button>
        </el-upload>
        <span v-else class="readonly-chip">只读查看</span>
      </el-space>
      <div class="image-strip">
        <button v-for="item in images" :key="item.id" class="image-thumb" :class="{ active: item.id === image?.id }" type="button" @click="selectImage(item)">
          <img :src="item.image_url" :alt="item.filename" loading="lazy" />
          <span>{{ item.filename }}</span><em>{{ item.source_type }}</em>
        </button>
      </div>
    </div>

    <div class="imaging-grid">
      <div class="panel viewer-panel">
        <!-- 工具栏 -->
        <div v-if="canAnnotate" class="tool-bar">
          <button v-for="(label, tool) in toolLabels" :key="tool" class="tool-btn" :class="{active: drawTool===tool}" @click="drawTool=tool as any; resetDraw()">{{ label }}</button>
          <el-select v-model="lesionType" class="control-select-sm" placeholder="标注类型">
            <el-option v-for="t in lesionTypes" :key="t" :label="t" :value="t" />
          </el-select>
          <label class="toggle-label"><input type="checkbox" v-model="showHistory" @change="draw()"><span>显示历史</span></label>
          <button v-if="drawTool==='polygon'" class="tool-btn accent" @click="finishPolygon">完成多边形</button>
        </div>
        <div class="canvas-wrap">
          <img v-if="imageSrc" ref="imgEl" :src="imageSrc" alt="MRI影像" @load="setupCanvas" />
          <div v-else class="empty-view">选择或上传一张MRI样例影像后开始标注</div>
          <canvas ref="canvasEl" :class="{readonly:!canAnnotate}" @mousedown="begin" @mousemove="move" @mouseup="finish" @mouseleave="finish"></canvas>
        </div>
      </div>

      <aside class="panel roi-panel">
        <h3>标注检查器</h3>
        <p class="panel-desc">使用工具栏选择标注形状，拖拽画布绘制 ROI。保存后提取完整特征。</p>
        <div class="roi-meta">
          <span>当前影像</span><strong>{{ image?.filename || '未选择' }}</strong>
          <span>来源：{{ image?.source_type || '未加载' }}</span>
          <StatusPill :value="image?.status || '待标注'" />
        </div>

        <template v-if="canAnnotate">
          <el-input v-model="remark" type="textarea" :rows="2" placeholder="标注备注（可选）" />
          <el-button type="primary" class="full-button" @click="saveRoi">💾 保存ROI标注</el-button>
          <el-button class="full-button" @click="resetDraw">清除当前绘制</el-button>
          <el-button v-if="lastFeatures" type="success" class="full-button pcr-launch-btn" @click="launchPcr">🧬 基于此ROI发起pCR分析</el-button>
        </template>
        <div v-else class="readonly-note">当前账号为科室管理员，只能复核医生保存的标注版本和影像来源。</div>

        <!-- pCR 快速分析结果卡片 -->
        <div v-if="pcrResult" class="pcr-result-card">
          <div class="pcr-result-header">
            <span class="pcr-result-badge" :class="{ high: pcrResult.risk_level === '高概率', low: pcrResult.risk_level === '低概率' }">{{ pcrResult.risk_level }}</span>
            <strong>{{ pcrResult.molecular_subtype }}</strong>
          </div>
          <div class="pcr-result-prob">
            <div class="pcr-bar-bg"><div class="pcr-bar-fill" :style="{ width: (pcrResult.pcr_probability * 100) + '%' }"></div></div>
            <span>{{ (pcrResult.pcr_probability * 100).toFixed(1) }}%</span>
          </div>
          <ul v-if="pcrResult.key_factors?.length" class="pcr-factors">
            <li v-for="(f, i) in pcrResult.key_factors" :key="i">{{ f }}</li>
          </ul>
        </div>

        <!-- ROI 特征面板 -->
        <div v-if="lastFeatures" class="features-panel">
          <h4>📊 ROI 组学特征</h4>
          <div class="feat-grid">
            <div class="feat-item"><span>面积</span><strong>{{ Math.round(lastFeatures.area) }}</strong><em>px²</em></div>
            <div class="feat-item"><span>灰度均值</span><strong>{{ lastFeatures.gray_mean?.toFixed(1) }}</strong></div>
            <div class="feat-item"><span>灰度方差</span><strong>{{ lastFeatures.gray_std?.toFixed(1) }}</strong></div>
            <div class="feat-item"><span>偏度</span><strong>{{ lastFeatures.gray_skewness?.toFixed(3) }}</strong></div>
            <div class="feat-item"><span>峰度</span><strong>{{ lastFeatures.gray_kurtosis?.toFixed(3) }}</strong></div>
            <div class="feat-item accent"><span>熵</span><strong>{{ lastFeatures.gray_entropy?.toFixed(3) }}</strong></div>
            <div class="feat-item"><span>对比度</span><strong>{{ lastFeatures.gray_contrast?.toFixed(1) }}</strong></div>
            <div class="feat-item accent"><span>紧凑度</span><strong>{{ lastFeatures.compactness?.toFixed(4) }}</strong></div>
            <div class="feat-item"><span>周长</span><strong>{{ lastFeatures.perimeter?.toFixed(1) }}</strong><em>px</em></div>
          </div>
        </div>

        <!-- 标注历史时间线 -->
        <div class="annotation-history">
          <h4>📋 标注历史 <span v-if="annotations.length" class="hist-count">{{ annotations.length }}条</span></h4>
          <div v-if="!annotations.length" class="history-empty">暂无历史标注，请在左侧画布绘制 ROI</div>
          <div v-for="item in annotations" :key="item.id" class="history-item" :class="{ selected: lastAnnotationId === item.id }" @click="viewAnnotationFeatures(item)">
            <div class="hist-timeline-dot" :style="{ background: roiColors[item.lesion_type] || '#3b82f6' }"></div>
            <div class="hist-body">
              <div class="hist-head">
                <strong>v{{ item.version_no }}</strong>
                <StatusPill :value="item.lesion_type" />
                <span class="hist-type">{{ item.roi_json?.type || 'rect' }}</span>
              </div>
              <p>{{ item.remark || '无备注' }}</p>
              <span class="hist-hint">点击查看特征</span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.imaging-toolbar { display: grid; gap: 12px; }
.data-strip { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; }
.data-metric { padding: 14px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-glass); backdrop-filter: blur(8px); box-shadow: var(--shadow-sm); }
.data-metric span, .data-metric em { display: block; overflow: hidden; color: var(--color-muted); font-size: 13px; font-style: normal; text-overflow: ellipsis; white-space: nowrap; }
.data-metric strong { display: block; margin: 6px 0; color: var(--color-foreground); font-size: 18px; font-weight: 700; }
.imaging-grid { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 16px; }
.viewer-panel { min-width: 0; }
.image-strip { display: grid; grid-template-columns: repeat(auto-fill, minmax(108px, 1fr)); gap: 10px; max-height: 178px; overflow: auto; }
.image-thumb { display: grid; gap: 5px; padding: 8px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface); color: var(--color-foreground); cursor: pointer; text-align: left; transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease; }
.image-thumb:hover, .image-thumb.active { border-color: var(--color-primary-light); box-shadow: var(--shadow-md); transform: translateY(-1px); }
.image-thumb img { width: 100%; aspect-ratio: 1.2/1; object-fit: cover; border-radius: 6px; background: #0a0f1a; }
.image-thumb span, .image-thumb em { overflow: hidden; font-size: 12px; font-style: normal; text-overflow: ellipsis; white-space: nowrap; }
.image-thumb em { color: var(--color-muted); }

/* 工具栏 */
.tool-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.tool-btn { padding: 6px 14px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: var(--color-surface-glass); color: var(--color-foreground); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 150ms ease; }
.tool-btn:hover { border-color: var(--color-primary-light); }
.tool-btn.active { background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(14,116,144,0.1)); border-color: var(--color-primary-light); color: var(--color-primary); font-weight: 600; }
.tool-btn.accent { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.toggle-label { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--color-muted); cursor: pointer; }

/* ROI 面板 */
.roi-panel { overflow-y: auto; max-height: calc(100vh - 200px); }
.roi-panel h3 { margin: 0 0 4px; }
.panel-desc { color: var(--color-muted); line-height: 1.6; font-size: 13px; margin: 0 0 12px; }
.roi-meta { display: grid; gap: 6px; margin: 0 0 14px; padding: 12px; border-radius: var(--radius-sm); background: var(--color-surface-strong); border: 1px solid var(--color-border); }
.roi-meta span { color: var(--color-muted); font-size: 13px; }
.readonly-note, .readonly-chip { padding: 10px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-strong); color: var(--color-muted); line-height: 1.6; }
.readonly-chip { display: inline-flex; align-items: center; min-height: 32px; font-size: 13px; font-weight: 600; }
.full-button { width: 100%; margin-top: 8px; }
.pcr-launch-btn { animation: pulseGlow 2s ease-in-out infinite; }
@keyframes pulseGlow { 0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.3); } 50% { box-shadow: 0 0 12px 4px rgba(34,197,94,0.15); } }

/* pCR 结果卡片 */
.pcr-result-card { margin-top: 12px; padding: 14px; border-radius: var(--radius-md); background: linear-gradient(135deg, rgba(59,130,246,0.06), rgba(14,116,144,0.06)); border: 1px solid rgba(59,130,246,0.2); }
.pcr-result-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.pcr-result-header strong { font-size: 14px; color: var(--color-foreground); }
.pcr-result-badge { padding: 3px 10px; border-radius: var(--radius-full); font-size: 12px; font-weight: 600; color: #fff; background: #f59e0b; }
.pcr-result-badge.high { background: #ef4444; }
.pcr-result-badge.low { background: #22c55e; }
.pcr-result-prob { display: flex; align-items: center; gap: 10px; }
.pcr-result-prob span { font-size: 18px; font-weight: 700; color: var(--color-primary); font-variant-numeric: tabular-nums; }
.pcr-bar-bg { flex: 1; height: 8px; border-radius: 4px; background: var(--color-surface-strong); overflow: hidden; }
.pcr-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #3b82f6, #0ea5e9); transition: width 600ms ease; }
.pcr-factors { margin: 8px 0 0; padding-left: 18px; }
.pcr-factors li { font-size: 12px; color: var(--color-muted); line-height: 1.7; }

/* 特征面板 */
.features-panel { margin-top: 14px; padding: 14px; border-radius: var(--radius-md); background: linear-gradient(135deg, rgba(5,150,105,0.05), rgba(14,116,144,0.05)); border: 1px solid rgba(5,150,105,0.15); }
.features-panel h4 { margin: 0 0 10px; font-size: 14px; color: var(--color-success); }
.feat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.feat-item { padding: 6px 8px; border-radius: 6px; background: var(--color-surface-glass); border: 1px solid var(--color-border); transition: border-color 200ms; }
.feat-item:hover { border-color: var(--color-primary-light); }
.feat-item.accent { border-color: rgba(5,150,105,0.3); background: rgba(5,150,105,0.04); }
.feat-item span { display: block; font-size: 10px; color: var(--color-muted); text-transform: uppercase; letter-spacing: 0.03em; }
.feat-item strong { display: block; font-size: 14px; color: var(--color-foreground); font-weight: 600; font-variant-numeric: tabular-nums; }
.feat-item em { font-size: 10px; color: var(--color-muted); font-style: normal; }

/* 标注历史时间线 */
.annotation-history { margin-top: 16px; }
.annotation-history h4 { margin: 0 0 10px; color: var(--color-foreground); font-size: 14px; display: flex; align-items: center; gap: 8px; }
.hist-count { font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: var(--radius-full); background: var(--color-surface-strong); color: var(--color-muted); }
.history-empty { padding: 16px; border: 1px dashed var(--color-border); border-radius: var(--radius-sm); color: var(--color-muted); font-size: 13px; text-align: center; }
.history-item { display: flex; gap: 12px; padding: 10px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface); margin-bottom: 8px; cursor: pointer; transition: all 180ms ease; }
.history-item:hover { border-color: var(--color-primary-light); background: rgba(59,130,246,0.03); transform: translateX(2px); }
.history-item.selected { border-color: var(--color-primary); background: rgba(59,130,246,0.06); box-shadow: 0 0 0 1px var(--color-primary-light); }
.hist-timeline-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; box-shadow: 0 0 0 3px var(--color-surface), 0 0 0 4px var(--color-border); }
.hist-body { flex: 1; min-width: 0; }
.hist-head { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.hist-head strong { font-size: 13px; color: var(--color-foreground); }
.hist-type { font-size: 11px; color: var(--color-muted); padding: 1px 6px; border-radius: 4px; background: var(--color-surface-strong); }
.history-item p { margin: 3px 0 0; font-size: 12px; color: var(--color-muted); }
.hist-hint { font-size: 11px; color: var(--color-primary-light); opacity: 0; transition: opacity 200ms; }
.history-item:hover .hist-hint { opacity: 1; }
.empty-view { display: grid; place-items: center; min-height: 420px; color: rgba(148,163,184,0.5); }
.canvas-wrap canvas.readonly { cursor: default; }

@media (max-width: 1000px) { .imaging-grid { grid-template-columns: 1fr; } .data-strip { grid-template-columns: repeat(2, minmax(140px, 1fr)); } }
@media (max-width: 620px) { .data-strip { grid-template-columns: 1fr; } }
</style>
