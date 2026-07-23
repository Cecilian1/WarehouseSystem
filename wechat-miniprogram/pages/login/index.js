const { authService } = require('../../services/api')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    deviceCode: 'XXGJ-LS2K-0300-01',
    loading: false
  },
  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
  },
  login() {
    this.setData({ loading: true })
    authService.loginByWechat({ scene: 'demo' }).then((res) => {
      wx.setStorageSync('token', res.data.token)
      wx.setStorageSync('userInfo', res.data.userInfo)
      return authService.bindDevice({ deviceCode: this.data.deviceCode })
    }).then(() => {
      wx.showToast({ title: '设备已绑定', icon: 'success' })
      setTimeout(() => wx.reLaunch({ url: '/pages/home/index' }), 500)
    }).finally(() => {
      this.setData({ loading: false })
    })
  },
  inputCode(event) {
    this.setData({ deviceCode: event.detail.value })
  },
  scanCode() {
    wx.showToast({ title: '比赛演示环境可手动输入设备编号', icon: 'none' })
  },
  showHelp() {
    wx.showModal({
      title: '绑定说明',
      content: '请确保开发板与手机在同一网络，后续接入 FastAPI 后可通过设备编号绑定真实冰箱。',
      showCancel: false
    })
  }
})
