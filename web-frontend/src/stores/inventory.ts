import { ref } from 'vue'
import { defineStore } from 'pinia'
import { inventoryApi } from '@/api'
import type { InventoryItem } from '@/types'

export const useInventoryStore = defineStore('inventory', () => {
  const list = ref<InventoryItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref('')
  const query = ref({ page: 1, pageSize: 10, keyword: '', category: '', freshness: '' })
  let refreshTimer: number | undefined
  let requestInFlight = false

  const loadList = async (showLoading: boolean) => {
    if (requestInFlight) return
    requestInFlight = true
    if (showLoading) loading.value = true
    try {
      const response = await inventoryApi.getList(query.value)
      list.value = response.data.list
      total.value = response.data.total
      error.value = ''
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : '库存数据刷新失败'
    } finally {
      if (showLoading) loading.value = false
      requestInFlight = false
    }
  }

  const fetchList = () => loadList(true)

  const startPolling = () => {
    if (refreshTimer !== undefined) return
    fetchList()
    refreshTimer = window.setInterval(() => { void loadList(false) }, 5000)
  }

  const stopPolling = () => {
    if (refreshTimer !== undefined) window.clearInterval(refreshTimer)
    refreshTimer = undefined
  }

  return { list, total, loading, error, query, fetchList, startPolling, stopPolling }
})
