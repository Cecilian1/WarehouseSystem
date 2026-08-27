import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { environmentApi } from '@/api'

export const useBoardStore = defineStore('board', () => {
  const temperature = ref<number | null>(null)
  const humidity = ref<number | null>(null)
  const hasData = ref(false)
  const abnormal = ref(false)
  const recordedAt = ref('')
  let timer: number | undefined

  const temperatureText = computed(() => temperature.value === null ? '暂无数据' : `${temperature.value.toFixed(1)}℃`)
  const humidityText = computed(() => humidity.value === null ? '暂无数据' : `${humidity.value.toFixed(1)}%RH`)
  const state = computed(() => !hasData.value ? 'empty' : abnormal.value ? 'warning' : 'normal')
  const statusText = computed(() => !hasData.value ? '暂无数据' : abnormal.value ? '异常' : '正常')

  const refresh = async () => {
    try {
      const response = await environmentApi.getLatest()
      hasData.value = response.data.valid
      temperature.value = response.data.valid ? response.data.temperature : null
      humidity.value = response.data.valid ? response.data.humidity : null
      abnormal.value = response.data.isAbnormal
      recordedAt.value = response.data.recordedAt
    } catch {
      hasData.value = false
      temperature.value = null
      humidity.value = null
      recordedAt.value = ''
    }
  }

  const startPolling = () => {
    if (timer) return
    refresh()
    timer = window.setInterval(refresh, 2000)
  }

  const stopPolling = () => {
    if (timer) window.clearInterval(timer)
    timer = undefined
  }

  return {
    temperature,
    humidity,
    hasData,
    abnormal,
    recordedAt,
    temperatureText,
    humidityText,
    state,
    statusText,
    refresh,
    startPolling,
    stopPolling,
  }
})
