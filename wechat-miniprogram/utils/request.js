const config = require('../config/index')
const mock = require('../mock/data')

function delay(data, ms = 220) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(JSON.parse(JSON.stringify(data))), ms)
  })
}

function mockRequest(options) {
  const { url, method = 'GET', data = {} } = options
  const route = `${method.toUpperCase()} ${url}`
  const handler = mock.routes[route] || mock.routes[`GET ${url}`]
  if (!handler) {
    return Promise.reject(new Error(`Mock接口未实现：${route}`))
  }
  return delay({ code: 0, message: 'ok', data: handler(data) })
}

function request(options) {
  if (config.enableMock) {
    return mockRequest(options)
  }

  const token = wx.getStorageSync('token')
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${config.baseUrl}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      timeout: config.timeout,
      header: {
        'content-type': 'application/json',
        Authorization: token ? `Bearer ${token}` : ''
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        reject(new Error(res.data && res.data.message ? res.data.message : '请求失败'))
      },
      fail(error) {
        wx.showToast({
          title: '当前网络不可用，正在展示最近一次同步数据',
          icon: 'none',
          duration: 2600
        })
        reject(error)
      }
    })
  })
}

module.exports = {
  request
}
