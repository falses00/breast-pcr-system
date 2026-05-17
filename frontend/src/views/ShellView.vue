<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DataAnalysis,
  DocumentChecked,
  Files,
  HomeFilled,
  Picture,
  User,
  UserFilled,
} from '@element-plus/icons-vue'
import { roleProfiles, routeRoles } from '../rolePolicy'

const router = useRouter()
const route = useRoute()
const user = computed(() => JSON.parse(localStorage.getItem('pcr_user') || '{}'))
const activePath = computed(() => route.path)
const roleProfile = computed(() => roleProfiles[user.value.role as keyof typeof roleProfiles])
const menuItems = computed(() => {
  const role = user.value.role
  const items = [
    { path: '/', label: '仪表盘', icon: HomeFilled, roles: routeRoles.dashboard },
    { path: '/patients', label: '患者管理', icon: Files, roles: routeRoles.patients },
    { path: '/imaging', label: '影像与ROI', icon: Picture, roles: routeRoles.imaging },
    { path: '/analysis', label: '分析任务', icon: DataAnalysis, roles: routeRoles.analysis },
    { path: '/audit', label: '审核管理', icon: DocumentChecked, roles: routeRoles.audit },
    { path: '/users', label: '用户管理', icon: User, roles: routeRoles.users },
  ]
  return items.filter((item) => item.roles.includes(role))
})

function logout() {
  localStorage.removeItem('pcr_token')
  localStorage.removeItem('pcr_user')
  router.push('/login')
}
</script>

<template>
  <el-container class="shell">
    <el-aside width="250px" class="aside">
      <div class="brand">
        <div class="brand-mark">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="rgba(147,197,253,0.6)" stroke-width="1.5"/>
            <circle cx="12" cy="12" r="5" fill="rgba(147,197,253,0.35)"/>
            <path d="M12 2v6M12 16v6M2 12h6M16 12h6" stroke="rgba(147,197,253,0.3)" stroke-width="1"/>
          </svg>
        </div>
        <div>
          <strong>乳腺MRI辅助分析</strong>
          <span>Clinical AI Workbench</span>
        </div>
      </div>
      <nav class="nav-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: activePath === item.path }"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
          <div class="nav-indicator"></div>
        </router-link>
      </nav>
      <div class="aside-footer">
        <div class="env-badge">
          <span class="env-dot"></span>
          <span>本地开发环境</span>
        </div>
      </div>
    </el-aside>
    <el-container class="main-container">
      <el-header class="header">
        <div class="header-user">
          <div class="avatar">{{ (user.name || '?')[0] }}</div>
          <div>
            <strong>{{ user.name || '系统用户' }}</strong>
            <span class="role-tag">{{ user.role || '未登录' }}</span>
          </div>
        </div>
        <div class="role-scope">
          <strong>{{ roleProfile?.title || '未识别角色' }}</strong>
          <span>{{ roleProfile?.scope || '请重新登录以加载权限' }}</span>
        </div>
        <div class="header-status">
          <span class="status-badge">
            <span class="status-dot status-dot-live"></span>
            35例 / 35张影像
          </span>
          <span class="status-badge warn">课程辅助展示</span>
        </div>
        <el-button :icon="UserFilled" @click="logout">退出</el-button>
      </el-header>
      <el-main class="content">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at 15% 10%, rgba(59, 130, 246, 0.06), transparent 30%),
    radial-gradient(circle at 85% 90%, rgba(14, 116, 144, 0.04), transparent 25%),
    var(--color-background);
}

.aside {
  background: linear-gradient(180deg, #0c1a30, #0f2240);
  border-right: 1px solid rgba(147, 197, 253, 0.08);
  display: flex;
  flex-direction: column;
}

.brand {
  height: 68px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.3), rgba(14, 116, 144, 0.2));
  border: 1px solid rgba(147, 197, 253, 0.15);
}

.brand strong {
  display: block;
  font-size: 14px;
  font-weight: 600;
}

.brand span {
  display: block;
  margin-top: 2px;
  color: rgba(147, 197, 253, 0.5);
  font-size: 11px;
  letter-spacing: 0.03em;
}

/* ── 导航菜单 ── */
.nav-menu {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  color: rgba(203, 213, 225, 0.8);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 200ms ease;
  cursor: pointer;
}

.nav-item:hover {
  color: #fff;
  background: rgba(59, 130, 246, 0.12);
}

.nav-item.active {
  color: #fff;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.25), rgba(14, 116, 144, 0.15));
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.1);
}

.nav-item.active .nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, #3b82f6, #0ea5e9);
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
}

.nav-item .el-icon {
  font-size: 18px;
}

/* ── 侧边栏底部 ── */
.aside-footer {
  padding: 14px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.env-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 12px;
  color: rgba(147, 197, 253, 0.5);
}

.env-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
  animation: pulse-dot 2s ease-in-out infinite;
}

/* ── 顶部 Header ── */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--color-surface-glass);
  backdrop-filter: var(--glass-blur);
  border-bottom: 1px solid var(--color-border);
  padding: 0 20px;
  height: 64px;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2563eb, #0e7490);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: grid;
  place-items: center;
}

.header-user strong {
  display: block;
  font-size: 14px;
  color: var(--color-foreground);
}

.role-tag {
  font-size: 12px;
  color: var(--color-muted);
  font-weight: 500;
}

.role-scope {
  min-width: 200px;
  max-width: 380px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface-glass);
  backdrop-filter: blur(8px);
}

.role-scope strong {
  display: block;
  color: var(--color-foreground);
  font-size: 13px;
  font-weight: 600;
}

.role-scope span {
  display: block;
  margin: 2px 0 0;
  overflow: hidden;
  color: var(--color-muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-status {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-right: 8px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: var(--radius-full);
  background: rgba(239, 246, 255, 0.7);
  backdrop-filter: blur(4px);
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  border: 1px solid rgba(191, 219, 254, 0.3);
}

.status-badge.warn {
  background: rgba(255, 251, 235, 0.7);
  color: #a16207;
  border-color: rgba(253, 230, 138, 0.3);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
}

.status-dot-live {
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
  animation: pulse-dot 2s ease-in-out infinite;
}

.content {
  padding: 20px;
}

@media (max-width: 900px) {
  .shell {
    display: block;
  }

  .aside {
    width: 100% !important;
  }

  .brand {
    height: 56px;
  }

  .nav-menu {
    flex-direction: row;
    overflow-x: auto;
    padding: 8px;
    gap: 4px;
  }

  .nav-item {
    flex: 0 0 auto;
    padding: 8px 12px;
    font-size: 13px;
  }

  .nav-item.active .nav-indicator {
    display: none;
  }

  .aside-footer {
    display: none;
  }

  .header {
    height: auto;
    min-height: 60px;
    flex-wrap: wrap;
    gap: 8px;
    padding: 10px 14px;
  }

  .header-status {
    order: 3;
    width: 100%;
    justify-content: flex-start;
    overflow-x: auto;
    margin-right: 0;
  }

  .role-scope {
    order: 2;
    width: 100%;
    max-width: none;
  }

  .content {
    padding: 14px;
  }
}
</style>
