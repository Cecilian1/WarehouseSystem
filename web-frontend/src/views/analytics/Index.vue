<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { BarChart3, CalendarRange, Download, LineChart, PieChart, Radar, Sparkles } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import { analyticsApi } from '@/api'
import { useAppStore } from '@/stores/app'
import type { AnalyticsData } from '@/types'

const appStore = useAppStore()
const range = ref<AnalyticsData['range']>('month')
const data = ref<AnalyticsData | null>(null)
const loading = ref(false)
const loadError = ref('')

const axis = computed(() => appStore.isDark ? 'rgba(148,163,184,.16)' : 'rgba(100,116,139,.17)')
const text = computed(() => appStore.isDark ? '#70829a' : '#7b8ca3')
const titleColor = computed(() => appStore.isDark ? '#f4f8ff' : '#16263d')
const hasFlowData = computed(() => Boolean(data.value?.daily.some((item) => item.inbound || item.outbound)))
const hasCategoryData = computed(() => Boolean(data.value?.categories.some((item) => item.value > 0)))
const hasFreshnessData = computed(() => Boolean(data.value?.freshness.some((item) => item.value > 0)))
const hasHeatmapData = computed(() => Boolean(data.value?.heatmap.length))
const hasKpiData = computed(() => Boolean(data.value?.kpis.recognitionCount || data.value?.kpis.totalInbound || data.value?.kpis.totalOutbound))

const kpis = computed(() => {
  const k = data.value?.kpis
  return [
    { label: '识别准确率', value: hasKpiData.value && k ? `${k.accuracy}%` : '暂无数据', change: k ? `${k.recognitionCount} 次操作` : '等待采集', icon: Sparkles, color: '#38bdf8' },
    { label: '库存周转率', value: hasKpiData.value && k ? `${k.turnover}%` : '暂无数据', change: k ? `出库 ${k.totalOutbound} 件` : '等待采集', icon: CalendarRange, color: '#22c55e' },
    { label: '库存保鲜率', value: hasCategoryData.value && k ? `${k.savingRate}%` : '暂无数据', change: k ? `入库 ${k.totalInbound} 件` : '等待库存数据', icon: LineChart, color: '#14b8a6' },
    { label: '平均库存周期', value: hasCategoryData.value && k?.avgCycle ? `${k.avgCycle} 天` : '暂无数据', change: '按在库品类计算', icon: BarChart3, color: '#f59e0b' },
  ]
})

const commonTooltip = computed(() => ({
  trigger: 'axis',
  backgroundColor: appStore.isDark ? 'rgba(10,23,40,.96)' : 'rgba(255,255,255,.98)',
  borderColor: axis.value,
  textStyle: { color: titleColor.value, fontSize: 10 },
}))

const trendOption = computed(() => ({
  animationDuration: 700,
  tooltip: commonTooltip.value,
  legend: { top: 2, right: 6, data: ['入库', '出库'], textStyle: { color: text.value, fontSize: 9 } },
  grid: { top: 35, right: 12, bottom: 25, left: 35 },
  xAxis: { type: 'category', boundaryGap: false, data: data.value?.daily.map((item) => item.date) || [], axisLine: { lineStyle: { color: axis.value } }, axisTick: { show: false }, axisLabel: { color: text.value, fontSize: 8 } },
  yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: axis.value, type: 'dashed' } }, axisLabel: { color: text.value, fontSize: 8 } },
  series: [
    { name: '入库', type: 'line', smooth: true, symbol: 'circle', symbolSize: 5, data: data.value?.daily.map((item) => item.inbound), lineStyle: { color: '#38bdf8', width: 3 }, itemStyle: { color: '#38bdf8' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(56,189,248,.32)' }, { offset: 1, color: 'rgba(56,189,248,0)' }] } } },
    { name: '出库', type: 'line', smooth: true, symbol: 'circle', symbolSize: 5, data: data.value?.daily.map((item) => item.outbound), lineStyle: { color: '#22c55e', width: 2 }, itemStyle: { color: '#22c55e' } },
  ],
}))

const barOption = computed(() => ({
  animationDuration: 700,
  tooltip: commonTooltip.value,
  grid: { top: 20, right: 10, bottom: 24, left: 34 },
  xAxis: { type: 'category', data: data.value?.daily.map((item) => item.date) || [], axisLine: { lineStyle: { color: axis.value } }, axisTick: { show: false }, axisLabel: { color: text.value, fontSize: 8 } },
  yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: axis.value, type: 'dashed' } }, axisLabel: { color: text.value, fontSize: 8 } },
  series: [{ type: 'bar', data: data.value?.daily.map((item) => item.inbound + item.outbound), barMaxWidth: 18, itemStyle: { borderRadius: [5, 5, 1, 1], color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#4f8cff' }, { offset: 1, color: 'rgba(79,140,255,.2)' }] } } }],
}))

const donutOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, icon: 'circle', itemWidth: 8, textStyle: { color: text.value, fontSize: 9 } },
  series: [{ type: 'pie', radius: ['48%', '70%'], center: ['50%', '45%'], label: { show: false }, itemStyle: { borderColor: appStore.isDark ? '#102034' : '#f6f9fc', borderWidth: 3, borderRadius: 5 }, data: data.value?.categories.map((item) => ({ value: item.value, name: item.name, itemStyle: { color: item.color } })) || [] }],
}))

const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, icon: 'circle', itemWidth: 8, textStyle: { color: text.value, fontSize: 9 } },
  series: [{ type: 'pie', radius: ['10%', '70%'], center: ['50%', '45%'], roseType: 'radius', label: { color: text.value, fontSize: 9, formatter: '{b}\n{d}%' }, itemStyle: { borderColor: appStore.isDark ? '#102034' : '#f6f9fc', borderWidth: 2, borderRadius: 5 }, data: data.value?.freshness.map((item) => ({ value: item.value, name: item.name, itemStyle: { color: item.color } })) || [] }],
}))

const radarOption = computed(() => ({
  radar: { center: ['50%', '52%'], radius: '67%', indicator: data.value?.radar.map((item) => ({ name: item.name, max: 100 })) || [], axisName: { color: text.value, fontSize: 9 }, splitArea: { areaStyle: { color: ['rgba(79,140,255,.02)', 'rgba(79,140,255,.05)'] } }, splitLine: { lineStyle: { color: axis.value } }, axisLine: { lineStyle: { color: axis.value } } },
  series: [{ type: 'radar', data: [{ value: data.value?.radar.map((item) => item.value) || [], areaStyle: { color: 'rgba(79,140,255,.28)' }, lineStyle: { color: '#4f8cff', width: 2 }, itemStyle: { color: '#38bdf8' } }] }],
}))

const heatmapOption = computed(() => ({
  tooltip: { position: 'top' },
  grid: { top: 20, right: 10, bottom: 35, left: 55 },
  xAxis: { type: 'category', data: Array.from({ length: 12 }, (_, i) => `${i * 2}:00`), splitArea: { show: true }, axisLine: { lineStyle: { color: axis.value } }, axisLabel: { color: text.value, fontSize: 8 } },
  yAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'], splitArea: { show: true }, axisLine: { lineStyle: { color: axis.value } }, axisLabel: { color: text.value, fontSize: 8 } },
  visualMap: { min: 0, max: Math.max(1, ...(data.value?.heatmap.map((item) => item[2]) || [1])), calculable: false, orient: 'horizontal', left: 'center', bottom: 0, itemWidth: 10, itemHeight: 80, textStyle: { color: text.value, fontSize: 8 }, inRange: { color: ['rgba(56,189,248,.05)', '#38bdf8', '#22c55e', '#f59e0b'] } },
  series: [{ type: 'heatmap', data: data.value?.heatmap || [], label: { show: false }, itemStyle: { borderColor: appStore.isDark ? '#102034' : '#f6f9fc', borderWidth: 2, borderRadius: 3 } }],
}))

const load = async () => {
  loading.value = true
  loadError.value = ''
  try {
    data.value = (await analyticsApi.getData(range.value)).data
  } catch {
    data.value = null
    loadError.value = '统计数据暂时无法读取，请确认 API 服务和本地数据库正在运行。'
  } finally {
    loading.value = false
  }
}

const exportAnalytics = () => {
  if (!data.value?.daily.length) return
  const rows = ['日期,入库数量,出库数量', ...data.value.daily.map((item) => `${item.date},${item.inbound},${item.outbound}`)]
  const blob = new Blob([`\uFEFF${rows.join('\n')}`], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `warehouse-analytics-${range.value}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

watch(range, load)
onMounted(load)
</script>

<template>
  <div class="analytics-page">
    <PageHeader eyebrow="DATA INTELLIGENCE" title="统计分析">
      <template #actions>
        <div class="range-tabs" aria-label="统计时间范围">
          <button v-for="item in [{v:'today',l:'今日'},{v:'week',l:'本周'},{v:'month',l:'本月'},{v:'year',l:'本年'}]" :key="item.v" type="button" :class="{ active: range === item.v }" @click="range = item.v as AnalyticsData['range']">{{ item.l }}</button>
        </div>
        <el-button :disabled="!data?.daily.length" @click="exportAnalytics"><Download :size="15" />导出分析</el-button>
      </template>
    </PageHeader>

    <div v-if="loadError" class="data-notice" role="status">{{ loadError }}</div>
    <div v-else-if="loading && !data" class="data-notice" role="status">正在汇总库存与识别记录…</div>

    <div class="analysis-kpis">
      <GlassPanel v-for="item in kpis" :key="item.label" hover class="analysis-kpi">
        <div class="kpi-icon" :style="{color:item.color,background:`color-mix(in srgb, ${item.color} 12%, transparent)`}"><component :is="item.icon" :size="18" /></div>
        <div><span>{{ item.label }}</span><strong>{{ item.value }}</strong></div>
        <b>{{ item.change }}</b>
      </GlassPanel>
    </div>

    <div class="analytics-grid" :aria-busy="loading">
      <GlassPanel class="chart-card chart-wide">
        <div class="chart-title"><div><h2>入库 / 出库趋势</h2><span>库存流动量与节奏</span></div><LineChart :size="18" /></div>
        <BaseChart v-if="hasFlowData" :option="trendOption" height="280px" />
        <div v-else class="chart-empty">本时间范围内还没有入库或出库记录。</div>
      </GlassPanel>
      <GlassPanel class="chart-card">
        <div class="chart-title"><div><h2>操作量分布</h2><span>每日识别与库存操作</span></div><BarChart3 :size="18" /></div>
        <BaseChart v-if="hasFlowData" :option="barOption" height="280px" />
        <div v-else class="chart-empty">待产生库存操作后显示分布。</div>
      </GlassPanel>
      <GlassPanel class="chart-card">
        <div class="chart-title"><div><h2>库存分类占比</h2><span>水果 / 蔬菜结构</span></div><PieChart :size="18" /></div>
        <BaseChart v-if="hasCategoryData" :option="donutOption" height="240px" />
        <div v-else class="chart-empty">当前库存为空，暂无分类结构。</div>
      </GlassPanel>
      <GlassPanel class="chart-card">
        <div class="chart-title"><div><h2>新鲜度分布</h2><span>模型分类结果</span></div><PieChart :size="18" /></div>
        <BaseChart v-if="hasFreshnessData" :option="pieOption" height="240px" />
        <div v-else class="chart-empty">当前库存为空，暂无新鲜度分布。</div>
      </GlassPanel>
      <GlassPanel class="chart-card">
        <div class="chart-title"><div><h2>系统能力雷达</h2><span>由真实识别、环境与设备状态计算</span></div><Radar :size="18" /></div>
        <BaseChart v-if="data" :option="radarOption" height="240px" />
        <div v-else class="chart-empty">正在等待系统状态。</div>
      </GlassPanel>
      <GlassPanel class="chart-card chart-full">
        <div class="chart-title"><div><h2>识别活跃热力图</h2><span>按星期与时段聚合</span></div><CalendarRange :size="18" /></div>
        <BaseChart v-if="hasHeatmapData" :option="heatmapOption" height="240px" />
        <div v-else class="chart-empty">本时间范围内还没有可聚合的识别记录。</div>
      </GlassPanel>
    </div>
  </div>
</template>

<style scoped>
.range-tabs { display: flex; padding: 3px; border: 1px solid var(--stroke); border-radius: 10px; background: var(--surface-soft); }.range-tabs button { padding: 7px 11px; border: 0; border-radius: 8px; color: var(--text-3); font-size: 9px; background: transparent; }.range-tabs button.active { color: white; background: linear-gradient(135deg, #38bdf8, #4f8cff); }
.data-notice { margin-bottom: 12px; padding: 10px 12px; border: 1px solid rgba(56,189,248,.25); border-radius: 10px; color: var(--text-2); font-size: 11px; background: rgba(56,189,248,.06); }
.analysis-kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.analysis-kpi { display: grid; grid-template-columns: 40px 1fr auto; align-items: center; gap: 11px; }.kpi-icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 12px; }.analysis-kpi span, .analysis-kpi strong { display: block; }.analysis-kpi span { color: var(--text-3); font-size: 9px; }.analysis-kpi strong { margin-top: 5px; color: var(--text-1); font-size: 18px; }.analysis-kpi b { color: var(--text-2); font-size: 9px; }
.analytics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px; }.chart-wide { grid-column: span 2; }.chart-full { grid-column: 1 / -1; }.chart-card { min-width: 0; }.chart-title { display: flex; align-items: flex-start; justify-content: space-between; color: var(--cyan); }.chart-title h2 { margin: 0; color: var(--text-1); font-size: 13px; }.chart-title span { display: block; margin-top: 5px; color: var(--text-3); font-size: 9px; }
.chart-empty { display: grid; min-height: 240px; place-items: center; padding: 18px; color: var(--text-3); font-size: 11px; line-height: 1.7; text-align: center; }.chart-wide .chart-empty { min-height: 280px; }
@media (max-width: 1100px) { .analysis-kpis { grid-template-columns: 1fr 1fr; }.analytics-grid { grid-template-columns: 1fr 1fr; }.chart-wide, .chart-full { grid-column: 1 / -1; } }
@media (max-width: 680px) { .analysis-kpis, .analytics-grid { grid-template-columns: 1fr; }.chart-wide, .chart-full { grid-column: auto; }.range-tabs { overflow-x: auto; } }
</style>
