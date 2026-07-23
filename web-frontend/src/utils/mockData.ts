import type {
  AlertItem,
  DashboardData,
  DeviceItem,
  HistoryItem,
  InventoryItem,
  RecognitionRecord,
} from '@/types'

const now = new Date('2026-07-20T20:30:00+08:00')
const minute = 60 * 1000
const hour = 60 * minute

const timeLabel = (offset: number) =>
  new Date(now.getTime() + offset).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })

export const inventoryItems: InventoryItem[] = [
  { id: 1, name: '红富士苹果', category: '水果', quantity: 18, unit: '个', shelfLife: 21, remainingDays: 12, freshness: 'fresh', freshnessScore: 0.96, storageAdvice: '0-4°C · 85-90%RH', inboundAt: '2026-07-16 10:24', location: 'A-01 上层', color: '#ef4444' },
  { id: 2, name: '云南蓝莓', category: '水果', quantity: 6, unit: '盒', shelfLife: 10, remainingDays: 2, freshness: 'warning', freshnessScore: 0.72, storageAdvice: '1-3°C · 90-95%RH', inboundAt: '2026-07-12 17:08', location: 'A-02 保鲜盒', color: '#6366f1' },
  { id: 3, name: '西兰花', category: '蔬菜', quantity: 4, unit: '颗', shelfLife: 7, remainingDays: 4, freshness: 'fresh', freshnessScore: 0.91, storageAdvice: '0-3°C · 95%RH', inboundAt: '2026-07-17 08:42', location: 'B-01 中层', color: '#22c55e' },
  { id: 4, name: '番茄', category: '蔬菜', quantity: 9, unit: '个', shelfLife: 8, remainingDays: 1, freshness: 'warning', freshnessScore: 0.64, storageAdvice: '5-8°C · 85-90%RH', inboundAt: '2026-07-14 14:30', location: 'B-02 中层', color: '#f97316' },
  { id: 5, name: '黄瓜', category: '蔬菜', quantity: 7, unit: '根', shelfLife: 7, remainingDays: 5, freshness: 'fresh', freshnessScore: 0.93, storageAdvice: '7-10°C · 90-95%RH', inboundAt: '2026-07-18 09:12', location: 'C-01 下层', color: '#14b8a6' },
  { id: 6, name: '生菜', category: '蔬菜', quantity: 3, unit: '颗', shelfLife: 5, remainingDays: 0, freshness: 'spoiled', freshnessScore: 0.28, storageAdvice: '0-2°C · 95%RH', inboundAt: '2026-07-14 11:20', location: 'C-02 保鲜抽屉', color: '#84cc16' },
  { id: 7, name: '阳光玫瑰', category: '水果', quantity: 2, unit: '串', shelfLife: 12, remainingDays: 7, freshness: 'fresh', freshnessScore: 0.95, storageAdvice: '0-2°C · 90-95%RH', inboundAt: '2026-07-15 18:05', location: 'A-03 上层', color: '#a3e635' },
  { id: 8, name: '胡萝卜', category: '蔬菜', quantity: 11, unit: '根', shelfLife: 18, remainingDays: 13, freshness: 'fresh', freshnessScore: 0.97, storageAdvice: '0-4°C · 90-95%RH', inboundAt: '2026-07-15 09:40', location: 'C-03 下层', color: '#f59e0b' },
  { id: 9, name: '猕猴桃', category: '水果', quantity: 5, unit: '个', shelfLife: 14, remainingDays: 3, freshness: 'warning', freshnessScore: 0.68, storageAdvice: '0-4°C · 90-95%RH', inboundAt: '2026-07-09 16:18', location: 'A-04 上层', color: '#65a30d' },
  { id: 10, name: '彩椒', category: '蔬菜', quantity: 6, unit: '个', shelfLife: 10, remainingDays: 8, freshness: 'fresh', freshnessScore: 0.94, storageAdvice: '7-10°C · 90-95%RH', inboundAt: '2026-07-18 15:36', location: 'B-03 中层', color: '#eab308' },
]

export const recognitionRecords: RecognitionRecord[] = [
  { id: 3018, time: '20:29:42', name: '红富士苹果', category: '水果', quantity: 3, action: 'IN', confidence: 0.982, freshness: 'fresh', freshnessScore: 0.961, latency: 386 },
  { id: 3017, time: '20:26:17', name: '番茄', category: '蔬菜', quantity: 2, action: 'OUT', confidence: 0.947, freshness: 'warning', freshnessScore: 0.684, latency: 412 },
  { id: 3016, time: '20:22:08', name: '西兰花', category: '蔬菜', quantity: 1, action: 'IN', confidence: 0.963, freshness: 'fresh', freshnessScore: 0.918, latency: 398 },
  { id: 3015, time: '20:18:33', name: '黄瓜', category: '蔬菜', quantity: 2, action: 'IN', confidence: 0.931, freshness: 'fresh', freshnessScore: 0.936, latency: 374 },
  { id: 3014, time: '20:12:54', name: '云南蓝莓', category: '水果', quantity: 1, action: 'OUT', confidence: 0.914, freshness: 'warning', freshnessScore: 0.721, latency: 429 },
]

export const dashboardData: DashboardData = {
  statuses: [
    { id: 'board', label: 'LoongArch 2K2000-i', value: '在线', state: 'online', detail: '运行 12天 08:42' },
    { id: 'cpu', label: 'CPU', value: '38%', state: 'online', detail: '1.4 GHz · 2 核' },
    { id: 'memory', label: '内存', value: '52%', state: 'online', detail: '2.08 / 4 GB' },
    { id: 'sqlite', label: 'SQLite', value: '正常', state: 'online', detail: 'WAL · 128 MB' },
    { id: 'model', label: 'AI 模型', value: '已加载', state: 'online', detail: 'YOLOv11 + MobileNetV3' },
    { id: 'camera', label: '摄像头', value: '采集中', state: 'online', detail: '640 × 480 · 12 FPS' },
    { id: 'ws', label: 'WebSocket', value: '实时', state: 'online', detail: '18 ms' },
  ],
  metrics: [
    { id: 'stock', label: '库存总量', value: 71, unit: '件', change: 8.4, tone: 'blue' },
    { id: 'today', label: '今日新增', value: 18, unit: '件', change: 12.5, tone: 'cyan' },
    { id: 'expiring', label: '即将过期', value: 8, unit: '件', change: -2.1, tone: 'orange' },
    { id: 'alerts', label: '异常预警', value: 3, unit: '项', change: -25, tone: 'red' },
  ],
  environment: {
    temperature: 3.6,
    humidity: 88,
    temperatureState: 'online',
    humidityState: 'online',
    trend: Array.from({ length: 16 }, (_, index) => ({
      time: timeLabel((index - 15) * 15 * minute),
      temperature: +(3.3 + Math.sin(index / 2.3) * 0.45 + (index % 3) * 0.08).toFixed(1),
      humidity: +(87 + Math.cos(index / 2.7) * 2.2 + (index % 2) * 0.6).toFixed(1),
    })),
  },
  detections: [
    { id: 'd1', label: 'Apple × 3', confidence: 0.982, freshness: 'fresh', freshnessScore: 0.961, x: 12, y: 28, width: 28, height: 32 },
    { id: 'd2', label: 'Broccoli × 1', confidence: 0.963, freshness: 'fresh', freshnessScore: 0.918, x: 55, y: 18, width: 28, height: 36 },
    { id: 'd3', label: 'Tomato × 2', confidence: 0.947, freshness: 'warning', freshnessScore: 0.684, x: 48, y: 60, width: 25, height: 25 },
  ],
  recognitions: recognitionRecords,
  categories: [
    { name: '蔬菜', value: 40, color: '#22c55e' },
    { name: '水果', value: 31, color: '#4f8cff' },
  ],
  freshness: [
    { name: '新鲜', value: 56, color: '#22c55e' },
    { name: '临期', value: 12, color: '#f59e0b' },
    { name: '腐败', value: 3, color: '#ef4444' },
  ],
  stockTrend: Array.from({ length: 12 }, (_, index) => ({
    time: timeLabel((index - 11) * hour * 2),
    inbound: 5 + Math.round(Math.sin(index / 1.6) * 3 + (index % 4)),
    outbound: 3 + Math.round(Math.cos(index / 2.1) * 2 + (index % 3)),
  })),
  performance: {
    fps: 12,
    latency: 386,
    model: 'INT8',
    power: 8.6,
  },
}

export const alerts: AlertItem[] = [
  { id: 1, title: '生菜新鲜度低于安全阈值', type: 'spoiled', level: 'critical', source: 'C-02 保鲜抽屉', description: 'MobileNetV3 新鲜度评分 0.28，建议立即移出库存。', time: '2026-07-20 20:18:32', status: 'pending' },
  { id: 2, title: '番茄将在 24 小时内到期', type: 'expiring', level: 'warning', source: 'B-02 中层', description: '当前库存 9 个，建议优先使用或调整储存位置。', time: '2026-07-20 19:55:06', status: 'pending' },
  { id: 3, title: '湿度短时高于设定阈值', type: 'humidity', level: 'warning', source: 'SHT30 环境传感器', description: '湿度峰值 96.2%RH，持续 4 分 28 秒后恢复。', time: '2026-07-20 18:42:17', status: 'confirmed' },
  { id: 4, title: '摄像头采集延迟波动', type: 'device', level: 'info', source: 'UVC Camera /dev/video0', description: '连续三帧采集延迟超过 600ms，系统已自动恢复。', time: '2026-07-20 17:21:49', status: 'confirmed' },
  { id: 5, title: '云南蓝莓即将到期', type: 'expiring', level: 'warning', source: 'A-02 保鲜盒', description: '剩余保质期 2 天，当前新鲜度评分 0.72。', time: '2026-07-20 15:05:22', status: 'ignored' },
  { id: 6, title: '温度超过 8°C 预警线', type: 'temperature', level: 'critical', source: 'SHT30 环境传感器', description: '冰箱门开启导致温度上升，持续 11 分钟后恢复。', time: '2026-07-19 21:34:08', status: 'confirmed' },
]

export const devices: DeviceItem[] = [
  { id: 'board-01', name: '龙芯开发板', type: '边缘计算节点', model: 'Loongson 2K2000-i', state: 'online', uptime: 99.98, value: '38% CPU', detail: 'LA364 双核 · 1.4GHz · Loongnix', lastHeartbeat: '刚刚' },
  { id: 'camera-01', name: '冰箱内摄像头', type: '视觉采集', model: 'UVC Camera', state: 'online', uptime: 99.82, value: '12 FPS', detail: '640×480 · /dev/video0', lastHeartbeat: '3 秒前' },
  { id: 'sensor-01', name: '温湿度传感器', type: '环境感知', model: 'SHT30', state: 'online', uptime: 99.95, value: '3.6°C / 88%', detail: 'I2C3 · 0x44', lastHeartbeat: '8 秒前' },
  { id: 'led-01', name: '视觉补光灯', type: '执行器', model: 'GPIO LED', state: 'online', uptime: 99.90, value: '自动', detail: 'GPIO 74 · 触发式补光', lastHeartbeat: '12 秒前' },
  { id: 'storage-01', name: '本地数据库', type: '数据存储', model: 'SQLite 3', state: 'online', uptime: 100, value: '7.6 GB 可用', detail: 'WAL 模式 · 128 MB', lastHeartbeat: '刚刚' },
  { id: 'network-01', name: '边缘网络', type: '网络通信', model: 'Gigabit Ethernet', state: 'warning', uptime: 98.74, value: '18 ms', detail: '192.168.1.26 · 云同步正常', lastHeartbeat: '18 秒前' },
]

export const historyItems: HistoryItem[] = Array.from({ length: 32 }, (_, index) => {
  const isInventory = index % 3 !== 2
  const action = isInventory ? (index % 2 ? '自动出库' : '自动入库') : '环境采样'
  return {
    id: 8000 - index,
    time: new Date(now.getTime() - index * 42 * minute).toLocaleString('zh-CN', { hour12: false }),
    module: isInventory ? 'AI 识别' : '环境监测',
    action,
    detail: isInventory
      ? `${inventoryItems[index % inventoryItems.length].name} ${index % 2 ? '-' : '+'}${(index % 4) + 1} 件`
      : `温度 ${(3.2 + (index % 6) * 0.2).toFixed(1)}°C，湿度 ${84 + (index % 8)}%RH`,
    operator: isInventory ? 'Edge AI' : 'SHT30',
    status: index === 11 ? 'warning' : 'success',
  }
})

export const analyticsData = {
  daily: Array.from({ length: 14 }, (_, index) => ({
    date: `${String(index + 7).padStart(2, '0')}日`,
    inbound: 12 + Math.round(Math.sin(index / 1.7) * 7 + (index % 5)),
    outbound: 9 + Math.round(Math.cos(index / 2.1) * 5 + (index % 3)),
    waste: +(3.4 + Math.sin(index / 2.4) * 1.8).toFixed(1),
  })),
  categories: dashboardData.categories,
  freshness: dashboardData.freshness,
  radar: [
    { name: '识别准确率', value: 96 },
    { name: '库存周转率', value: 82 },
    { name: '环境稳定度', value: 94 },
    { name: '设备在线率', value: 99 },
    { name: '预警及时率', value: 91 },
    { name: '节约率', value: 78 },
  ],
  heatmap: Array.from({ length: 7 * 12 }, (_, index) => [
    index % 12,
    Math.floor(index / 12),
    Math.max(0, Math.round(4 + Math.sin(index / 5) * 3 + (index % 4))),
  ]),
}
