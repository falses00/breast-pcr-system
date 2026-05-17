<script setup lang="ts">
defineProps<{ title?: string }>()
</script>

<template>
  <div class="glass-card">
    <h4 v-if="title" class="glass-card-title">{{ title }}</h4>
    <slot />
  </div>
</template>

<style scoped>
.glass-card {
  background: var(--color-surface-glass);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 18px;
  box-shadow: var(--shadow-sm);
  transition: transform var(--duration-normal) var(--ease-spring), box-shadow var(--duration-normal) var(--ease-out);
}

.glass-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.glass-card-title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-foreground);
}
</style>
