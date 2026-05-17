<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { animate } from 'animejs'

const props = defineProps<{
  value: number | string
  duration?: number
  decimals?: number
  prefix?: string
  suffix?: string
}>()

const display = ref('0')

function animateValue(target: number) {
  const obj = { val: 0 }
  animate(obj, {
    val: target,
    duration: props.duration || 800,
    ease: 'outExpo',
    onUpdate: () => {
      const d = props.decimals ?? 0
      display.value = d > 0 ? obj.val.toFixed(d) : Math.round(obj.val).toString()
    },
  })
}

onMounted(() => {
  const num = typeof props.value === 'number' ? props.value : parseFloat(props.value)
  if (!isNaN(num)) animateValue(num)
  else display.value = String(props.value)
})

watch(() => props.value, (newVal) => {
  const num = typeof newVal === 'number' ? newVal : parseFloat(newVal)
  if (!isNaN(num)) animateValue(num)
  else display.value = String(newVal)
})
</script>

<template>
  <span class="count-up">{{ prefix }}{{ display }}{{ suffix }}</span>
</template>

<style scoped>
.count-up {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}
</style>
