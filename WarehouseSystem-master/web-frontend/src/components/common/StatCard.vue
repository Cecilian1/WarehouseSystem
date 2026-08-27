<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowDownRight, ArrowUpRight, Boxes, CircleAlert, Leaf, PackagePlus } from 'lucide-vue-next'
import type { MetricItem } from '@/types'

const props = defineProps<{ metric: MetricItem }>()
const displayValue = ref(0)
let animationFrame = 0

const iconMap = { stock: Boxes, today: PackagePlus, expiring: Leaf, alerts: CircleAlert }
const Icon = computed(() => iconMap[props.metric.id as keyof typeof iconMap] || Boxes)

const animateValue = (target: number) => {
  cancelAnimationFrame(animationFrame)
  const start = displayValue.value
  const startedAt = performance.now()
  const step = (time: number) => {
    const progress = Math.min((time - startedAt) / 800, 1)
    displayValue.value = Math.round(start + (target - start) * (1 - Math.pow(1 - progress, 3)))
    if (progress < 1) animationFrame = requestAnimationFrame(step)
  }
  animationFrame = requestAnimationFrame(step)
}

watch(() => props.metric.value, animateValue, { immediate: true })
</script>

<template>
  <article class="stat-card glass-panel panel-hover" :class="`stat-card--${metric.tone}`">
    <div class="stat-card__top">
      <div class="stat-icon"><component :is="Icon" :size="18" /></div>
      <span :class="['change', metric.change >= 0 ? 'is-up' : 'is-down']">
        <ArrowUpRight v-if="metric.change >= 0" :size="14" />
        <ArrowDownRight v-else :size="14" />
        {{ Math.abs(metric.change).toFixed(1) }}%
      </span>
    </div>
    <div class="stat-card__value">{{ displayValue }}<small>{{ metric.unit }}</small></div>
    <div class="stat-card__label">{{ metric.label }}</div>
    <div class="stat-card__line"><span /></div>
  </article>
</template>

<style scoped>
.stat-card {
  min-height: 124px;
  padding: 16px 18px;
  overflow: hidden;
}
.stat-card__top, .stat-card__value { display: flex; align-items: center; justify-content: space-between; }
.stat-icon {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 11px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 14%, transparent);
}
.change { display: inline-flex; align-items: center; gap: 1px; font-size: 11px; }
.is-up { color: var(--green); }
.is-down { color: var(--red); }
.stat-card__value { justify-content: flex-start; gap: 6px; margin-top: 15px; font-size: 29px; font-weight: 720; letter-spacing: -0.03em; }
.stat-card__value small { color: var(--text-3); font-size: 12px; font-weight: 500; letter-spacing: 0; }
.stat-card__label { margin-top: 4px; color: var(--text-2); font-size: 12px; }
.stat-card__line { height: 3px; margin-top: 14px; overflow: hidden; border-radius: 99px; background: rgba(255, 255, 255, 0.08); }
.stat-card__line span { display: block; width: 64%; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--accent), transparent); }
.stat-card--blue { --accent: var(--blue); }
.stat-card--cyan { --accent: var(--cyan); }
.stat-card--green { --accent: var(--green); }
.stat-card--orange { --accent: var(--orange); }
.stat-card--red { --accent: var(--red); }
.stat-card--purple { --accent: var(--purple); }
</style>
