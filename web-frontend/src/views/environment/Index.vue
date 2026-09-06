<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { Activity, BellRing, Droplets, Gauge, Settings2, Thermometer, Waves } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import { environmentApi } from '@/api'
import { useAppStore } from '@/stores/app'
import { useDashboardStore } from '@/stores/dashboard'
import type { EnvironmentData, EnvironmentPoint } from '@/types'

const appStore = useAppStore()
const dashboardStore = useDashboardStore()
const range = ref<EnvironmentData['range']>('24h')
const environment = ref<EnvironmentData | null>(null)
const loading = ref(false)
const loadError = ref('')
let requestId = 0

const valid = computed(() => Boolean(environment.value?.valid))
const temperature = computed(() => environment.value?.temperature ?? 0)
const humidity = computed(() => environment.value?.humidity ?? 0)
const trend = computed(() => environment.value?.trend || [])
const summary = computed(() => environment.value?.summary)
const severity = computed<'offline' | 'normal' | 'warning' | 'critical'>(() => {
  if (!valid.value) return 'offline'
  if (temperature.value >= 9 || humidity.value >= 96) return 'critical'
  if (environment.value?.temperatureState === 'warning' || environment.value?.humidityState === 'warning' || temperature.value >= 7 || humidity.value >= 94) return 'warning'
  return 'normal'
})
const expectedSamples = computed(() => ({ '6h': 120, '24h': 480, '7d': 3360 }[range.value]))
const dataCompleteness = computed(() => Math.min(100, Math.round((summary.value?.sampleCount || 0) / expectedSamples.value * 100)))
const temperatureStability = computed(() => valid.value ? Math.max(0, Math.round(100 - (summary.value?.temperature.stddev || 0) * 25)) : 0)
const humidityStability = computed(() => valid.value ? Math.max(0, Math.round(100 - (summary.value?.humidity.stddev || 0) * 10)) : 0)
const healthScore = computed(() => {
  if (!valid.value) return 0
  const baseline = Math.round(temperatureStability.value * .4 + humidityStability.value * .3 + dataCompleteness.value * .3)
  if (severity.value === 'critical') return Math.min(baseline, 25)
  if (severity.value === 'warning') return Math.min(baseline, 60)
  return baseline
})
const rangeText = computed(() => ({ '6h': '近 6 小时', '24h': '近 24 小时', '7d': '近 7 天' }[range.value]))
const healthMessage = computed(() => {
  if (!valid.value) return '等待 SHT3x 首次采样'
  if (severity.value === 'critical') return '当前温湿度已严重超出安全范围，请检查制冷设备。'
  if (severity.value === 'warning') return '当前温湿度接近安全阈值，请持续关注。'
  if (summary.value?.abnormalCount) return `本时间段内有 ${summary.value.abnormalCount} 次异常采样。`
  return '当前时间段内未发现环境异常。'
})

const lineOption = computed(() => {
  const axisColor = appStore.isDark ? 'rgba(148,163,184,.18)' : 'rgba(100,116,139,.18)'
  const chartText = appStore.isDark ? '#70829a' : '#7b8ca3'
  const tempValues = trend.value.map((item) => item.temperature)
  const humidityValues = trend.value.map((item) => item.humidity)
  const tempPadding = Math.max(1, (Math.max(...tempValues) - Math.min(...tempValues)) * .3)
  const humidityPadding = Math.max(3, (Math.max(...humidityValues) - Math.min(...humidityValues)) * .2)
  return {
    animationDuration: 700,
    tooltip: { trigger: 'axis' },
    legend: { top: 0, right: 6, data: ['温度', '湿度'], textStyle: { color: chartText, fontSize: 10 } },
    grid: { top: 34, right: 45, bottom: 26, left: 42 },
    xAxis: { type: 'category', boundaryGap: false, data: trend.value.map((item) => item.time), axisLine: { lineStyle: { color: axisColor } }, axisTick: { show: false }, axisLabel: { color: chartText, fontSize: 9, hideOverlap: true } },
    yAxis: [
      { type: 'value', min: Math.floor(Math.min(...tempValues) - tempPadding), max: Math.ceil(Math.max(...tempValues) + tempPadding), name: '°C', nameTextStyle: { color: chartText }, splitLine: { lineStyle: { color: axisColor, type: 'dashed' } }, axisLabel: { color: chartText, fontSize: 9 } },
      { type: 'value', min: Math.floor(Math.min(...humidityValues) - humidityPadding), max: Math.ceil(Math.max(...humidityValues) + humidityPadding), name: '%RH', nameTextStyle: { color: chartText }, splitLine: { show: false }, axisLabel: { color: chartText, fontSize: 9 } },
    ],
    series: [
      { name: '温度', type: 'line', smooth: true, showSymbol: tempValues.length === 1, symbol: 'circle', symbolSize: 8, data: tempValues, lineStyle: { width: 3, color: '#38bdf8' }, itemStyle: { color: '#38bdf8' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(56,189,248,.32)' }, { offset: 1, color: 'rgba(56,189,248,0)' }] } } },
      { name: '湿度', type: 'line', yAxisIndex: 1, smooth: true, showSymbol: humidityValues.length === 1, symbol: 'circle', symbolSize: 8, data: humidityValues, lineStyle: { width: 2, color: '#14b8a6' }, itemStyle: { color: '#14b8a6' }, areaStyle: { color: 'rgba(20,184,166,.06)' } },
    ],
  }
})

const createGauge = (value: number, max: number, color: string, suffix: string) => ({
  animationDuration: 700,
  series: [{
    type: 'gauge', startAngle: 220, endAngle: -40, min: 0, max, radius: '92%',
    axisLine: { lineStyle: { width: 10, color: [[1, 'rgba(148,163,184,.12)']] } },
    progress: { show: true, width: 10, roundCap: true, itemStyle: { color } },
    pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
    detail: { valueAnimation: true, formatter: (current: number) => `${Number(current).toFixed(1)}${suffix}`, color: appStore.isDark ? '#f4f8ff' : '#16263d', fontSize: 24, fontWeight: 700, offsetCenter: [0, '4%'] },
    data: [{ value: Number(value.toFixed(1)) }],
  }],
})

const tempGauge = computed(() => createGauge(temperature.value, Math.max(35, Math.ceil(temperature.value / 5) * 5), severity.value === 'critical' ? '#ef4444' : severity.value === 'warning' ? '#f59e0b' : '#38bdf8', '°C'))
const humidityGauge = computed(() => createGauge(humidity.value, 100, severity.value === 'critical' ? '#ef4444' : severity.value === 'warning' ? '#f59e0b' : '#14b8a6', '%RH'))

const load = async () => {
  const currentRequest = ++requestId
  loading.value = true
  loadError.value = ''
  try {
    const response = await environmentApi.getCurrent(range.value)
    if (currentRequest === requestId) environment.value = response.data
  } catch {
    if (currentRequest === requestId) {
      environment.value = null
      loadError.value = '未取得传感器数据，请检查 env_service、数据同步服务和网络连接。'
    }
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}

const mergeLiveReading = (point: EnvironmentPoint) => {
  if (!environment.value || range.value === '7d') return
  const nextTrend = [...environment.value.trend]
  const last = nextTrend.at(-1)
  if (last?.time === point.time) nextTrend[nextTrend.length - 1] = point
  else nextTrend.push(point)
  const maxPoints = range.value === '6h' ? 120 : 480
  environment.value = { ...environment.value, trend: nextTrend.slice(-maxPoints) }
}

watch(range, load)
watch(() => dashboardStore.environment, (latest) => {
  if (!latest) return
  if (!environment.value) return
  environment.value = {
    ...environment.value,
    temperature: latest.temperature,
    humidity: latest.humidity,
    valid: latest.valid !== false,
    temperatureState: latest.temperatureState,
    humidityState: latest.humidityState,
    recordedAt: latest.recordedAt || environment.value.recordedAt,
  }
  const livePoint = latest.trend.at(-1)
  if (livePoint) mergeLiveReading(livePoint)
})
onMounted(load)
</script>

<template>
  <div class="environment-page">
    <PageHeader eyebrow="ENVIRONMENT SENSING" title="环境监测" />
    <div v-if="loadError" class="data-notice" role="status">{{ loadError }}</div>
    <div v-else-if="loading && !environment" class="data-notice" role="status">正在读取 SHT3x 温湿度数据…</div>

    <div class="environment-hero">
      <GlassPanel :class="['sensor-card', `is-${severity}`]" strong>
        <div class="sensor-card__head"><div><span>实时温度</span><small>SHT3x · 冷藏室</small></div><Thermometer :size="24" /></div>
        <BaseChart v-if="valid" :option="tempGauge" height="180px" />
        <div v-else class="sensor-empty">暂无有效温度采样</div>
        <div class="sensor-range"><span>安全范围 2-5°C</span><strong>{{ severity === 'normal' ? '运行正常' : severity === 'warning' ? '接近阈值' : severity === 'critical' ? '严重异常' : '等待采样' }}</strong></div>
      </GlassPanel>
      <GlassPanel :class="['sensor-card', `is-${severity}`]" strong>
        <div class="sensor-card__head"><div><span>实时湿度</span><small>SHT3x · 冷藏室</small></div><Droplets :size="24" /></div>
        <BaseChart v-if="valid" :option="humidityGauge" height="180px" />
        <div v-else class="sensor-empty">暂无有效湿度采样</div>
        <div class="sensor-range"><span>安全范围 85-95%RH</span><strong>{{ severity === 'normal' ? '运行正常' : severity === 'warning' ? '接近阈值' : severity === 'critical' ? '严重异常' : '等待采样' }}</strong></div>
      </GlassPanel>
      <GlassPanel class="environment-health">
        <div class="health-head"><div><h2>环境健康指数</h2><span>由实际采样波动与完整度计算</span></div><Gauge :size="20" /></div>
        <div class="health-score"><strong>{{ healthScore }}</strong><span>/ 100</span></div>
        <div class="health-bars">
          <div><span>温度稳定度</span><b>{{ temperatureStability }}%</b><i><em :style="{ width: `${temperatureStability}%` }" /></i></div>
          <div><span>湿度稳定度</span><b>{{ humidityStability }}%</b><i><em :style="{ width: `${humidityStability}%` }" /></i></div>
          <div><span>数据完整度</span><b>{{ dataCompleteness }}%</b><i><em :style="{ width: `${dataCompleteness}%` }" /></i></div>
        </div>
        <div :class="['health-alert', `is-${severity}`]"><BellRing :size="14" />{{ healthMessage }}</div>
      </GlassPanel>
    </div>

    <div class="environment-content">
      <GlassPanel class="trend-card">
        <div class="chart-head">
          <div><h2>温湿度历史曲线</h2><span>{{ rangeText }} · 当前共 {{ summary?.sampleCount || 0 }} 条 SHT3x 采样</span></div>
          <div class="range-switch" aria-label="环境历史范围">
            <button v-for="item in [{k:'6h',l:'6小时'},{k:'24h',l:'24小时'},{k:'7d',l:'7天'}]" :key="item.k" type="button" :class="{ active: range === item.k }" @click="range = item.k as EnvironmentData['range']">{{ item.l }}</button>
          </div>
        </div>
        <BaseChart v-if="trend.length" :option="lineOption" height="310px" />
        <div v-else class="chart-empty">暂无该时间范围的传感器采样数据。</div>
      </GlassPanel>

      <div class="environment-side">
        <GlassPanel>
          <div class="mini-title"><div><h2>环境洞察</h2><span>基于真实采样计算</span></div><Activity :size="17" /></div>
          <div class="insight-list">
            <div><i class="is-green"><Waves :size="14" /></i><span><strong>温度波动 {{ summary?.temperature.stddev ?? '--' }}°C</strong><small>{{ rangeText }}均值 {{ summary?.temperature.average ?? '--' }}°C，范围 {{ summary?.temperature.min ?? '--' }}–{{ summary?.temperature.max ?? '--' }}°C</small></span></div>
            <div><i class="is-cyan"><Droplets :size="14" /></i><span><strong>湿度波动 {{ summary?.humidity.stddev ?? '--' }}%RH</strong><small>{{ rangeText }}均值 {{ summary?.humidity.average ?? '--' }}%RH，范围 {{ summary?.humidity.min ?? '--' }}–{{ summary?.humidity.max ?? '--' }}%RH</small></span></div>
            <div><i class="is-blue"><Thermometer :size="14" /></i><span><strong>{{ valid ? '传感器数据已上报' : '等待传感器上报' }}</strong><small>{{ environment?.recordedAt ? `最近采样：${environment.recordedAt}` : '未发现 env_log 记录' }}</small></span></div>
          </div>
        </GlassPanel>
        <GlassPanel>
          <div class="mini-title"><div><h2>阈值策略</h2><span>env_service 当前配置</span></div><Settings2 :size="17" /></div>
          <dl class="threshold-list">
            <div><dt>温度预警</dt><dd>&gt; 8.0°C / 10 分钟</dd></div>
            <div><dt>湿度提示</dt><dd>&gt; 95%RH</dd></div>
            <div><dt>采样间隔</dt><dd>180 秒</dd></div>
            <div><dt>实时刷新</dt><dd>WebSocket 推送</dd></div>
          </dl>
        </GlassPanel>
      </div>
    </div>
  </div>
</template>

<style scoped>
.data-notice { margin-bottom: 14px; padding: 10px 12px; border: 1px solid rgba(56,189,248,.25); border-radius: 10px; color: var(--text-2); font-size: 11px; background: rgba(56,189,248,.06); }
.environment-hero { display: grid; grid-template-columns: 1fr 1fr .9fr; gap: 14px; }
.sensor-card { position: relative; overflow: hidden; transition: border-color .3s ease, background .3s ease, box-shadow .3s ease; }.sensor-card.is-warning { border-color: rgba(245,158,11,.55); background: linear-gradient(145deg, rgba(245,158,11,.13), var(--surface)); box-shadow: 0 0 30px rgba(245,158,11,.12); }.sensor-card.is-critical { border-color: rgba(239,68,68,.68); background: linear-gradient(145deg, rgba(239,68,68,.15), var(--surface)); animation: critical-card 1.45s ease-in-out infinite; }
@keyframes critical-card { 50% { box-shadow: 0 0 34px rgba(239,68,68,.28); } }
.sensor-card__head { display: flex; align-items: flex-start; justify-content: space-between; color: var(--cyan); }.sensor-card__head span, .sensor-card__head small { display: block; }.sensor-card__head span { color: var(--text-1); font-size: 13px; font-weight: 650; }.sensor-card__head small { margin-top: 5px; color: var(--text-3); font-size: 9px; }.sensor-empty { display: grid; min-height: 180px; place-items: center; color: var(--text-3); font-size: 11px; }
.sensor-range { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: var(--text-3); font-size: 9px; }.sensor-range strong { color: var(--green); }.is-warning .sensor-range strong { color: var(--orange); }.is-critical .sensor-range strong, .is-offline .sensor-range strong { color: var(--red); }
.environment-health { display: flex; flex-direction: column; }.health-head, .chart-head, .mini-title { display: flex; align-items: flex-start; justify-content: space-between; color: var(--cyan); }.health-head h2, .chart-head h2, .mini-title h2 { margin: 0; color: var(--text-1); font-size: 13px; }.health-head span, .chart-head span, .mini-title span { display: block; margin-top: 5px; color: var(--text-3); font-size: 9px; }.health-score { display: flex; align-items: baseline; margin-top: 20px; }.health-score strong { color: var(--text-1); font-size: 42px; letter-spacing: -.04em; }.health-score span { margin-left: 5px; color: var(--text-3); font-size: 11px; }.health-bars { display: grid; gap: 10px; margin-top: 12px; }.health-bars div { display: grid; grid-template-columns: 1fr auto; gap: 5px; }.health-bars span, .health-bars b { font-size: 9px; }.health-bars span { color: var(--text-3); }.health-bars b { color: var(--text-2); }.health-bars i { grid-column: 1/-1; height: 4px; overflow: hidden; border-radius: 99px; background: var(--surface-soft); }.health-bars em { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--cyan), var(--green)); }.health-alert { display: flex; align-items: center; gap: 6px; margin-top: auto; padding: 9px; border-radius: 10px; color: #82eea7; font-size: 9px; background: rgba(34,197,94,.08); }.health-alert.is-warning { color: #ffd477; background: rgba(245,158,11,.1); }.health-alert.is-critical, .health-alert.is-offline { color: #ff9a9a; background: rgba(239,68,68,.12); }
.environment-content { display: grid; grid-template-columns: 1.6fr .65fr; gap: 14px; margin-top: 14px; }.range-switch { display: flex; padding: 3px; border-radius: 9px; background: var(--surface-soft); }.range-switch button { padding: 6px 9px; border: 0; border-radius: 7px; color: var(--text-3); font-size: 9px; background: transparent; }.range-switch button.active { color: white; background: var(--blue); }.chart-empty { display: grid; min-height: 310px; place-items: center; color: var(--text-3); font-size: 11px; }
.environment-side { display: grid; gap: 14px; }.insight-list { display: grid; gap: 9px; margin-top: 16px; }.insight-list > div { display: flex; align-items: center; gap: 9px; padding: 10px; border-radius: 11px; background: var(--surface-soft); }.insight-list i { display: grid; width: 31px; height: 31px; flex: 0 0 auto; place-items: center; border-radius: 9px; }.insight-list i.is-green { color: var(--green); background: rgba(34,197,94,.1); }.insight-list i.is-cyan { color: var(--teal); background: rgba(20,184,166,.1); }.insight-list i.is-blue { color: var(--cyan); background: rgba(56,189,248,.1); }.insight-list strong, .insight-list small { display: block; }.insight-list strong { color: var(--text-1); font-size: 10px; }.insight-list small { margin-top: 4px; color: var(--text-3); font-size: 8px; line-height: 1.5; }.threshold-list { margin: 14px 0 0; }.threshold-list div { display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--stroke); }.threshold-list div:last-child { border-bottom: 0; }.threshold-list dt, .threshold-list dd { margin: 0; font-size: 9px; }.threshold-list dt { color: var(--text-3); }.threshold-list dd { color: var(--text-1); font-weight: 600; }
@media (max-width: 1100px) { .environment-hero { grid-template-columns: 1fr 1fr; }.environment-health { grid-column: 1/-1; }.environment-content { grid-template-columns: 1fr; }.environment-side { grid-template-columns: 1fr 1fr; } }
@media (max-width: 680px) { .environment-hero, .environment-side { grid-template-columns: 1fr; }.environment-health { grid-column: auto; }.chart-head { gap: 12px; flex-direction: column; } }
</style>
