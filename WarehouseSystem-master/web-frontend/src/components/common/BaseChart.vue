<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAppStore } from '@/stores/app'

const props = withDefaults(defineProps<{
  option: Record<string, any>
  height?: string
  autoresize?: boolean
}>(), {
  height: '240px',
  autoresize: true,
})

const chartRef = ref<HTMLDivElement>()
const appStore = useAppStore()
let chart: echarts.ECharts | undefined
let observer: ResizeObserver | undefined

const render = async () => {
  await nextTick()
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption(props.option as echarts.EChartsOption, { notMerge: true, lazyUpdate: true })
}

onMounted(() => {
  render()
  if (props.autoresize && chartRef.value) {
    observer = new ResizeObserver(() => chart?.resize())
    observer.observe(chartRef.value)
  }
})

watch(() => props.option, render, { deep: true })
watch(() => appStore.theme, () => {
  chart?.dispose()
  chart = undefined
  render()
})

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
})
</script>

<template>
  <div ref="chartRef" class="base-chart" :style="{ height }" />
</template>

<style scoped>
.base-chart { width: 100%; min-height: 80px; }
</style>
