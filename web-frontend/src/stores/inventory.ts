import { ref } from 'vue'
import { defineStore } from 'pinia'
import { inventoryApi } from '@/api'
import type { InventoryItem } from '@/types'

export const useInventoryStore = defineStore('inventory', () => {
  const list = ref<InventoryItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const query = ref({ page: 1, pageSize: 10, keyword: '', category: '', freshness: '' })

  const fetchList = async () => {
    loading.value = true
    try {
      const response = await inventoryApi.getList(query.value)
      list.value = response.data.list
      total.value = response.data.total
    } finally {
      loading.value = false
    }
  }

  return { list, total, loading, query, fetchList }
})
