<script setup lang="ts">
import { computed } from 'vue'
import { Droplets, Snowflake, Thermometer, Wind } from 'lucide-vue-next'
import BaseChart from '@/components/common/BaseChart.vue'
import type { DashboardData } from '@/types'
import { useAppStore } from '@/stores/app'

const props = defineProps<{ environment: DashboardData['environment'] }>()
const appStore = useAppStore()
const valid = computed(() => props.environment.valid !== false)
const isCritical = computed(() => valid.value && (props.environment.temperature >= 9 || props.environment.humidity >= 96))
const isWarning = computed(() => valid.value && (isCritical.value || props.environment.temperature >= 7 || props.environment.humidity >= 94 || props.environment.temperatureState === 'warning' || props.environment.humidityState === 'warning'))
const statusLabel = computed(() => !valid.value ? '等待采样' : isCritical.value ? '严重异常' : isWarning.value ? '环境异常' : '数据正常')
const statusClass = computed(() => !valid.value || isWarning.value ? 'is-warning' : 'is-online')
const gaugeColor = computed(() => isCritical.value ? '#ef4444' : isWarning.value ? '#f59e0b' : '#38bdf8')
const temperatureStability = computed(() => {
  const values = props.environment.trend.map((item) => item.temperature)
  if (values.length < 2) return null
  const average = values.reduce((sum, value) => sum + value, 0) / values.length
  const stddev = Math.sqrt(values.reduce((sum, value) => sum + (value - average) ** 2, 0) / values.length)
  return Math.max(0, Math.round(100 - stddev * 25))
})
const gaugeMax = computed(() => Math.max(35, Math.ceil(props.environment.temperature / 5) * 5))

const gaugeOption = computed(() => {
  const dark = appStore.isDark
  const scale = gaugeMax.value
  const offset = 2
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
        max: gaugeMax.value,
        splitNumber: 6,
        axisLine: {
          lineStyle: {
            width: 9,
            color: [
              [(2 + offset) / (scale + offset), '#38bdf8'],
              [(5 + offset) / (scale + offset), '#22c55e'],
              [(8 + offset) / (scale + offset), '#f59e0b'],
              [1, '#ef4444'],
            ],
          },
        },
        progress: { show: true, width: 9, itemStyle: { color: gaugeColor.value, shadowBlur: 10, shadowColor: gaugeColor.value } },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: {
          valueAnimation: true,
          formatter: (value: number) => `${Number(value).toFixed(1)}°C`,
          color: dark ? '#f4f8ff' : '#16263d',
          fontSize: 25,
          fontWeight: 700,
          offsetCenter: [0, '8%'],
        },
        data: [{ value: valid.value ? Number(props.environment.temperature.toFixed(1)) : 0 }],
      },
    ],
  }
})

const trendOption = computed(() => ({
  animationDuration: 900,
  grid: { top: 12, right: 4, bottom: 4, left: 4 },
  xAxis: { type: 'category', show: false, data: props.environment.trend.map((item) => item.time) },
  yAxis: { type: 'value', show: false, scale: true },
  series: [{
    type: 'line',
    data: props.environment.trend.map((item) => item.temperature),
    smooth: true,
    showSymbol: props.environment.trend.length === 1,
    symbol: 'circle',
    symbolSize: 7,
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
        <p class="section-subtitle">SHT3x · I2C0 / 0x44</p>
      </div>
      <span :class="['status-chip', statusClass]"><span class="realtime-dot" />{{ statusLabel }}</span>
    </header>

    <div class="temperature-gauge">
      <BaseChart v-if="valid" :option="gaugeOption" height="150px" />
      <div v-else class="environment-empty">暂无 SHT3x 采样</div>
      <div class="gauge-caption"><Snowflake :size="13" />冷藏室温度</div>
    </div>

    <div class="environment-values">
      <div class="env-value">
        <div class="env-icon is-temp"><Thermometer :size="17" /></div>
        <div><span>实时温度</span><strong>{{ valid ? environment.temperature.toFixed(1) : '--' }}<small>°C</small></strong></div>
      </div>
      <div class="env-value">
        <div class="env-icon is-humidity"><Droplets :size="17" /></div>
        <div><span>实时湿度</span><strong>{{ valid ? environment.humidity.toFixed(0) : '--' }}<small>%RH</small></strong></div>
      </div>
    </div>

    <div class="mini-trend">
      <div class="mini-trend__head"><span><Wind :size="13" />最近 {{ environment.trend.length }} 次采样</span><b>{{ temperatureStability === null ? '等待更多采样' : `温度稳定度 ${temperatureStability}%` }}</b></div>
      <BaseChart v-if="environment.trend.length" :option="trendOption" height="70px" />
      <div v-else class="trend-empty">暂无历史数据</div>
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
.environment-empty { display: grid; height: 150px; place-items: center; color: var(--text-3); font-size: 10px; }
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
.trend-empty { display: grid; height: 70px; place-items: center; color: var(--text-3); font-size: 9px; }
.environment-range { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: auto; padding-top: 11px; color: var(--text-3); font-size: 9px; }
.environment-range strong { color: var(--text-2); font-size: 10px; }
@media (max-width: 1100px) { .temperature-gauge { display: none; } }
</style>
