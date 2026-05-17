<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createTimeline, stagger } from 'animejs'
import { api } from '../api/client'
import type { UserRecord } from '../api/types'
import PageHeader from '../components/PageHeader.vue'
import StatusPill from '../components/StatusPill.vue'

const users = ref<UserRecord[]>([])
const form = reactive({ username: '', password: '123456', name: '', role: '医生', department: '乳腺科' })
const editVisible = ref(false)
const editForm = reactive({ id: 0, name: '', role: '', department: '', is_active: true })

// 统计指标
const totalCount = computed(() => users.value.length)
const doctorCount = computed(() => users.value.filter(u => u.role === '医生').length)
const managerCount = computed(() => users.value.filter(u => u.role === '科室管理员').length)
const disabledCount = computed(() => users.value.filter(u => !u.is_active).length)

async function load() {
  users.value = await api.users()
}

async function createUser() {
  if (!form.username.trim() || !form.name.trim()) return ElMessage.warning('请填写用户名和姓名')
  await api.createUser(form)
  ElMessage.success('账号已创建')
  form.username = ''; form.name = ''
  await load()
}

function openEdit(user: UserRecord) {
  editForm.id = user.id
  editForm.name = user.name
  editForm.role = user.role
  editForm.department = user.department || '乳腺科'
  editForm.is_active = user.is_active !== false
  editVisible.value = true
}

async function saveEdit() {
  await api.updateUser(editForm.id, {
    name: editForm.name,
    role: editForm.role,
    department: editForm.department,
    is_active: editForm.is_active,
  })
  ElMessage.success('用户信息已更新')
  editVisible.value = false
  await load()
}

async function toggleActive(user: UserRecord) {
  const action = user.is_active ? '禁用' : '启用'
  await ElMessageBox.confirm(`确定${action}用户 "${user.name}" 吗？`, '操作确认', { type: 'warning' })
  await api.updateUser(user.id, { is_active: !user.is_active })
  ElMessage.success(`已${action}`)
  await load()
}

async function resetPassword(user: UserRecord) {
  await ElMessageBox.confirm(`确定将 "${user.name}" 的密码重置为 "123456" 吗？`, '密码重置', { type: 'warning' })
  await api.updateUser(user.id, { password: '123456' })
  ElMessage.success('密码已重置为 123456')
}

onMounted(async () => {
  await load()
  const tl = createTimeline({ defaults: { ease: 'outCubic', duration: 400 } })
  tl.add('.page-header', { opacity: { from: 0, to: 1 }, y: { from: -12, to: 0 } }, 0)
  tl.add('.stat-card', { opacity: { from: 0, to: 1 }, y: { from: 16, to: 0 }, scale: { from: 0.95, to: 1 }, delay: stagger(60, { from: 'center' }) }, 100)
  tl.add('.panel', { opacity: { from: 0, to: 1 }, y: { from: 16, to: 0 }, delay: stagger(80) }, 350)
})
</script>

<template>
  <section class="page">
    <PageHeader
      eyebrow="RBAC ADMIN"
      title="用户与角色权限管理"
      subtitle="系统管理员维护医生、科室管理员、系统管理员账号。支持创建、编辑、禁用和密码重置。"
    />

    <!-- 统计指标 -->
    <div class="stat-strip">
      <div class="stat-card"><span>用户总数</span><strong>{{ totalCount }}</strong><em>所有角色</em></div>
      <div class="stat-card"><span>医生账号</span><strong>{{ doctorCount }}</strong><em>核心业务角色</em></div>
      <div class="stat-card"><span>科室管理员</span><strong>{{ managerCount }}</strong><em>数据审核角色</em></div>
      <div class="stat-card"><span>已禁用</span><strong>{{ disabledCount }}</strong><em>无法登录系统</em></div>
    </div>

    <div class="grid">
      <!-- 用户列表 -->
      <div class="panel">
        <h3>用户列表</h3>
        <el-table :data="users" height="520" highlight-current-row>
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column label="角色" width="120">
            <template #default="{ row }">
              <StatusPill :value="row.role" />
            </template>
          </el-table-column>
          <el-table-column prop="department" label="科室" width="100" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <span class="status-dot" :class="{ active: row.is_active !== false, disabled: row.is_active === false }">
                {{ row.is_active !== false ? '启用' : '禁用' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" :type="row.is_active !== false ? 'warning' : 'success'" @click="toggleActive(row)">
                {{ row.is_active !== false ? '禁用' : '启用' }}
              </el-button>
              <el-button size="small" @click="resetPassword(row)">重置密码</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 新增账号 -->
      <div class="panel">
        <h3>新增账号</h3>
        <el-form label-position="top">
          <el-form-item label="用户名"><el-input v-model="form.username" placeholder="如 doctor_wang" /></el-form-item>
          <el-form-item label="初始密码"><el-input v-model="form.password" show-password /></el-form-item>
          <el-form-item label="姓名"><el-input v-model="form.name" placeholder="王医生" /></el-form-item>
          <el-form-item label="角色">
            <el-select v-model="form.role" class="full-control">
              <el-option label="医生" value="医生" />
              <el-option label="科室管理员" value="科室管理员" />
              <el-option label="系统管理员" value="系统管理员" />
            </el-select>
          </el-form-item>
          <el-form-item label="科室"><el-input v-model="form.department" placeholder="乳腺科" /></el-form-item>
          <el-button type="primary" class="full-btn" @click="createUser">创建账号</el-button>
        </el-form>

        <div class="help-card">
          <h4>权限说明</h4>
          <ul>
            <li><strong>医生</strong>：患者建档、影像上传、ROI标注、发起pCR分析</li>
            <li><strong>科室管理员</strong>：审核医生提交的数据和分析结果</li>
            <li><strong>系统管理员</strong>：用户账号创建、编辑、禁用、密码重置</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑用户信息" width="480px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="姓名"><el-input v-model="editForm.name" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" class="full-control">
            <el-option label="医生" value="医生" />
            <el-option label="科室管理员" value="科室管理员" />
            <el-option label="系统管理员" value="系统管理员" />
          </el-select>
        </el-form-item>
        <el-form-item label="科室"><el-input v-model="editForm.department" /></el-form-item>
        <el-form-item label="账号状态">
          <el-switch v-model="editForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.stat-strip { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; }
.stat-card { padding: 14px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-glass); backdrop-filter: blur(8px); box-shadow: var(--shadow-sm); }
.stat-card span, .stat-card em { display: block; color: var(--color-muted); font-size: 13px; font-style: normal; }
.stat-card strong { display: block; margin: 6px 0; color: var(--color-foreground); font-size: 20px; font-weight: 700; }
.grid { display: grid; grid-template-columns: 1fr 380px; gap: 16px; }
.full-btn { width: 100%; margin-top: 4px; }
.full-control { width: 100%; }
.status-dot { font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: var(--radius-full); }
.status-dot.active { color: #059669; background: rgba(5,150,105,0.1); }
.status-dot.disabled { color: #dc2626; background: rgba(220,38,38,0.1); }
.help-card { margin-top: 20px; padding: 14px; border-radius: var(--radius-sm); background: var(--color-surface-strong); border: 1px solid var(--color-border); }
.help-card h4 { margin: 0 0 8px; font-size: 13px; color: var(--color-primary); }
.help-card ul { margin: 0; padding-left: 18px; }
.help-card li { font-size: 12px; color: var(--color-muted); line-height: 1.8; }
.help-card li strong { color: var(--color-foreground); }
@media (max-width: 1000px) { .grid { grid-template-columns: 1fr; } .stat-strip { grid-template-columns: repeat(2, 1fr); } }
</style>
