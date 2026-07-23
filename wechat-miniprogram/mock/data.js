const now = new Date('2026-07-23T20:30:00+08:00')
const hour = 60 * 60 * 1000
const day = 24 * hour

function time(offset) {
  const date = new Date(now.getTime() + offset)
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const devices = [
  {
    id: 'fridge-01',
    name: '客厅智能冰箱',
    code: 'XXGJ-LS2K-0300-01',
    state: 'online',
    lastSync: '刚刚',
    temperature: 3.6,
    humidity: 88,
    cameraStatus: '正常采集',
    sensorStatus: '正常',
    firmware: 'v1.0.6',
    model: 'LoongArch 2K0300',
    storage: '7.6 GB 可用'
  },
  {
    id: 'fridge-02',
    name: '父母家冰箱',
    code: 'XXGJ-LS2K-0300-02',
    state: 'warning',
    lastSync: '18 分钟前',
    temperature: 8.4,
    humidity: 91,
    cameraStatus: '正常采集',
    sensorStatus: '温度偏高',
    firmware: 'v1.0.5',
    model: 'LoongArch 2K0300',
    storage: '5.2 GB 可用'
  },
  {
    id: 'fridge-03',
    name: '备用演示设备',
    code: 'XXGJ-DEMO-0300-03',
    state: 'offline',
    lastSync: '2 小时前',
    temperature: 0,
    humidity: 0,
    cameraStatus: '离线',
    sensorStatus: '离线',
    firmware: 'v0.9.8',
    model: 'LoongArch 2K0300',
    storage: '未知'
  }
]

const inventory = [
  {
    id: 1,
    name: '红富士苹果',
    category: '水果',
    quantity: 8,
    unit: '个',
    inboundAt: time(-6 * day),
    updatedAt: '10 分钟前',
    expireAt: time(8 * day),
    shelfLife: 14,
    remainingDays: 8,
    freshness: 'fresh',
    freshnessScore: 96,
    confidence: 98,
    location: 'A-01 上层',
    ideal: '0-4°C · 85-90%RH',
    exposure: '过去24小时温度稳定，未出现明显波动',
    advice: '保持冷藏，食用前清洗即可',
    color: '#cb6259',
    icon: 'apple'
  },
  {
    id: 2,
    name: '香蕉',
    category: '水果',
    quantity: 5,
    unit: '根',
    inboundAt: time(-3 * day),
    updatedAt: '26 分钟前',
    expireAt: time(2 * day),
    shelfLife: 5,
    remainingDays: 2,
    freshness: 'expiring',
    freshnessScore: 70,
    confidence: 93,
    location: 'A-02 上层',
    ideal: '8-12°C · 80-85%RH',
    exposure: '冷藏温度略低，表皮可能变暗',
    advice: '建议尽快食用，避免与苹果长时间放在一起',
    color: '#dbc56d',
    icon: 'banana'
  },
  {
    id: 3,
    name: '草莓',
    category: '水果',
    quantity: 2,
    unit: '盒',
    inboundAt: time(-4 * day),
    updatedAt: '35 分钟前',
    expireAt: time(1 * day),
    shelfLife: 5,
    remainingDays: 1,
    freshness: 'mild',
    freshnessScore: 62,
    confidence: 95,
    location: 'A-03 保鲜盒',
    ideal: '0-2°C · 90-95%RH',
    exposure: '湿度较高，建议检查是否有积水',
    advice: '请优先食用，清洗后尽快入口',
    color: '#be6674',
    icon: 'berry'
  },
  {
    id: 4,
    name: '橙子',
    category: '水果',
    quantity: 6,
    unit: '个',
    inboundAt: time(-2 * day),
    updatedAt: '1 小时前',
    expireAt: time(11 * day),
    shelfLife: 13,
    remainingDays: 11,
    freshness: 'fresh',
    freshnessScore: 94,
    confidence: 91,
    location: 'A-04 中层',
    ideal: '3-7°C · 85-90%RH',
    exposure: '环境稳定',
    advice: '可继续冷藏保存',
    color: '#d99555',
    icon: 'orange'
  },
  {
    id: 5,
    name: '西红柿',
    category: '蔬菜',
    quantity: 4,
    unit: '个',
    inboundAt: time(-5 * day),
    updatedAt: '12 分钟前',
    expireAt: time(2 * day),
    shelfLife: 7,
    remainingDays: 2,
    freshness: 'mild',
    freshnessScore: 66,
    confidence: 96,
    location: 'B-01 中层',
    ideal: '5-8°C · 85-90%RH',
    exposure: '18:20附近有短时升温',
    advice: '建议两天内做熟食用',
    color: '#cb6259',
    icon: 'tomato'
  },
  {
    id: 6,
    name: '黄瓜',
    category: '蔬菜',
    quantity: 7,
    unit: '根',
    inboundAt: time(-1 * day),
    updatedAt: '刚刚',
    expireAt: time(6 * day),
    shelfLife: 7,
    remainingDays: 6,
    freshness: 'fresh',
    freshnessScore: 92,
    confidence: 94,
    location: 'B-02 中层',
    ideal: '7-10°C · 90-95%RH',
    exposure: '温湿度适宜',
    advice: '用保鲜袋包裹可减少水分流失',
    color: '#5d9b73',
    icon: 'cucumber'
  },
  {
    id: 7,
    name: '菠菜',
    category: '蔬菜',
    quantity: 3,
    unit: '把',
    inboundAt: time(-4 * day),
    updatedAt: '43 分钟前',
    expireAt: time(0.5 * day),
    shelfLife: 4,
    remainingDays: 0,
    freshness: 'expiring',
    freshnessScore: 52,
    confidence: 90,
    location: 'C-01 保鲜抽屉',
    ideal: '0-2°C · 95%RH',
    exposure: '湿度偏高，叶片可能变软',
    advice: '建议今晚优先食用',
    color: '#5d9b73',
    icon: 'leaf'
  },
  {
    id: 8,
    name: '生菜',
    category: '蔬菜',
    quantity: 1,
    unit: '颗',
    inboundAt: time(-6 * day),
    updatedAt: '1 小时前',
    expireAt: time(-0.5 * day),
    shelfLife: 5,
    remainingDays: -1,
    freshness: 'spoiled',
    freshnessScore: 28,
    confidence: 89,
    location: 'C-02 保鲜抽屉',
    ideal: '0-2°C · 95%RH',
    exposure: '连续两次识别到叶片发黄',
    advice: '建议立即移出库存',
    color: '#7da45f',
    icon: 'lettuce'
  },
  {
    id: 9,
    name: '胡萝卜',
    category: '蔬菜',
    quantity: 10,
    unit: '根',
    inboundAt: time(-3 * day),
    updatedAt: '2 小时前',
    expireAt: time(15 * day),
    shelfLife: 18,
    remainingDays: 15,
    freshness: 'fresh',
    freshnessScore: 97,
    confidence: 97,
    location: 'C-03 下层',
    ideal: '0-4°C · 90-95%RH',
    exposure: '状态稳定',
    advice: '可继续保存，避免与叶菜挤压',
    color: '#d99555',
    icon: 'carrot'
  },
  {
    id: 10,
    name: '西兰花',
    category: '蔬菜',
    quantity: 2,
    unit: '颗',
    inboundAt: time(-2 * day),
    updatedAt: '22 分钟前',
    expireAt: time(5 * day),
    shelfLife: 7,
    remainingDays: 5,
    freshness: 'fresh',
    freshnessScore: 91,
    confidence: 96,
    location: 'B-03 中层',
    ideal: '0-3°C · 95%RH',
    exposure: '过去24小时稳定',
    advice: '建议保鲜袋密封冷藏',
    color: '#4f835e',
    icon: 'broccoli'
  }
]

const foodAlerts = [
  ['草莓将在1天后过期', '草莓剩余保质期较短，建议优先食用。', '草莓', 'expiring', 'warning'],
  ['生菜疑似腐败变质', 'AI识别到叶片发黄和边缘软化，建议移出库存。', '生菜', 'spoiled', 'critical'],
  ['菠菜今日需要处理', '菠菜剩余保质期不足1天，适合今晚烹饪。', '菠菜', 'expiring', 'warning'],
  ['西红柿新鲜度下降', '新鲜度评分降至66，请关注表皮状态。', '西红柿', 'freshness', 'warning'],
  ['香蕉即将成熟过度', '建议尽快食用，避免继续低温保存。', '香蕉', 'freshness', 'warning'],
  ['草莓湿度暴露偏高', '保鲜盒湿度连续偏高，可能影响口感。', '草莓', 'humidity', 'info'],
  ['苹果库存较多', '当前苹果有8个，可暂缓采购。', '红富士苹果', 'inventory', 'info'],
  ['橙子状态良好', '橙子新鲜度稳定，可继续保存。', '橙子', 'inventory', 'info']
]

const deviceAlerts = [
  ['温度持续偏高', '冰箱内温度超过8°C并持续10分钟，请检查冰箱门。', 'SHT30 环境传感器', 'temperature', 'critical'],
  ['摄像头短时离线', 'UVC摄像头最近一次心跳延迟，系统正在重试。', '冰箱内摄像头', 'device', 'warning'],
  ['存储空间不足提醒', '本地图片目录增长较快，建议定期清理历史帧。', '本地数据库', 'storage', 'warning'],
  ['设备同步延迟', '父母家冰箱18分钟前同步，建议确认网络状态。', '父母家冰箱', 'device', 'info']
]

const alerts = foodAlerts.concat(deviceAlerts).map((item, index) => ({
  id: index + 1,
  title: item[0],
  description: item[1],
  source: item[2],
  type: item[3],
  level: item[4],
  status: index < 5 ? 'pending' : index < 9 ? 'confirmed' : 'pending',
  time: time(-(index + 1) * hour),
  suggestion: item[4] === 'critical' ? '建议立即处理，并同步给家庭成员。' : '建议稍后查看详情并按需处理。'
}))

const records = Array.from({ length: 20 }, (_, index) => {
  const item = inventory[index % inventory.length]
  const isIn = index % 3 !== 1
  const manual = index % 5 === 0
  return {
    id: 8000 - index,
    time: time(-index * 3 * hour),
    produceId: item.id,
    name: item.name,
    type: manual ? 'manual' : isIn ? 'inbound' : 'outbound',
    action: manual ? '手动修正' : isIn ? '自动入库' : '自动出库',
    quantity: (index % 3) + 1,
    detail: manual ? `${item.name} 信息修正` : `${item.name} ${isIn ? '+' : '-'}${(index % 3) + 1}${item.unit}`,
    operator: manual ? '家庭成员' : 'Edge AI',
    status: index === 7 ? 'warning' : 'success',
    confidence: item.confidence,
    snapshot: item.icon
  }
})

const envTrend = Array.from({ length: 7 }, (_, dayIndex) => {
  const baseDate = new Date(now.getTime() - (6 - dayIndex) * day)
  const label = `${baseDate.getMonth() + 1}/${baseDate.getDate()}`
  return {
    date: label,
    tempMin: +(2.8 + Math.sin(dayIndex) * 0.3).toFixed(1),
    tempMax: +(5.4 + Math.cos(dayIndex / 1.5) * 1.2 + (dayIndex === 5 ? 3 : 0)).toFixed(1),
    humidityMin: 82 + (dayIndex % 3),
    humidityMax: 90 + (dayIndex % 4) + (dayIndex === 5 ? 5 : 0),
    points: Array.from({ length: 8 }, (_, pointIndex) => ({
      time: `${String(pointIndex * 3).padStart(2, '0')}:00`,
      temperature: +(3.4 + Math.sin((pointIndex + dayIndex) / 2) * 0.7 + (dayIndex === 5 && pointIndex === 6 ? 4 : 0)).toFixed(1),
      humidity: +(86 + Math.cos((pointIndex + dayIndex) / 2) * 4 + (dayIndex === 5 && pointIndex === 6 ? 8 : 0)).toFixed(1)
    }))
  }
})

const recognitionResult = {
  id: 3018,
  frameNo: 'PF-003018',
  time: time(-12 * 60 * 1000),
  status: 'completed',
  image: 'latest-frame',
  latency: 386,
  pipeline: [
    { key: 'capture', name: '图像采集中', done: true, cost: '72 ms' },
    { key: 'detect', name: '果蔬识别中', done: true, cost: '141 ms' },
    { key: 'freshness', name: '新鲜度分析中', done: true, cost: '96 ms' },
    { key: 'compare', name: '库存比对中', done: true, cost: '77 ms' },
    { key: 'done', name: '识别完成', done: true, cost: '已完成' }
  ],
  targets: [
    { id: 't1', name: '红富士苹果', category: '水果', quantity: 3, freshness: 'fresh', freshnessScore: 96, confidence: 98, x: 14, y: 28, w: 28, h: 26 },
    { id: 't2', name: '西兰花', category: '蔬菜', quantity: 1, freshness: 'fresh', freshnessScore: 91, confidence: 96, x: 56, y: 20, w: 25, h: 30 },
    { id: 't3', name: '西红柿', category: '蔬菜', quantity: 2, freshness: 'mild', freshnessScore: 66, confidence: 95, x: 48, y: 60, w: 30, h: 24 }
  ]
}

const messages = alerts.map((alert) => ({
  id: alert.id,
  title: alert.title,
  type: alert.type,
  time: alert.time,
  device: alert.type === 'device' || alert.type === 'temperature' || alert.type === 'storage' ? '客厅智能冰箱' : '',
  produce: alert.source,
  reason: alert.description,
  suggestion: alert.suggestion,
  status: alert.status
}))

function dashboard() {
  const freshCount = inventory.filter((item) => item.freshness === 'fresh').length
  const mildCount = inventory.filter((item) => item.freshness === 'mild').length
  const expiringCount = inventory.filter((item) => item.freshness === 'expiring').length
  const spoiledCount = inventory.filter((item) => item.freshness === 'spoiled').length
  const pendingAlerts = alerts.filter((item) => item.status === 'pending')
  return {
    greeting: '晚上好，今天也要记得及时享用新鲜食材',
    device: devices[0],
    environment: {
      temperature: 3.6,
      humidity: 88,
      state: '适宜',
      description: '温湿度稳定，适合果蔬冷藏',
      trend: envTrend[6].points
    },
    freshness: {
      fresh: freshCount,
      mild: mildCount,
      expiring: expiringCount,
      spoiled: spoiledCount
    },
    reminders: pendingAlerts.slice(0, 3),
    suggestions: [
      '建议优先食用草莓、菠菜和西红柿。',
      '当前蔬菜较充足，可暂缓采购叶菜。',
      '温度整体稳定，继续保持冰箱门及时关闭。'
    ],
    quickActions: [
      { title: '查看库存', path: '/pages/inventory/index', icon: 'box' },
      { title: '开始识别', path: '/pages/recognition/index', icon: 'scan' },
      { title: '手动入库', path: '/pages/inventory/index', icon: 'add' },
      { title: '查看预警', path: '/pages/alerts/index', icon: 'alert' }
    ]
  }
}

function getInventory(query = {}) {
  let list = inventory.slice()
  if (query.keyword) {
    list = list.filter((item) => `${item.name}${item.category}${item.location}`.includes(query.keyword))
  }
  if (query.category && query.category !== '全部') {
    list = list.filter((item) => item.category === query.category)
  }
  if (query.freshness && query.freshness !== '全部') {
    list = list.filter((item) => item.freshness === query.freshness)
  }
  if (query.sort === '保质期') {
    list.sort((a, b) => a.remainingDays - b.remainingDays)
  }
  if (query.sort === '新鲜度') {
    list.sort((a, b) => a.freshnessScore - b.freshnessScore)
  }
  if (query.sort === '入库时间') {
    list.sort((a, b) => new Date(b.inboundAt.replace(/-/g, '/')) - new Date(a.inboundAt.replace(/-/g, '/')))
  }
  return list
}

function getDetail(data = {}) {
  const item = inventory.find((food) => Number(food.id) === Number(data.id)) || inventory[0]
  return {
    ...item,
    timeline: records.filter((record) => record.produceId === item.id).slice(0, 5),
    latestSnapshot: recognitionResult.frameNo
  }
}

function getAlertList(query = {}) {
  let list = alerts.slice()
  if (query.level && query.level !== 'all') {
    list = list.filter((item) => item.level === query.level)
  }
  return list
}

const routes = {
  'POST /auth/wechat-login': () => ({
    token: 'mock-token',
    userInfo: {
      nickName: '芯鲜家庭',
      avatarUrl: '',
      familyName: '青屿之家'
    }
  }),
  'POST /devices/bind': (data) => ({
    success: true,
    deviceId: data.deviceCode || 'fridge-01'
  }),
  'GET /dashboard': dashboard,
  'GET /devices': () => devices,
  'GET /devices/status': (data) => devices.find((device) => device.id === data.deviceId) || devices[0],
  'GET /inventory': getInventory,
  'GET /inventory/detail': getDetail,
  'POST /inventory/inbound': (data) => ({ success: true, data }),
  'POST /inventory/outbound': (data) => ({ success: true, data }),
  'GET /recognitions/latest': () => recognitionResult,
  'POST /recognitions/confirm': (data) => ({ success: true, updated: data.targets ? data.targets.length : recognitionResult.targets.length }),
  'PUT /recognitions/target': (data) => ({ success: true, data }),
  'GET /alerts': getAlertList,
  'POST /alerts/handle': (data) => ({ success: true, id: data.id, action: data.action }),
  'GET /messages': () => messages,
  'GET /messages/detail': (data) => messages.find((item) => Number(item.id) === Number(data.id)) || messages[0],
  'GET /environment/current': () => ({
    temperature: 3.6,
    humidity: 88,
    state: '适宜',
    today: envTrend[6],
    analysis: '过去24小时温度整体稳定，但18:20至18:45出现短时升高，可能与冰箱门开启有关。'
  }),
  'GET /environment/history': () => envTrend,
  'GET /records': (query = {}) => {
    let list = records.slice()
    if (query.type && query.type !== '全部') list = list.filter((item) => item.type === query.type)
    if (query.keyword) list = list.filter((item) => `${item.name}${item.detail}`.includes(query.keyword))
    return list
  }
}

module.exports = {
  routes,
  inventory,
  devices,
  alerts,
  records,
  envTrend,
  recognitionResult,
  messages
}
