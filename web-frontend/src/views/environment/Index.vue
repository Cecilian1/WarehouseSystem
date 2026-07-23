<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Activity, BellRing, Droplets, Gauge, Settings2, Thermometer, Waves } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import { environmentApi } from '@/api'
import { useAppStore } from '@/stores/app'
import type { EnvironmentPoint } from '@/types'

const appStore = useAppStore()
const temperature = ref(3.6)
const humidity = ref(88)
const trend = ref<EnvironmentPoint[]>([])
const range = ref<'6h' | '24h' | '7d'>('24h')
const simulateAlert = ref(false)

const effectiveTemperature = computed(() => simulateAlert.value ? 9.4 : temperature.value)
const effectiveHumidity = computed(() => simulateAlert.value ? 96.8 : humidity.value)
const severity = computed(() => effectiveTemperature.value >= 9 || effectiveHumidity.value >= 96 ? 'critical' : effectiveTemperature.value >= 7 || effectiveHumidity.value >= 94 ? 'warning' : 'normal')

const lineOption = computed(() => {
  const axisColor = appStore.isDark ? 'rgba(148,163,184,.18)' : 'rgba(100,116,139,.18)'
  const text = appStore.isDark ? '#70829a' : '#7b8ca3'
  return {
    animationDuration: 1000,
    tooltip: { trigger: 'axis' },
    legend: { top: 0, right: 6, data: ['温度', '湿度'], textStyle: { color: text, fontSize: 10 } },
    grid: { top: 34, right: 45, bottom: 26, left: 42 },
    xAxis: { type: 'category', boundaryGap: false, data: trend.value.map((item) => item.time), axisLine: { lineStyle: { color: axisColor } }, axisTick: { show: false }, axisLabel: { color: text, fontSize: 9 } },
    yAxis: [
      { type: 'value', min: 0, max: 10, name: '°C', nameTextStyle: { color: text }, splitLine: { lineStyle: { color: axisColor, type: 'dashed' } }, axisLabel: { color: text, fontSize: 9 } },
      { type: 'value', min: 70, max: 100, name: '%RH', nameTextStyle: { color: text }, splitLine: { show: false }, axisLabel: { color: text, fontSize: 9 } },
    ],
    series: [
      { name: '温度', type: 'line', smooth: true, showSymbol: false, data: trend.value.map((item) => item.temperature), lineStyle: { width: 3, color: '#38bdf8' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(56,189,248,.32)' }, { offset: 1, color: 'rgba(56,189,248,0)' }] } } },
      { name: '湿度', type: 'line', yAxisIndex: 1, smooth: true, showSymbol: false, data: trend.value.map((item) => item.humidity), lineStyle: { width: 2, color: '#14b8a6' }, areaStyle: { color: 'rgba(20,184,166,.06)' } },
    ],
  }
})

const createGauge = (value: number, max: number, color: string, suffix: string) => ({
  animationDuration: 900,
  series: [{
    type: 'gauge', startAngle: 220, endAngle: -40, min: 0, max, radius: '92%',
    axisLine: { lineStyle: { width: 10, color: [[1, 'rgba(148,163,184,.12)']] } },
    progress: { show: true, width: 10, roundCap: true, itemStyle: { color } },
    pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
    detail: { valueAnimation: true, formatter: `{value}${suffix}`, color: appStore.isDark ? '#f4f8ff' : '#16263d', fontSize: 24, fontWeight: 700, offsetCenter: [0, '4%'] },
    data: [{ value }],
  }],
})

const tempGauge = computed(() => createGauge(effectiveTemperature.value, 12, severity.value === 'critical' ? '#ef4444' : severity.value === 'warning' ? '#f59e0b' : '#38bdf8', '°'))
const humidityGauge = computed(() => createGauge(effectiveHumidity.value, 100, severity.value === 'critical' ? '#ef4444' : severity.value === 'warning' ? '#f59e0b' : '#14b8a6', '%'))

onMounted(async () => {
  const response = await environmentApi.getCurrent()
  temperature.value = response.data.temperature
  humidity.value = response.data.humidity
  trend.value = response.data.trend
})
</script>

<template>
  <div class="environment-page">
    <PageHeader eyebrow="ENVIRONMENT SENSING" title="环境监测" description="温湿度实时感知、趋势分析与异常阈值联动">
      <template #actions>
        <el-switch v-model="simulateAlert" active-text="异常态演示" />
        <el-button><Settings2 :size="15" />阈值设置</el-button>
      </template>
    </PageHeader>

    <div class="environment-hero">
      <GlassPanel :class="['sensor-card', `is-${severity}`]" strong>
        <div class="sensor-card__head"><div><span>实时温度</span><small>SHT30 · 冷藏室</small></div><Thermometer :size="24" /></div>
        <BaseChart :option="tempGauge" height="180px" />
        <div class="sensor-range"><span>安全范围 2-5°C</span><strong>{{ severity === 'normal' ? '运行正常' : severity === 'warning' ? '接近阈值' : '严重异常' }}</strong></div>
      </GlassPanel>
      <GlassPanel :class="['sensor-card', `is-${severity}`]" strong>
        <div class="sensor-card__head"><div><span>实时湿度</span><small>SHT30 · 冷藏室</small></div><Droplets :size="24" /></div>
        <BaseChart :option="humidityGauge" height="180px" />
        <div class="sensor-range"><span>安全范围 85-95%RH</span><strong>{{ severity === 'normal' ? '运行正常' : severity === 'warning' ? '接近阈值' : '严重异常' }}</strong></div>
      </GlassPanel>
      <GlassPanel class="environment-health">
        <div class="health-head"><div><h2>环境健康指数</h2><span>多指标综合评估</span></div><Gauge :size="20" /></div>
        <div class="health-score"><strong>{{ simulateAlert ? 62 : 96 }}</strong><span>/ 100</span></div>
        <div class="health-bars">
          <div><span>温度稳定度</span><b>{{ simulateAlert ? 58 : 98 }}%</b><i><em :style="{ width: `${simulateAlert ? 58 : 98}%` }" /></i></div>
          <div><span>湿度稳定度</span><b>{{ simulateAlert ? 64 : 94 }}%</b><i><em :style="{ width: `${simulateAlert ? 64 : 94}%` }" /></i></div>
          <div><span>数据完整度</span><b>99%</b><i><em style="width:99%" /></i></div>
        </div>
        <div :class="['health-alert', `is-${severity}`]"><BellRing :size="14" />{{ severity === 'normal' ? '当前无环境异常' : '环境数据已触发预警规则' }}</div>
      </GlassPanel>
    </div>

    <div class="environment-content">
      <GlassPanel class="trend-card">
        <div class="chart-head">
          <div><h2>温湿度历史曲线</h2><span>采样周期 3 分钟 · WebSocket 实时更新</span></div>
          <div class="range-switch">
            <button v-for="item in [{k:'6h',l:'6小时'},{k:'24h',l:'24小时'},{k:'7d',l:'7天'}]" :key="item.k" :class="{ active: range === item.k }" @click="range = item.k as typeof range">{{ item.l }}</button>
          </div>
        </div>
        <BaseChart :option="lineOption" height="310px" />
      </GlassPanel>

      <div class="environment-side">
        <GlassPanel>
          <div class="mini-title"><div><h2>环境洞察</h2><span>端侧异常分析</span></div><Activity :size="17" /></div>
          <div class="insight-list">
            <div><i class="is-green"><Waves :size="14" /></i><span><strong>波动范围优秀</strong><small>温度标准差仅 0.42°C</small></span></div>
            <div><i class="is-cyan"><Droplets :size="14" /></i><span><strong>湿度适宜</strong><small>近 24h 均值 88.6%RH</small></span></div>
            <div><i class="is-blue"><Thermometer :size="14" /></i><span><strong>制冷周期正常</strong><small>平均启停间隔 36 分钟</small></span></div>
          </div>
        </GlassPanel>
        <GlassPanel>
          <div class="mini-title"><div><h2>阈值策略</h2><span>当前生效规则</span></div><Settings2 :size="17" /></div>
          <dl class="threshold-list">
            <div><dt>温度预警</dt><dd>&gt; 8.0°C / 10 分钟</dd></div>
            <div><dt>湿度预警</dt><dd>&gt; 95%RH / 10 分钟</dd></div>
            <div><dt>采样间隔</dt><dd>180 秒</dd></div>
            <div><dt>异常恢复</dt><dd>连续 3 次正常</dd></div>
          </dl>
        </GlassPanel>
      </div>
    </div>
  </div>
</template>

<style scoped>
.environment-hero { display: grid; grid-template-columns: 1fr 1fr .9fr; gap: 14px; }
.sensor-card { position: relative; overflow: hidden; transition: border-color .3s ease, background .3s ease, box-shadow .3s ease; }
.sensor-card.is-warning { border-color: rgba(245,158,11,.55); background: linear-gradient(145deg, rgba(245,158,11,.13), var(--surface)); box-shadow: 0 0 30px rgba(245,158,11,.12); }
.sensor-card.is-critical { border-color: rgba(239,68,68,.68); background: linear-gradient(145deg, rgba(239,68,68,.15), var(--surface)); animation: critical-card 1.45s ease-in-out infinite; }
@keyframes critical-card { 50% { box-shadow: 0 0 34px rgba(239,68,68,.28); } }
.sensor-card__head { display: flex; align-items: flex-start; justify-content: space-between; color: var(--cyan); }
.sensor-card__head span, .sensor-card__head small { display: block; }.sensor-card__head span { color: var(--text-1); font-size: 13px; font-weight: 650; }.sensor-card__head small { margin-top: 5px; color: var(--text-3); font-size: 9px; }
.sensor-range { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: var(--text-3); font-size: 9px; }.sensor-range strong { color: var(--green); }.is-warning .sensor-range strong { color: var(--orange); }.is-critical .sensor-range strong { color: var(--red); }
.environment-health { display: flex; flex-direction: column; }
.health-head, .chart-head, .mini-title { display: flex; align-items: flex-start; justify-content: space-between; color: var(--cyan); }
.health-head h2, .chart-head h2, .mini-title h2 { margin: 0; color: var(--text-1); font-size: 13px; }.health-head span, .chart-head span, .mini-title span { display: block; margin-top: 5px; color: var(--text-3); font-size: 9px; }
.health-score { display: flex; align-items: baseline; margin-top: 20px; }.health-score strong { color: var(--text-1); font-size: 42px; letter-spacing: -.04em; }.health-score span { margin-left: 5px; color: var(--text-3); font-size: 11px; }
.health-bars { display: grid; gap: 10px; margin-top: 12px; }.health-bars div { display: grid; grid-template-columns: 1fr auto; gap: 5px; }.health-bars span, .health-bars b { font-size: 9px; }.health-bars span { color: var(--text-3); }.health-bars b { color: var(--text-2); }.health-bars i { grid-column: 1/-1; height: 4px; overflow: hidden; border-radius: 99px; background: var(--surface-soft); }.health-bars em { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--cyan), var(--green)); }
.health-alert { display: flex; align-items: center; gap: 6px; margin-top: auto; padding: 9px; border-radius: 10px; color: #82eea7; font-size: 9px; background: rgba(34,197,94,.08); }.health-alert.is-warning { color: #ffd477; background: rgba(245,158,11,.1); }.health-alert.is-critical { color: #ff9a9a; background: rgba(239,68,68,.12); }
.environment-content { display: grid; grid-template-columns: 1.6fr .65fr; gap: 14px; margin-top: 14px; }
.range-switch { display: flex; padding: 3px; border-radius: 9px; background: var(--surface-soft); }.range-switch button { padding: 6px 9px; border: 0; border-radius: 7px; color: var(--text-3); font-size: 9px; background: transparent; }.range-switch button.active { color: white; background: var(--blue); }
.environment-side { display: grid; gap: 14px; }
.insight-list { display: grid; gap: 9px; margin-top: 16px; }.insight-list > div { display: flex; align-items: center; gap: 9px; padding: 10px; border-radius: 11px; background: var(--surface-soft); }.insight-list i { display: grid; width: 31px; height: 31px; place-items: center; border-radius: 9px; }.insight-list i.is-green { color: var(--green); background: rgba(34,197,94,.1); }.insight-list i.is-cyan { color: var(--teal); background: rgba(20,184,166,.1); }.insight-list i.is-blue { color: var(--cyan); background: rgba(56,189,248,.1); }.insight-list strong, .insight-list small { display: block; }.insight-list strong { color: var(--text-1); font-size: 10px; }.insight-list small { margin-top: 4px; color: var(--text-3); font-size: 8px; }
.threshold-list { margin: 14px 0 0; }.threshold-list div { display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--stroke); }.threshold-list div:last-child { border-bottom: 0; }.threshold-list dt, .threshold-list dd { margin: 0; font-size: 9px; }.threshold-list dt { color: var(--text-3); }.threshold-list dd { color: var(--text-1); font-weight: 600; }
@media (max-width: 1100px) { .environment-hero { grid-template-columns: 1fr 1fr; } .environment-health { grid-column: 1/-1; } .environment-content { grid-template-columns: 1fr; } .environment-side { grid-template-columns: 1fr 1fr; } }
@media (max-width: 680px) { .environment-hero, .environment-side { grid-template-columns: 1fr; } .environment-health { grid-column: auto; } .chart-head { gap: 12px; flex-direction: column; } }
</style>
