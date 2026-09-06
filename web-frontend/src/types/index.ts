export type ThemeMode = 'dark' | 'light'
export type FreshnessLevel = 'fresh' | 'warning' | 'spoiled'
export type AlertLevel = 'info' | 'warning' | 'critical'
export type DeviceState = 'online' | 'warning' | 'offline'

export interface TrendPoint {
  time: string
  value: number
}

export interface EnvironmentPoint {
  time: string
  temperature: number
  humidity: number
  isAbnormal?: boolean
  sampleCount?: number
  abnormalCount?: number
}

export interface EnvironmentMetricSummary {
  min: number
  max: number
  average: number
  stddev: number
}

export interface EnvironmentData {
  valid: boolean
  temperature: number
  humidity: number
  temperatureState: DeviceState
  humidityState: DeviceState
  recordedAt: string
  range: '6h' | '24h' | '7d'
  trend: EnvironmentPoint[]
  summary: {
    sampleCount: number
    abnormalCount: number
    temperature: EnvironmentMetricSummary
    humidity: EnvironmentMetricSummary
  }
}

export interface AnalyticsData {
  range: 'today' | 'week' | 'month' | 'year'
  kpis: {
    accuracy: number
    recognitionCount: number
    turnover: number
    savingRate: number
    avgCycle: number
    totalInbound: number
    totalOutbound: number
  }
  daily: Array<{ date: string; inbound: number; outbound: number; waste?: number }>
  categories: CategoryStat[]
  freshness: CategoryStat[]
  radar: Array<{ name: string; value: number }>
  heatmap: number[][]
}

export interface StatusItem {
  id: string
  label: string
  value: string
  state: DeviceState
  detail?: string
}

export interface MetricItem {
  id: string
  label: string
  value: number
  unit?: string
  change: number
  tone: 'blue' | 'cyan' | 'green' | 'orange' | 'red' | 'purple'
}

export interface DetectionBox {
  id: string
  label: string
  confidence: number
  freshness: FreshnessLevel
  freshnessScore: number
  x: number
  y: number
  width: number
  height: number
}

export interface RecognitionRecord {
  id: number
  time: string
  createdAt?: string
  produceId?: number
  name: string
  category: string
  quantity: number
  action: 'IN' | 'OUT'
  confidence: number
  freshness: FreshnessLevel
  freshnessScore: number
  image?: string
  latency: number
}

export interface CategoryStat {
  name: string
  value: number
  color: string
}

export interface DashboardData {
  statuses: StatusItem[]
  metrics: MetricItem[]
  environment: {
    valid?: boolean
    temperature: number
    humidity: number
    temperatureState: DeviceState
    humidityState: DeviceState
    recordedAt?: string
    trend: EnvironmentPoint[]
  }
  detections: DetectionBox[]
  recognitions: RecognitionRecord[]
  categories: CategoryStat[]
  freshness: CategoryStat[]
  stockTrend: Array<{ time: string; inbound: number; outbound: number }>
  performance: {
    fps: number
    latency: number
    model: string
    power: number
  }
}

export interface InventoryItem {
  id: number
  name: string
  category: '水果' | '蔬菜'
  quantity: number
  unit: string
  shelfLife: number
  remainingDays: number
  freshness: FreshnessLevel
  freshnessScore: number
  storageAdvice: string
  inboundAt: string
  location: string
  color: string
}

export interface ProduceItem {
  id: number
  name: string
  category: string
  shelfLifeDays: number
  idealTempRange: string
  iconUrl: string
  currentQty: number
  earliestExpireDate: string
}

export interface ProducePayload {
  name: string
  category: string
  shelfLifeDays: number
  idealTempRange: string
  iconUrl: string
  unit?: string
  location?: string
}

export interface InventoryMutationPayload {
  name: string
  category: string
  quantity: number
  unit: string
  shelfLife: number
  storageAdvice: string
  location: string
  iconUrl?: string
}

export interface AlertItem {
  id: number
  title: string
  type: 'expiring' | 'spoiled' | 'device' | 'temperature' | 'humidity'
  level: AlertLevel
  source: string
  description: string
  time: string
  status: 'pending' | 'confirmed' | 'ignored'
}

export interface DeviceItem {
  id: string
  name: string
  type: string
  model: string
  state: DeviceState
  uptime: number
  value: string
  detail: string
  lastHeartbeat: string
}

export interface HistoryItem {
  id: number
  time: string
  module: string
  action: string
  detail: string
  operator: string
  status: 'success' | 'warning' | 'failed'
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}
