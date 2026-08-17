const { dashboardService } = require('../../services/api')
const { applyPageTheme, FRESHNESS_COLORS } = require('../../utils/theme')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    overview: {
      device: { name: '读取设备中', state: 'offline', cameraStatus: '等待上报', sensorStatus: '等待上报', code: '', lastSync: '暂无' },
      environment: { state: '适宜', temperature: 0, humidity: 0, description: '正在读取环境数据', trend: [] },
      freshness: { fresh: 0, mild: 0, expiring: 0, spoiled: 0 },
      reminders: [],
      suggestions: [],
      quickActions: [],
      statuses: [],
      categories: [],
      recognitions: []
    },
    loading: true,
    freshnessBars: [],
    metrics: [],
    categoryGradient: '',
    categoryTotal: 0,
    stockBars: [],
    netFlowText: '+0',
    themeClass: 'theme-dark'
  },
  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    applyPageTheme(this)
  },
  onShow() {
    applyPageTheme(this)
    this.load()
  },
  onPullDownRefresh() {
    this.load().finally(() => wx.stopPullDownRefresh())
  },
  load() {
    this.setData({ loading: true })
    return dashboardService.getOverview('fridge-01').then((res) => {
      const freshness = res.data.freshness
      const total = Math.max(1, freshness.fresh + freshness.mild + freshness.expiring + freshness.spoiled)

      const metrics = (res.data.metrics || []).map((item) => ({
        ...item,
        changeAbs: Math.abs(item.change),
        up: item.change >= 0
      }))

      const categories = res.data.categories || []
      const categoryTotal = categories.reduce((sum, item) => sum + item.value, 0)
      let angleStart = 0
      const categoryGradient = categories.map((item) => {
        const angle = categoryTotal ? (item.value / categoryTotal) * 360 : 0
        const segment = `${item.color} ${angleStart}deg ${angleStart + angle}deg`
        angleStart += angle
        return segment
      }).join(', ')

      const stockTrend = res.data.stockTrend || []
      const maxFlow = Math.max(1, ...stockTrend.map((point) => Math.max(point.inbound, point.outbound)))
      const stockBars = stockTrend.map((point) => ({
        time: point.time,
        inboundHeight: Math.max(8, Math.round((point.inbound / maxFlow) * 160)),
        outboundHeight: Math.max(8, Math.round((point.outbound / maxFlow) * 160))
      }))
      const netFlow = stockTrend.reduce((sum, point) => sum + point.inbound - point.outbound, 0)

      this.setData({
        overview: res.data,
        freshnessBars: [
          { key: 'fresh', label: '新鲜', value: freshness.fresh, width: freshness.fresh / total * 100, color: FRESHNESS_COLORS.fresh },
          { key: 'mild', label: '轻度', value: freshness.mild, width: freshness.mild / total * 100, color: FRESHNESS_COLORS.mild },
          { key: 'expiring', label: '临期', value: freshness.expiring, width: freshness.expiring / total * 100, color: FRESHNESS_COLORS.expiring },
          { key: 'spoiled', label: '腐败', value: freshness.spoiled, width: freshness.spoiled / total * 100, color: FRESHNESS_COLORS.spoiled }
        ],
        metrics,
        categoryGradient,
        categoryTotal,
        stockBars,
        netFlowText: (netFlow >= 0 ? '+' : '') + netFlow,
        loading: false
      })
    })
  },
  go(event) {
    const url = event.currentTarget.dataset.url
    if (url.includes('/pages/home') || url.includes('/pages/inventory') || url.includes('/pages/recognition') || url.includes('/pages/alerts') || url.includes('/pages/mine')) {
      wx.switchTab({ url })
    } else {
      wx.navigateTo({ url })
    }
  },
  goDevice() {
    wx.navigateTo({ url: '/pages/devices/index' })
  },
  goEnvironment() {
    wx.navigateTo({ url: '/pages/environment/index' })
  },
  goMessage(event) {
    wx.navigateTo({ url: `/pages/message-detail/index?id=${event.currentTarget.dataset.id}` })
  }
})
