const { environmentService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')

function envTone(state) {
  if (state === '异常') return 'warn'
  if (state === '适宜') return 'ok'
  return 'off'
}

function displayValue(value) {
  if (value === 0 || value === '0') return 0
  return value === undefined || value === null || value === '' ? '--' : value
}

function normalizeCurrent(raw) {
  const data = raw || {}
  const today = data.today || {}
  const offline = data.valid === false || data.state === '未上报'
  const state = offline ? '未上报' : (data.state || '未上报')
  return {
    temperature: offline ? '--' : displayValue(data.temperature),
    humidity: offline ? '--' : displayValue(data.humidity),
    state,
    tone: envTone(state),
    analysis: data.analysis || (offline ? '暂无环境采集数据，请检查开发板连接。' : '暂无环境分析'),
    today: {
      tempMax: displayValue(today.tempMax),
      tempMin: displayValue(today.tempMin),
      humidityMax: displayValue(today.humidityMax),
      humidityMin: displayValue(today.humidityMin)
    }
  }
}

function normalizeHistory(rows) {
  const list = Array.isArray(rows) ? rows : []
  const maxTemp = Math.max(1, ...list.map((item) => Number(item.tempMax) || 0))
  const maxHumidity = Math.max(1, ...list.map((item) => Number(item.humidityMax) || 0))
  return list.map((item) => ({
    ...item,
    date: item.date || '',
    tempHeight: Math.max(16, Math.round(((Number(item.tempMax) || 0) / maxTemp) * 180)),
    humidityHeight: Math.max(16, Math.round(((Number(item.humidityMax) || 0) / maxHumidity) * 180))
  }))
}

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    current: null,
    history: [],
    range: '7天',
    ranges: ['今日', '7天', '30天']
  },
  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    applyPageTheme(this)
    this.load()
  },
  onShow() {
    applyPageTheme(this)
  },
  load() {
    return Promise.all([
      environmentService.getCurrent('fridge-01'),
      environmentService.getHistory(this.data.range)
    ]).then(([current, history]) => {
      this.setData({
        current: normalizeCurrent(current && current.data),
        history: normalizeHistory(history && history.data)
      })
    }).catch(() => {
      this.setData({
        current: normalizeCurrent({ state: '未上报', valid: false }),
        history: []
      })
    })
  },
  selectRange(event) {
    this.setData({ range: event.currentTarget.dataset.value }, () => this.load())
  },
  back() {
    wx.navigateBack()
  }
})
