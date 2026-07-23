import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { dashboardApi } from '@/api'
import type { DashboardData } from '@/types'
import { realtimeSocket } from '@/utils/websocket'

export const useDashboardStore = defineStore('dashboard', () => {
  const data = ref<DashboardData | null>(null)
  const loading = ref(false)
  const lastUpdated = ref(new Date())
  const socketConnected = ref(false)
  let unsubscribe: (() => void) | undefined

  const environment = computed(() => data.value?.environment)
  const activeAlerts = computed(() => data.value?.metrics.find((item) => item.id === 'alerts')?.value || 0)

  const fetchOverview = async () => {
    loading.value = true
    try {
      const response = await dashboardApi.getOverview()
      data.value = response.data
      lastUpdated.value = new Date()
    } finally {
      loading.value = false
    }
  }

  const connectRealtime = () => {
    if (unsubscribe) return
    realtimeSocket.connect()
    socketConnected.value = realtimeSocket.isConnected()
    unsubscribe = realtimeSocket.on((event) => {
      if (!data.value) return
      if (event.type === 'environment:update') data.value.environment = event.payload
      if (event.type === 'inventory:update') {
        const stock = data.value.metrics.find((item) => item.id === 'stock')
        const alerts = data.value.metrics.find((item) => item.id === 'alerts')
        if (stock) stock.value = event.payload.stock
        if (alerts) alerts.value = event.payload.alerts
      }
      if (event.type === 'system:update') {
        const cpu = data.value.statuses.find((item) => item.id === 'cpu')
        const memory = data.value.statuses.find((item) => item.id === 'memory')
        const ws = data.value.statuses.find((item) => item.id === 'ws')
        if (cpu) cpu.value = event.payload.cpu
        if (memory) memory.value = event.payload.memory
        if (ws) ws.detail = event.payload.latency
      }
      lastUpdated.value = new Date()
      socketConnected.value = true
    })
  }

  const disconnectRealtime = () => {
    unsubscribe?.()
    unsubscribe = undefined
    realtimeSocket.disconnect()
    socketConnected.value = false
  }

  return {
    data,
    loading,
    lastUpdated,
    socketConnected,
    environment,
    activeAlerts,
    fetchOverview,
    connectRealtime,
    disconnectRealtime,
  }
})
