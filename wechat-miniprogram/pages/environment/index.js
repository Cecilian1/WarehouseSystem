const { environmentService } = require('../../services/api')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
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
    this.load()
  },
  load() {
    return Promise.all([
      environmentService.getCurrent('fridge-01'),
      environmentService.getHistory(this.data.range)
    ]).then(([current, history]) => {
      const list = history.data.map((item) => ({
        ...item,
        tempHeight: Math.max(28, item.tempMax * 22),
        humidityHeight: Math.max(28, item.humidityMax * 1.2)
      }))
      this.setData({ current: current.data, history: list })
    })
  },
  selectRange(event) {
    this.setData({ range: event.currentTarget.dataset.value }, () => this.load())
  },
  back() {
    wx.navigateBack()
  }
})
