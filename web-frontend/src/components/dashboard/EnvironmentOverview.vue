<script setup lang="ts">
import { computed } from 'vue'
import { Droplets, Snowflake, Thermometer, Wind } from 'lucide-vue-next'
import BaseChart from '@/components/common/BaseChart.vue'
import type { DashboardData } from '@/types'
import { useAppStore } from '@/stores/app'

const props = defineProps<{ environment: DashboardData['environment'] }>()
const appStore = useAppStore()

const gaugeOption = computed(() => {
  const dark = appStore.isDark
  return {
    animationDuration: 900,
    series: [
      {
        type: 'gauge',
        center: ['50%', '58%'],
        radius: '92%',
        startAngle: 210,
        endAngle: -30,
        min: -2,
        max: 10,
        splitNumber: 6,
        axisLine: {
          lineStyle: {
            width: 9,
            color: [[0.42, '#38bdf8'], [0.7, '#22c55e'], [1, '#f59e0b']],
          },
        },
        progress: { show: true, width: 9, itemStyle: { color: '#e7fbff', shadowBlur: 10, shadowColor: '#38bdf8' } },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { length: 6, lineStyle: { color: dark ? 'rgba(255,255,255,.25)' : 'rgba(15,23,42,.25)', width: 1 } },
        axisLabel: { distance: 14, color: dark ? '#70829a' : '#7b8ca3', fontSize: 8 },
        detail: {
          valueAnimation: true,
          formatter: '{value}°',
          color: dark ? '#f4f8ff' : '#16263d',
          fontSize: 25,
          fontWeight: 700,
          offsetCenter: [0, '8%'],
        },
        data: [{ value: props.environment.temperature }],
      },
    ],
  }
})

const trendOption = computed(() => ({
  animationDuration: 900,
  grid: { top: 12, right: 4, bottom: 4, left: 4 },
  xAxis: { type: 'category', show: false, data: props.environment.trend.map((item) => item.time) },
  yAxis: { type: 'value', show: false, min: 2.5, max: 5 },
  series: [{
    type: 'line',
    data: props.environment.trend.map((item) => item.temperature),
    smooth: true,
    showSymbol: false,
    lineStyle: { width: 2, color: '#38bdf8' },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(56,189,248,.38)' }, { offset: 1, color: 'rgba(56,189,248,0)' }],
      },
    },
  }],
}))
</script>

<template>
  <section class="environment-card glass-panel">
    <header class="panel-heading">
      <div>
        <h2 class="section-title">实时环境监测</h2>
        <p class="section-subtitle">SHT30 · I2C3 / 0x44</p>
      </div>
      <span class="status-chip is-online"><span class="realtime-dot" />数据正常</span>
    </header>

    <div class="temperature-gauge">
      <BaseChart :option="gaugeOption" height="150px" />
      <div class="gauge-caption"><Snowflake :size="13" />冷藏室温度</div>
    </div>

    <div class="environment-values">
      <div class="env-value">
        <div class="env-icon is-temp"><Thermometer :size="17" /></div>
        <div><span>实时温度</span><strong>{{ environment.temperature.toFixed(1) }}<small>°C</small></strong></div>
      </div>
      <div class="env-value">
        <div class="env-icon is-humidity"><Droplets :size="17" /></div>
        <div><span>实时湿度</span><strong>{{ environment.humidity.toFixed(0) }}<small>%RH</small></strong></div>
      </div>
    </div>

    <div class="mini-trend">
      <div class="mini-trend__head"><span><Wind :size="13" />过去 4 小时</span><b>环境稳定度 96.8%</b></div>
      <BaseChart :option="trendOption" height="70px" />
    </div>

    <div class="environment-range">
      <span>建议储存区间</span>
      <strong>2-5°C · 85-95%RH</strong>
    </div>
  </section>
</template>

<style scoped>
.environment-card { display: flex; min-height: 0; flex-direction: column; padding: 16px; }
.panel-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.temperature-gauge { position: relative; margin-top: 2px; }
.gauge-caption { position: absolute; bottom: 13px; left: 50%; display: flex; align-items: center; gap: 5px; color: var(--text-3); font-size: 9px; transform: translateX(-50%); white-space: nowrap; }
.environment-values { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.env-value { display: flex; min-width: 0; align-items: center; gap: 9px; padding: 10px; border: 1px solid var(--stroke); border-radius: 12px; background: var(--surface-soft); }
.env-icon { display: grid; width: 31px; height: 31px; flex: 0 0 auto; place-items: center; border-radius: 9px; }
.env-icon.is-temp { color: var(--cyan); background: rgba(56,189,248,.1); }
.env-icon.is-humidity { color: var(--teal); background: rgba(20,184,166,.1); }
.env-value span { display: block; color: var(--text-3); font-size: 9px; }
.env-value strong { display: block; margin-top: 3px; color: var(--text-1); font-size: 17px; }
.env-value small { margin-left: 3px; color: var(--text-3); font-size: 8px; font-weight: 500; }
.mini-trend { margin-top: 11px; padding: 10px 9px 2px; border-radius: 12px; background: rgba(56,189,248,.04); }
.mini-trend__head { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: var(--text-3); font-size: 9px; }
.mini-trend__head span { display: flex; align-items: center; gap: 5px; }
.mini-trend__head b { color: #8fe9ff; font-weight: 600; }
.environment-range { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: auto; padding-top: 11px; color: var(--text-3); font-size: 9px; }
.environment-range strong { color: var(--text-2); font-size: 10px; }
@media (max-width: 1100px) { .temperature-gauge { display: none; } }
</style>
