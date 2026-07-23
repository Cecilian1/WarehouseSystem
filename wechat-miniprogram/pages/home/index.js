const { dashboardService } = require('../../services/api')

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
      quickActions: []
    },
    loading: true,
    freshnessBars: []
  },
  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    this.load()
  },
  onShow() {
    if (this.getTabBar) this.getTabBar().syncRoute()
  },
  onPullDownRefresh() {
    this.load().finally(() => wx.stopPullDownRefresh())
  },
  load() {
    this.setData({ loading: true })
    return dashboardService.getOverview('fridge-01').then((res) => {
      const freshness = res.data.freshness
      const total = Math.max(1, freshness.fresh + freshness.mild + freshness.expiring + freshness.spoiled)
      this.setData({
        overview: res.data,
        freshnessBars: [
          { key: 'fresh', label: '新鲜', value: freshness.fresh, width: freshness.fresh / total * 100, color: '#5d9b73' },
          { key: 'mild', label: '轻度', value: freshness.mild, width: freshness.mild / total * 100, color: '#dbc56d' },
          { key: 'expiring', label: '临期', value: freshness.expiring, width: freshness.expiring / total * 100, color: '#d99555' },
          { key: 'spoiled', label: '腐败', value: freshness.spoiled, width: freshness.spoiled / total * 100, color: '#cb6259' }
        ],
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
