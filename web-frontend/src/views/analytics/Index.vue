<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { BarChart3, CalendarRange, Download, LineChart, PieChart, Radar, Sparkles } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import { analyticsApi } from '@/api'
import { useAppStore } from '@/stores/app'

interface Analytics {
  daily: Array<{ date: string; inbound: number; outbound: number; waste: number }>
  categories: Array<{ name: string; value: number; color: string }>
  freshness: Array<{ name: string; value: number; color: string }>
  radar: Array<{ name: string; value: number }>
  heatmap: number[][]
}

const appStore = useAppStore()
const range = ref<'today' | 'week' | 'month' | 'year'>('month')
const data = ref<Analytics | null>(null)
const axis = computed(() => appStore.isDark ? 'rgba(148,163,184,.16)' : 'rgba(100,116,139,.17)')
const text = computed(() => appStore.isDark ? '#70829a' : '#7b8ca3')
const titleColor = computed(() => appStore.isDark ? '#f4f8ff' : '#16263d')

const commonTooltip = computed(() => ({
  trigger: 'axis',
  backgroundColor: appStore.isDark ? 'rgba(10,23,40,.96)' : 'rgba(255,255,255,.98)',
  borderColor: axis.value,
  textStyle: { color: titleColor.value, fontSize: 10 },
}))

const trendOption = computed(() => ({
  animationDuration: 1100,
  tooltip: commonTooltip.value,
  legend: { top: 2, right: 6, data: ['入库', '出库'], textStyle: { color: text.value, fontSize: 9 } },
  grid: { top: 35, right: 12, bottom: 25, left: 35 },
  xAxis: { type: 'category', boundaryGap: false, data: data.value?.daily.map((item) => item.date) || [], axisLine: { lineStyle: { color: axis.value } }, axisTick: { show: false }, axisLabel: { color: text.value, fontSize: 8 } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: axis.value, type: 'dashed' } }, axisLabel: { color: text.value, fontSize: 8 } },
  series: [
    { name: '入库', type: 'line', smooth: true, symbol: 'circle', symbolSize: 5, data: data.value?.daily.map((item) => item.inbound), lineStyle: { color: '#38bdf8', width: 3 }, itemStyle: { color: '#38bdf8' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(56,189,248,.32)' }, { offset: 1, color: 'rgba(56,189,248,0)' }] } } },
    { name: '出库', type: 'line', smooth: true, symbol: 'circle', symbolSize: 5, data: data.value?.daily.map((item) => item.outbound), lineStyle: { color: '#22c55e', width: 2 }, itemStyle: { color: '#22c55e' } },
  ],
}))

const barOption = computed(() => ({
  animationDuration: 1000,
  tooltip: commonTooltip.value,
  grid: { top: 20, right: 10, bottom: 24, left: 34 },
  xAxis: { type: 'category', data: data.value?.daily.map((item) => item.date) || [], axisLine: { lineStyle: { color: axis.value } }, axisTick: { show: false }, axisLabel: { color: text.value, fontSize: 8 } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: axis.value, type: 'dashed' } }, axisLabel: { color: text.value, fontSize: 8 } },
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
  visualMap: { min: 0, max: 12, calculable: false, orient: 'horizontal', left: 'center', bottom: 0, itemWidth: 10, itemHeight: 80, textStyle: { color: text.value, fontSize: 8 }, inRange: { color: ['rgba(56,189,248,.05)', '#38bdf8', '#22c55e', '#f59e0b'] } },
  series: [{ type: 'heatmap', data: data.value?.heatmap || [], label: { show: false }, itemStyle: { borderColor: appStore.isDark ? '#102034' : '#f6f9fc', borderWidth: 2, borderRadius: 3 } }],
}))

onMounted(async () => { data.value = (await analyticsApi.getData()).data as unknown as Analytics })
</script>

<template>
  <div class="analytics-page">
    <PageHeader eyebrow="DATA INTELLIGENCE" title="统计分析" description="库存效率、识别质量与环境稳定性的多维分析">
      <template #actions>
        <div class="range-tabs">
          <button v-for="item in [{v:'today',l:'今日'},{v:'week',l:'本周'},{v:'month',l:'本月'},{v:'year',l:'本年'}]" :key="item.v" :class="{ active: range === item.v }" @click="range = item.v as typeof range">{{ item.l }}</button>
        </div>
        <el-button><Download :size="15" />导出分析</el-button>
      </template>
    </PageHeader>

    <div class="analysis-kpis">
      <GlassPanel v-for="item in [
        {label:'识别准确率',value:'96.8%',change:'+1.4%',icon:Sparkles,color:'#38bdf8'},
        {label:'库存周转率',value:'82.4%',change:'+8.2%',icon:CalendarRange,color:'#22c55e'},
        {label:'本月节约率',value:'12.8%',change:'+3.6%',icon:LineChart,color:'#14b8a6'},
        {label:'平均库存周期',value:'8.4 天',change:'-0.8 天',icon:BarChart3,color:'#f59e0b'}
      ]" :key="item.label" hover class="analysis-kpi">
        <div class="kpi-icon" :style="{color:item.color,background:`color-mix(in srgb, ${item.color} 12%, transparent)`}"><component :is="item.icon" :size="18" /></div>
        <div><span>{{ item.label }}</span><strong>{{ item.value }}</strong></div>
        <b>{{ item.change }}</b>
      </GlassPanel>
    </div>

    <div class="analytics-grid">
      <GlassPanel class="chart-card chart-wide">
        <div class="chart-title"><div><h2>入库 / 出库趋势</h2><span>库存流动量与节奏</span></div><LineChart :size="18" /></div>
        <BaseChart :option="trendOption" height="280px" />
      </GlassPanel>
      <GlassPanel class="chart-card">
        <div class="chart-title"><div><h2>操作量分布</h2><span>每日识别与库存操作</span></div><BarChart3 :size="18" /></div>
        <BaseChart :option="barOption" height="280px" />
      </GlassPanel>
      <GlassPanel class="chart-card">
        <div class="chart-title"><div><h2>库存分类占比</h2><span>水果 / 蔬菜结构</span></div><PieChart :size="18" /></div>
        <BaseChart :option="donutOption" height="240px" />
      </GlassPanel>
      <GlassPanel class="chart-card">
        <div class="chart-title"><div><h2>新鲜度分布</h2><span>模型分类结果</span></div><PieChart :size="18" /></div>
        <BaseChart :option="pieOption" height="240px" />
      </GlassPanel>
      <GlassPanel class="chart-card">
        <div class="chart-title"><div><h2>系统能力雷达</h2><span>六维综合评估</span></div><Radar :size="18" /></div>
        <BaseChart :option="radarOption" height="240px" />
      </GlassPanel>
      <GlassPanel class="chart-card chart-wide">
        <div class="chart-title"><div><h2>识别活跃热力图</h2><span>按星期与时段聚合</span></div><CalendarRange :size="18" /></div>
        <BaseChart :option="heatmapOption" height="240px" />
      </GlassPanel>
    </div>
  </div>
</template>

<style scoped>
.range-tabs { display: flex; padding: 3px; border: 1px solid var(--stroke); border-radius: 10px; background: var(--surface-soft); }.range-tabs button { padding: 7px 11px; border: 0; border-radius: 8px; color: var(--text-3); font-size: 9px; background: transparent; }.range-tabs button.active { color: white; background: linear-gradient(135deg, var(--blue), #6c63ff); }
.analysis-kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.analysis-kpi { display: grid; grid-template-columns: 40px 1fr auto; align-items: center; gap: 11px; }.kpi-icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 12px; }.analysis-kpi span, .analysis-kpi strong { display: block; }.analysis-kpi span { color: var(--text-3); font-size: 9px; }.analysis-kpi strong { margin-top: 5px; color: var(--text-1); font-size: 18px; }.analysis-kpi b { color: var(--green); font-size: 9px; }
.analytics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px; }.chart-wide { grid-column: span 2; }.chart-card { min-width: 0; }.chart-title { display: flex; align-items: flex-start; justify-content: space-between; color: var(--cyan); }.chart-title h2 { margin: 0; color: var(--text-1); font-size: 13px; }.chart-title span { display: block; margin-top: 5px; color: var(--text-3); font-size: 9px; }
@media (max-width: 1100px) { .analysis-kpis { grid-template-columns: 1fr 1fr; }.analytics-grid { grid-template-columns: 1fr 1fr; }.chart-wide { grid-column: span 2; } }
@media (max-width: 680px) { .analysis-kpis, .analytics-grid { grid-template-columns: 1fr; }.chart-wide { grid-column: auto; }.range-tabs { overflow-x: auto; } }
</style>
