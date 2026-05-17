<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { animate, stagger, createTimeline } from 'animejs'
import { api } from '../api/client'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const form = reactive({ username: '', password: '' })
const particleContainer = ref<HTMLDivElement>()

async function login() {
  if (!form.username.trim() || !form.password) {
    error.value = '请输入系统分配的用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await api.login(form.username, form.password)
    localStorage.setItem('pcr_token', res.access_token)
    localStorage.setItem('pcr_user', JSON.stringify(res.user))
    router.push('/')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '登录失败'
  } finally {
    loading.value = false
  }
}

function createParticles() {
  const container = particleContainer.value
  if (!container) return
  for (let i = 0; i < 24; i++) {
    const el = document.createElement('div')
    el.className = 'particle'
    el.style.left = `${Math.random() * 100}%`
    el.style.top = `${Math.random() * 100}%`
    el.style.width = el.style.height = `${2 + Math.random() * 4}px`
    el.style.opacity = `${0.15 + Math.random() * 0.25}`
    container.appendChild(el)
  }
  animate('.particle', {
    translateY: () => `${-30 + Math.random() * 60}px`,
    translateX: () => `${-20 + Math.random() * 40}px`,
    opacity: [
      { to: () => 0.1 + Math.random() * 0.3, duration: 2000 },
      { to: () => 0.05 + Math.random() * 0.15, duration: 2000 },
    ],
    duration: () => 3000 + Math.random() * 4000,
    loop: true,
    alternate: true,
    ease: 'inOutSine',
    delay: () => Math.random() * 2000,
  })
}

onMounted(() => {
  createParticles()
  const tl = createTimeline({
    defaults: { ease: 'outCubic', duration: 600 },
  })
  tl.add('.brand-icon', { opacity: { from: 0, to: 1 }, scale: { from: 0.5, to: 1 }, rotate: { from: -90, to: 0 }, duration: 700 }, 0)
  tl.add('.title-block .subtitle', { opacity: { from: 0, to: 1 }, x: { from: -30, to: 0 } }, 200)
  tl.add('.title-block h1', { opacity: { from: 0, to: 1 }, y: { from: 20, to: 0 } }, 300)
  tl.add('.version-tag', { opacity: { from: 0, to: 1 } }, 500)
  tl.add('.title-block .disclaimer', { opacity: { from: 0, to: 1 }, y: { from: 10, to: 0 } }, 600)
  tl.add('.login-panel', { opacity: { from: 0, to: 1 }, x: { from: 40, to: 0 }, scale: { from: 0.95, to: 1 }, duration: 700 }, 200)
  tl.add('.role-card', { opacity: { from: 0, to: 1 }, x: { from: 20, to: 0 }, scale: { from: 0.92, to: 1 }, delay: stagger(80) }, 600)
})
</script>

<template>
  <main class="login-page">
    <div ref="particleContainer" class="particles"></div>
    <section class="login-block title-block">
      <div class="brand-icon">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="22" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
          <circle cx="24" cy="24" r="14" stroke="rgba(147,197,253,0.6)" stroke-width="2"/>
          <circle cx="24" cy="24" r="6" fill="rgba(147,197,253,0.5)"/>
          <path d="M24 2 L24 14 M24 34 L24 46 M2 24 L14 24 M34 24 L46 24" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
        </svg>
      </div>
      <p class="subtitle">乳腺MRI影像与临床病理数据</p>
      <h1>辅助分析系统</h1>
      <p class="version-tag">v0.1.0 · 课程级医学AI工作台</p>
      <div class="disclaimer">仅用于课程项目辅助分析展示，不作为真实临床诊断依据。</div>
    </section>
    <section class="login-block login-panel">
      <h2>系统登录</h2>
      <el-form label-position="top" @submit.prevent="login">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" placeholder="请输入用户名" size="large" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="current-password" show-password placeholder="请输入密码" size="large" @keyup.enter="login" />
        </el-form-item>
        <el-alert v-if="error" type="error" :title="error" :closable="false" />
        <el-button class="login-button" type="primary" :loading="loading" size="large" @click="login">
          {{ loading ? '验证中…' : '登录系统' }}
        </el-button>
      </el-form>
      <div class="role-cards">
        <div class="role-card role-doctor">
          <strong>👨‍⚕️ 医生</strong>
          <span>数据录入 · 影像上传 · ROI标注 · 分析发起</span>
        </div>
        <div class="role-card role-dept">
          <strong>📋 科室管理员</strong>
          <span>数据审核 · 质量管理 · 统计查看</span>
        </div>
        <div class="role-card role-sys">
          <strong>⚙️ 系统管理员</strong>
          <span>账号创建 · 角色权限分配</span>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.1fr 440px;
  align-items: center;
  gap: 48px;
  padding: 56px;
  background:
    radial-gradient(circle at 20% 30%, rgba(30, 64, 175, 0.3), transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(14, 116, 144, 0.2), transparent 40%),
    linear-gradient(135deg, #0a1628 0%, #0f2645 40%, #0c3558 100%);
  overflow: hidden;
}

.particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

:deep(.particle) {
  position: absolute;
  border-radius: 50%;
  background: rgba(147, 197, 253, 0.4);
  pointer-events: none;
}

.title-block {
  position: relative;
  z-index: 1;
  color: #fff;
  max-width: 680px;
}

.brand-icon {
  margin-bottom: 24px;
  opacity: 0.85;
}

.subtitle {
  margin: 0 0 8px;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 0.02em;
}

.title-block h1 {
  margin: 0 0 16px;
  font-size: 44px;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #ffffff 30%, #93c5fd 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.version-tag {
  margin: 0 0 24px;
  font-size: 13px;
  color: rgba(147, 197, 253, 0.6);
  font-weight: 500;
}

.title-block .disclaimer {
  background: rgba(255, 247, 230, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.2);
  color: rgba(251, 191, 36, 0.85);
  backdrop-filter: blur(8px);
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
}

.login-panel {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(24px) saturate(1.4);
  -webkit-backdrop-filter: blur(24px) saturate(1.4);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.login-panel h2 {
  margin: 0 0 20px;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}

.login-panel :deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.75);
  font-weight: 500;
}

.login-panel :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: none;
  transition: border-color 200ms ease, background 200ms ease;
}

.login-panel :deep(.el-input__wrapper:hover),
.login-panel :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(147, 197, 253, 0.5);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.login-panel :deep(.el-input__inner) {
  color: #fff;
}

.login-panel :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.35);
}

.login-button {
  width: 100%;
  margin-top: 8px;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border: none;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35);
  transition: box-shadow 250ms ease, transform 150ms ease;
}

.login-button:hover {
  box-shadow: 0 6px 24px rgba(37, 99, 235, 0.45);
  transform: translateY(-1px);
}

.role-cards {
  display: grid;
  gap: 8px;
  margin-top: 20px;
}

.role-card {
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: background 200ms ease, border-color 200ms ease, transform 200ms var(--ease-spring);
}

.role-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(147, 197, 253, 0.2);
  transform: translateX(4px);
}

.role-card strong {
  display: block;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.role-card span {
  display: block;
  margin-top: 2px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
    padding: 24px;
    gap: 32px;
  }
  .title-block h1 {
    font-size: 32px;
  }
  .login-panel {
    padding: 24px;
  }
}
</style>
