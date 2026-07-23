const { request } = require('../utils/request')

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
    return request({ url: '/dashboard', data: { deviceId } })
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
    return request({ url: '/inventory', data: query })
  },
  getDetail(id) {
    return request({ url: '/inventory/detail', data: { id } })
  },
  inbound(data) {
    return request({ url: '/inventory/inbound', method: 'POST', data })
  },
  outbound(data) {
    return request({ url: '/inventory/outbound', method: 'POST', data })
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
    return request({ url: '/records', data: query })
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
