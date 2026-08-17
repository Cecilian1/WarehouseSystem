const { request } = require('../utils/request')

function mapResponse(task, mapper) {
  return task.then((res) => ({ ...res, data: mapper(res.data) }))
}

function toPercent(value) {
  const number = Number(value || 0)
  return Math.max(0, Math.min(100, Math.round(number <= 1 ? number * 100 : number)))
}

function normalizeFreshness(value) {
  return value === 'warning' ? 'expiring' : value
}

function normalizeInventoryItem(item) {
  return {
    ...item,
    freshness: normalizeFreshness(item.freshness),
    freshnessScore: toPercent(item.freshnessScore),
    confidence: toPercent(item.confidence),
    storageAdvice: item.storageAdvice || item.ideal || '',
    ideal: item.ideal || item.storageAdvice || '',
    advice: item.advice || item.storageAdvice || '',
    updatedAt: item.updatedAt || item.inboundAt || ''
  }
}

function normalizeDashboard(data) {
  const freshness = { fresh: 0, mild: 0, expiring: 0, spoiled: 0 }
  if (Array.isArray(data.freshness)) {
    data.freshness.forEach((item) => {
      if (item.name.includes('新鲜')) freshness.fresh += Number(item.value || 0)
      else if (item.name.includes('腐败')) freshness.spoiled += Number(item.value || 0)
      else freshness.expiring += Number(item.value || 0)
    })
  } else if (data.freshness) {
    Object.assign(freshness, data.freshness)
  }

  const statuses = data.statuses || []
  const board = statuses.find((item) => item.id === 'board') || {}
  const camera = statuses.find((item) => item.id === 'camera') || {}
  const sensor = statuses.find((item) => item.id === 'sensor') || {}
  const environmentValid = Boolean(
    data.environment &&
    data.environment.valid !== false &&
    data.environment.temperatureState !== 'offline'
  )
  return {
    ...data,
    device: data.device || {
      id: 'fridge-01',
      code: 'fridge-01',
      name: 'ATK-DL2K0300 开发板',
      state: board.state || 'offline',
      cameraStatus: camera.value || '未上报',
      sensorStatus: sensor.value || '未上报',
      lastSync: camera.detail || board.detail || '暂无'
    },
    environment: {
      ...data.environment,
      valid: environmentValid,
      state: !environmentValid
        ? '未上报'
        : data.environment.temperatureState === 'warning' ? '异常' : '适宜',
      description: environmentValid
        ? '数据来自开发板环境采集服务'
        : '温湿度传感器尚未连接'
    },
    freshness,
    reminders: data.reminders || [],
    suggestions: data.suggestions || [],
    quickActions: data.quickActions || []
  }
}

const authService = {
  loginByWechat(data) {
    return request({ url: '/auth/wechat-login', method: 'POST', data })
  },
  bindDevice(data) {
    return request({ url: '/devices/bind', method: 'POST', data })
  }
}

const dashboardService = {
  getOverview(deviceId) {
    return mapResponse(
      request({ url: '/dashboard', data: { deviceId } }),
      normalizeDashboard
    )
  }
}

const deviceService = {
  getList() {
    return request({ url: '/devices' })
  },
  getStatus(deviceId) {
    return request({ url: '/devices/status', data: { deviceId } })
  }
}

const inventoryService = {
  getList(query = {}) {
    const params = {
      ...query,
      category: query.category === '全部' ? '' : query.category,
      freshness: query.freshness === '全部' ? '' : query.freshness,
      pageSize: 100
    }
    return mapResponse(request({ url: '/inventory', data: params }), (data) => {
      const list = Array.isArray(data) ? data : data.list || []
      return list.map(normalizeInventoryItem)
    })
  },
  getDetail(id) {
    return mapResponse(
      request({ url: '/inventory/detail', data: { id } }),
      normalizeInventoryItem
    )
  },
  inbound(data) {
    return request({ url: '/inventory/inbound', method: 'POST', data })
  },
  update(id, data) {
    return request({ url: `/inventory/${id}`, method: 'PUT', data })
  },
  outbound(data) {
    return request({
      url: '/inventory/outbound',
      method: 'POST',
      data: { ...data, produceId: data.produceId || data.id }
    })
  },
  remove(id) {
    return request({ url: `/inventory/${id}`, method: 'DELETE' })
  }
}

const recognitionService = {
  getResult() {
    return request({ url: '/recognitions/latest' })
  },
  confirm(data) {
    return request({ url: '/recognitions/confirm', method: 'POST', data })
  },
  updateTarget(data) {
    return request({ url: '/recognitions/target', method: 'PUT', data })
  }
}

const alertService = {
  getList(query = {}) {
    return request({ url: '/alerts', data: query })
  },
  handle(data) {
    return request({ url: '/alerts/handle', method: 'POST', data })
  },
  getMessages() {
    return request({ url: '/messages' })
  },
  getMessageDetail(id) {
    return request({ url: '/messages/detail', data: { id } })
  }
}

const environmentService = {
  getCurrent(deviceId) {
    return request({ url: '/environment/current', data: { deviceId } })
  },
  getHistory(range = '7d') {
    return request({ url: '/environment/history', data: { range } })
  }
}

const recordService = {
  getList(query = {}) {
    return mapResponse(request({ url: '/records', data: query }), (data) => {
      const rows = Array.isArray(data) ? data : (data && data.list) || []
      const list = rows.map((item) => ({
        ...item,
        confidence: toPercent(item.confidence)
      }))
      if (Array.isArray(data)) {
        return { list, total: list.length, page: 1, pageSize: list.length }
      }
      return {
        list,
        total: Number(data && data.total) || list.length,
        page: Number(data && data.page) || 1,
        pageSize: Number(data && data.pageSize) || list.length
      }
    })
  }
}

module.exports = {
  authService,
  dashboardService,
  deviceService,
  inventoryService,
  recognitionService,
  alertService,
  environmentService,
  recordService
}
