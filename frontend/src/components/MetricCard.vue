<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  hint?: string
  tone?: 'blue' | 'green' | 'amber' | 'red'
}>()
</script>

<template>
  <div class="metric-card" :class="`metric-${tone || 'blue'}`">
    <div class="metric-top">
      <span>{{ label }}</span>
      <i />
    </div>
    <strong><slot name="value">{{ value }}</slot></strong>
    <p v-if="hint">{{ hint }}</p>
  </div>
</template>
