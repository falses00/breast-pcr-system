<script setup lang="ts">
defineProps<{
  type?: 'text' | 'card' | 'chart' | 'table'
  lines?: number
}>()
</script>

<template>
  <div class="skeleton-wrapper">
    <template v-if="type === 'chart'">
      <div class="skeleton skeleton-chart"></div>
    </template>
    <template v-else-if="type === 'card'">
      <div class="skeleton skeleton-card"></div>
    </template>
    <template v-else-if="type === 'table'">
      <div v-for="i in (lines || 5)" :key="i" class="skeleton skeleton-text" :style="{ width: `${60 + Math.random() * 40}%` }"></div>
    </template>
    <template v-else>
      <div v-for="i in (lines || 3)" :key="i" class="skeleton skeleton-text" :style="{ width: `${50 + Math.random() * 50}%` }"></div>
    </template>
  </div>
</template>

<style scoped>
.skeleton-wrapper {
  display: grid;
  gap: 8px;
}
</style>
