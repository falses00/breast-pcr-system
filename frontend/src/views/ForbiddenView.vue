<script setup lang="ts">
import { computed } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import { roleProfiles } from '../rolePolicy'

const user = computed(() => JSON.parse(localStorage.getItem('pcr_user') || '{}'))
const profile = computed(() => roleProfiles[user.value.role as keyof typeof roleProfiles])
</script>

<template>
  <section class="page">
    <PageHeader
      eyebrow="ACCESS CONTROL"
      title="无权访问该功能"
      subtitle="当前账号角色没有进入该页面的权限。系统会同时在前端路由和后端接口执行RBAC校验。"
    >
      <el-button type="primary" @click="$router.push('/')">返回仪表盘</el-button>
    </PageHeader>
    <div class="panel forbidden-panel">
      <strong>{{ user.name || '当前用户' }}</strong>
      <p>当前角色：{{ user.role || '未知' }}</p>
      <p>角色职责：{{ profile?.scope || '未加载' }}</p>
      <p>系统已启用前端路由级权限约束；后端接口仍会继续执行角色校验，避免绕过页面直接调用接口。</p>
    </div>
  </section>
</template>

<style scoped>
.forbidden-panel {
  max-width: 720px;
}

.forbidden-panel strong {
  display: block;
  color: #0f2f5c;
  font-size: 20px;
}

.forbidden-panel p {
  margin: 10px 0 0;
  color: #64748b;
  line-height: 1.7;
}
</style>
