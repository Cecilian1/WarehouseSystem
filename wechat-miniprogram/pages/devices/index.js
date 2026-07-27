const { deviceService } = require('../../services/api')
const { applyThemeClass } = require('../../utils/theme')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    devices: [],
    avgUptime: 0,
    onlineCount: 0,
    attentionCount: 0
  },
  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    applyThemeClass(this)
    this.load()
  },
  onShow() {
    applyThemeClass(this)
  },
  load() {
    return deviceService.getList().then((res) => {
      const devices = res.data
      const onlineCount = devices.filter((item) => item.state === 'online').length
      const avgUptime = devices.length
        ? Math.round(devices.reduce((sum, item) => sum + item.uptime, 0) / devices.length)
        : 0
      this.setData({
        devices,
        avgUptime,
        onlineCount,
        attentionCount: devices.length - onlineCount
      })
    })
  },
  back() {
    wx.navigateBack()
  },
  switchDevice(event) {
    getApp().globalData.currentDeviceId = event.currentTarget.dataset.id
    wx.showToast({ title: '已切换设备', icon: 'success' })
  },
  addDevice() {
    wx.showToast({ title: '添加设备入口已预留', icon: 'none' })
  },
  unbindDevice() {
    wx.showModal({
      title: '解除绑定',
      content: '危险操作需要二次确认。演示版不会真正解绑设备。',
      confirmText: '知道了',
      showCancel: false
    })
  }
})
