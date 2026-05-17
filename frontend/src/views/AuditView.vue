<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createTimeline, stagger } from 'animejs'
import { api } from '../api/client'
import type { AuditRecord } from '../api/types'
import PageHeader from '../components/PageHeader.vue'
import StatusPill from '../components/StatusPill.vue'

const audits = ref<AuditRecord[]>([])
const opinionMap = ref<Record<number, string>>({})

// 统计指标
const pending = computed(() => audits.value.filter(a => a.review_status === '待审核').length)
const approved = computed(() => audits.value.filter(a => a.review_status === '通过').length)
const rejected = computed(() => audits.value.filter(a => a.review_status === '驳回' || a.review_status === '退回补充').length)

async function load() {
  audits.value = await api.audits()
}

async function review(row: AuditRecord, status: string) {
  const opinion = opinionMap.value[row.id] || (status === '通过' ? '审核通过，数据质量合格' : '需补充标注或临床信息')
  await api.updateAudit(row.id, { review_status: status, review_opinion: opinion })
  ElMessage.success(`已${status}`)
  await load()
}

onMounted(async () => {
  await load()
  const tl = createTimeline({ defaults: { ease: 'outCubic', duration: 400 } })
  tl.add('.page-header', { opacity: { from: 0, to: 1 }, y: { from: -12, to: 0 } }, 0)
  tl.add('.stat-card', { opacity: { from: 0, to: 1 }, y: { from: 16, to: 0 }, scale: { from: 0.95, to: 1 }, delay: stagger(60, { from: 'center' }) }, 100)
  tl.add('.panel', { opacity: { from: 0, to: 1 }, y: { from: 16, to: 0 } }, 350)
})
</script>

<template>
  <section class="page">
    <PageHeader
      eyebrow="QUALITY REVIEW"
      title="数据审核管理"
      subtitle="科室管理员对医生提交的标注与分析结果进行审核，确保数据质量与合规性。"
    />

    <!-- 统计卡 -->
    <div class="stat-strip">
      <div class="stat-card pending"><span>待审核</span><strong>{{ pending }}</strong><em>需科室管理员处理</em></div>
      <div class="stat-card"><span>已通过</span><strong>{{ approved }}</strong><em>数据质量合格</em></div>
      <div class="stat-card"><span>已退回</span><strong>{{ rejected }}</strong><em>需医生补充修改</em></div>
      <div class="stat-card"><span>审核总计</span><strong>{{ audits.length }}</strong><em>所有审核记录</em></div>
    </div>

    <div class="panel">
      <h3>审核列表</h3>
      <div v-if="!audits.length" class="empty-state">暂无审核记录。医生保存标注或创建分析任务后将自动产生。</div>
      <div v-for="row in audits" :key="row.id" class="audit-card" :class="{ pass: row.review_status === '通过', fail: row.review_status === '驳回' || row.review_status === '退回补充' }">
        <div class="audit-head">
          <div class="audit-info">
            <strong>{{ row.biz_type }}</strong>
            <span class="biz-id">业务ID #{{ row.biz_id }}</span>
            <StatusPill :value="row.review_status" />
          </div>
        </div>

        <!-- 现有审核意见 -->
        <div v-if="row.review_opinion" class="audit-opinion-display">
          <span>审核意见：</span>{{ row.review_opinion }}
        </div>

        <!-- 操作区 -->
        <div class="audit-actions">
          <el-input
            v-model="opinionMap[row.id]"
            size="small"
            :placeholder="row.review_status === '待审核' ? '输入审核意见...' : '修改审核意见...'"
            class="opinion-input"
          />
          <el-button size="small" type="success" @click="review(row, '通过')">✅ 通过</el-button>
          <el-button size="small" type="warning" @click="review(row, '退回补充')">↩️ 退回</el-button>
          <el-button size="small" type="danger" @click="review(row, '驳回')">❌ 驳回</el-button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.stat-strip { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; }
.stat-card { padding: 14px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-glass); backdrop-filter: blur(8px); }
.stat-card span, .stat-card em { display: block; color: var(--color-muted); font-size: 13px; font-style: normal; }
.stat-card strong { display: block; margin: 6px 0; color: var(--color-foreground); font-size: 20px; font-weight: 700; }
.stat-card.pending { border-color: rgba(245,158,11,0.3); background: linear-gradient(135deg, rgba(245,158,11,0.04), transparent); }
.stat-card.pending strong { color: #f59e0b; }

.empty-state { padding: 24px; text-align: center; color: var(--color-muted); border: 1px dashed var(--color-border); border-radius: var(--radius-sm); }

.audit-card { padding: 14px; margin-bottom: 10px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface); transition: border-color 200ms, box-shadow 200ms; }
.audit-card:hover { border-color: var(--color-primary-light); box-shadow: var(--shadow-sm); }
.audit-card.pass { border-left: 3px solid #22c55e; }
.audit-card.fail { border-left: 3px solid #ef4444; }

.audit-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.audit-info { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.audit-info strong { font-size: 14px; color: var(--color-foreground); }
.biz-id { font-size: 12px; color: var(--color-muted); padding: 2px 8px; border-radius: 4px; background: var(--color-surface-strong); }

.audit-opinion-display { padding: 8px 12px; margin-bottom: 8px; border-radius: var(--radius-sm); background: var(--color-surface-strong); font-size: 13px; color: var(--color-muted); }
.audit-opinion-display span { font-weight: 600; color: var(--color-foreground); margin-right: 4px; }

.audit-actions { display: flex; align-items: center; gap: 8px; }
.opinion-input { flex: 1; min-width: 200px; }

@media (max-width: 800px) {
  .stat-strip { grid-template-columns: repeat(2, 1fr); }
  .audit-actions { flex-wrap: wrap; }
  .opinion-input { min-width: 100%; }
}
</style>
