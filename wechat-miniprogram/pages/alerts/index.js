const { alertService } = require('../../services/api')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    alerts: [],
    groups: [],
    filter: 'all',
    sheetVisible: false,
    selected: { suggestion: '' },
    stats: []
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
    return alertService.getList({ level: this.data.filter }).then((res) => {
      const alerts = res.data
      this.setData({
        alerts,
        stats: [
          { label: '临期提醒', value: alerts.filter((item) => item.type === 'expiring').length, tone: 'warning' },
          { label: '腐败提醒', value: alerts.filter((item) => item.type === 'spoiled').length, tone: 'critical' },
          { label: '设备异常', value: alerts.filter((item) => ['device', 'temperature', 'storage'].includes(item.type)).length, tone: 'info' },
          { label: '未读消息', value: alerts.filter((item) => item.status === 'pending').length, tone: 'warning' }
        ],
        groups: [
          { title: '紧急', level: 'critical', list: alerts.filter((item) => item.level === 'critical') },
          { title: '需要关注', level: 'warning', list: alerts.filter((item) => item.level === 'warning') },
          { title: '普通提醒', level: 'info', list: alerts.filter((item) => item.level === 'info') }
        ]
      })
    })
  },
  setFilter(event) {
    this.setData({ filter: event.currentTarget.dataset.value }, () => this.load())
  },
  openHandle(event) {
    const id = event.currentTarget.dataset.id
    const selected = this.data.alerts.find((item) => item.id === id)
    this.setData({ selected, sheetVisible: true })
  },
  goDetail(event) {
    wx.navigateTo({ url: `/pages/message-detail/index?id=${event.currentTarget.dataset.id}` })
  },
  cancelSheet() {
    this.setData({ sheetVisible: false })
  },
  confirmSheet() {
    alertService.handle({ id: this.data.selected.id, action: 'confirmed' }).then(() => {
      wx.showToast({ title: '已标记处理', icon: 'success' })
      this.setData({ sheetVisible: false })
      this.load()
    })
  }
})
