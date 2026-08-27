<script setup lang="ts">
import { computed } from 'vue'
import { Activity, Radio } from 'lucide-vue-next'
import BaseChart from '@/components/common/BaseChart.vue'
import { useAppStore } from '@/stores/app'

const props = defineProps<{ data: Array<{ time: string; inbound: number; outbound: number }> }>()
const appStore = useAppStore()
const option = computed(() => {
  const axis = appStore.isDark ? 'rgba(148,163,184,.2)' : 'rgba(100,116,139,.2)'
  const text = appStore.isDark ? '#70829a' : '#7b8ca3'
  return {
    animationDuration: 1000,
    grid: { top: 24, right: 10, bottom: 20, left: 30 },
    tooltip: { trigger: 'axis', backgroundColor: appStore.isDark ? 'rgba(12,25,43,.94)' : 'rgba(255,255,255,.96)', borderColor: axis, textStyle: { color: appStore.isDark ? '#f4f8ff' : '#16263d', fontSize: 10 } },
    legend: { top: 0, right: 0, itemWidth: 9, itemHeight: 5, textStyle: { color: text, fontSize: 9 }, data: ['入库', '出库'] },
    xAxis: { type: 'category', boundaryGap: false, data: props.data.map((item) => item.time), axisLine: { lineStyle: { color: axis } }, axisTick: { show: false }, axisLabel: { color: text, fontSize: 8, interval: 2 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: axis, type: 'dashed' } }, axisLabel: { color: text, fontSize: 8 } },
    series: [
      { name: '入库', type: 'line', smooth: true, showSymbol: false, data: props.data.map((item) => item.inbound), lineStyle: { width: 2, color: '#38bdf8' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(56,189,248,.35)' }, { offset: 1, color: 'rgba(56,189,248,0)' }] } } },
      { name: '出库', type: 'line', smooth: true, showSymbol: false, data: props.data.map((item) => item.outbound), lineStyle: { width: 2, color: '#22c55e' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(34,197,94,.24)' }, { offset: 1, color: 'rgba(34,197,94,0)' }] } } },
    ],
  }
})
</script>

<template>
  <section class="trend-panel glass-panel">
    <header class="trend-header">
      <div>
        <h2 class="section-title">入库 / 出库趋势</h2>
        <p class="section-subtitle">过去 24 小时 · 动态刷新</p>
      </div>
      <span class="live-label"><Radio :size="12" /> LIVE</span>
    </header>
    <div class="trend-body">
      <BaseChart :option="option" height="128px" />
      <div class="trend-insight">
        <div class="insight-icon"><Activity :size="17" /></div>
        <div><span>今日净流入</span><strong>+11 件</strong><small>较昨日提升 8.4%</small></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.trend-panel { min-width: 0; padding: 15px 17px; }
.trend-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.live-label { display: flex; align-items: center; gap: 4px; color: #7de6ff; font-size: 8px; letter-spacing: .1em; }
.trend-body { display: grid; grid-template-columns: minmax(0, 1fr) 104px; align-items: center; gap: 8px; }
.trend-insight { padding: 10px; border-left: 1px solid var(--stroke); }
.insight-icon { display: grid; width: 32px; height: 32px; place-items: center; border-radius: 10px; color: var(--cyan); background: rgba(56,189,248,.1); }
.trend-insight span, .trend-insight strong, .trend-insight small { display: block; }
.trend-insight span { margin-top: 9px; color: var(--text-3); font-size: 8px; }
.trend-insight strong { margin-top: 4px; color: #83e8ff; font-size: 15px; }
.trend-insight small { margin-top: 4px; color: var(--text-3); font-size: 8px; }
@media (max-width: 900px) { .trend-insight { display: none; } .trend-body { grid-template-columns: 1fr; } }
</style>
