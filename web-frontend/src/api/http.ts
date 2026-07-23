import axios, {
  type AxiosAdapter,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { alerts, analyticsData, dashboardData, devices, historyItems, inventoryItems, recognitionRecords } from '@/utils/mockData'
import type { ApiResponse, PageResult } from '@/types'

const useMock = import.meta.env.VITE_USE_MOCK !== 'false'
const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

const ok = <T>(config: InternalAxiosRequestConfig, data: T): AxiosResponse<ApiResponse<T>> => ({
  data: { code: 0, message: 'ok', data },
  status: 200,
  statusText: 'OK',
  headers: {},
  config,
})

const mockAdapter: AxiosAdapter = async (config) => {
  await wait(180 + Math.random() * 220)
  const url = config.url || ''
  const params = config.params || {}

  if (url === '/dashboard') return ok(config, structuredClone(dashboardData))
  if (url === '/recognitions') return ok(config, structuredClone(recognitionRecords))
  if (url === '/devices') return ok(config, structuredClone(devices))
  if (url === '/analytics') return ok(config, structuredClone(analyticsData))
  if (url === '/environment') return ok(config, structuredClone(dashboardData.environment))
  if (url === '/settings' && config.method === 'post') return ok(config, JSON.parse(config.data || '{}'))

  if (url === '/inventory') {
    const page = Number(params.page || 1)
    const pageSize = Number(params.pageSize || 10)
    const keyword = String(params.keyword || '').trim().toLowerCase()
    const category = String(params.category || '')
    const freshness = String(params.freshness || '')
    const filtered = inventoryItems.filter((item) => {
      const matchesKeyword = !keyword || `${item.name}${item.category}${item.location}`.toLowerCase().includes(keyword)
      return matchesKeyword && (!category || item.category === category) && (!freshness || item.freshness === freshness)
    })
    const result: PageResult<(typeof inventoryItems)[number]> = {
      list: filtered.slice((page - 1) * pageSize, page * pageSize),
      total: filtered.length,
      page,
      pageSize,
    }
    return ok(config, structuredClone(result))
  }

  if (url === '/alerts') {
    const status = String(params.status || '')
    return ok(config, structuredClone(status ? alerts.filter((item) => item.status === status) : alerts))
  }

  if (url === '/history') {
    const page = Number(params.page || 1)
    const pageSize = Number(params.pageSize || 10)
    return ok(config, {
      list: structuredClone(historyItems.slice((page - 1) * pageSize, page * pageSize)),
      total: historyItems.length,
      page,
      pageSize,
    })
  }

  return Promise.reject(new Error(`Mock route not found: ${config.method?.toUpperCase()} ${url}`))
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  adapter: useMock ? mockAdapter : undefined,
})

http.interceptors.request.use((config) => {
  config.headers['X-Device-ID'] = 'fridge-01'
  return config
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error),
)
