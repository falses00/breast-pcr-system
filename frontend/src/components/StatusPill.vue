<script setup lang="ts">
defineProps<{ value?: string }>()
</script>

<template>
  <span class="status-pill" :class="`status-${value || 'default'}`">{{ value || '未知' }}</span>
</template>
