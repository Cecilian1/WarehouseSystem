import { http } from './http'
import type {
  AlertItem,
  ApiResponse,
  DashboardData,
  DeviceItem,
  EnvironmentPoint,
  HistoryItem,
  InventoryItem,
  PageResult,
  ProduceItem,
  ProducePayload,
  RecognitionRecord,
} from '@/types'

export const dashboardApi = {
  getOverview: () => http.get<never, ApiResponse<DashboardData>>('/dashboard'),
}

export const inventoryApi = {
  getList: (params: Record<string, unknown>) =>
    http.get<never, ApiResponse<PageResult<InventoryItem>>>('/inventory', { params }),
}

export const recognitionApi = {
  getList: () => http.get<never, ApiResponse<RecognitionRecord[]>>('/recognitions'),
}

export const environmentApi = {
  getCurrent: () =>
    http.get<never, ApiResponse<{ temperature: number; humidity: number; trend: EnvironmentPoint[] }>>('/environment'),
  getLatest: () =>
    http.get<never, ApiResponse<{ valid: boolean; temperature: number; humidity: number; isAbnormal: boolean; recordedAt: string }>>('/environment/latest'),
}

export const produceApi = {
  getList: () => http.get<never, ApiResponse<ProduceItem[]>>('/produce'),
  create: (payload: ProducePayload) => http.post<never, ApiResponse<ProduceItem>>('/produce', payload),
  update: (id: number, payload: ProducePayload) =>
    http.put<never, ApiResponse<ProduceItem>>(`/produce/${id}`, payload),
}

export const alertApi = {
  getList: (status = '') => http.get<never, ApiResponse<AlertItem[]>>('/alerts', { params: { status } }),
}

export const deviceApi = {
  getList: () => http.get<never, ApiResponse<DeviceItem[]>>('/devices'),
}

export const historyApi = {
  getList: (params: { page: number; pageSize: number }) =>
    http.get<never, ApiResponse<PageResult<HistoryItem>>>('/history', { params }),
}

export const analyticsApi = {
  getData: () => http.get<never, ApiResponse<Record<string, unknown>>>('/analytics'),
}

export const settingsApi = {
  save: (payload: Record<string, unknown>) =>
    http.post<never, ApiResponse<Record<string, unknown>>>('/settings', payload),
}
