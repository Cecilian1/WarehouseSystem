const { deviceService } = require('../../services/api')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    devices: []
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
    return deviceService.getList().then((res) => {
      this.setData({ devices: res.data })
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
