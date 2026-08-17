const { authService } = require('../../services/api')
const config = require('../../config/index')
const { applyPageTheme } = require('../../utils/theme')

function getWechatLoginCode() {
  return new Promise((resolve, reject) => {
    wx.login({
      success(result) {
        if (result.code) {
          resolve(result.code)
          return
        }
        reject(new Error('微信登录未返回 code'))
      },
      fail: reject
    })
  })
}

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    deviceCode: 'XXGJ-LS2K-0300-01',
    loading: false,
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
  },
  login() {
    this.setData({ loading: true })
    getWechatLoginCode().then((code) => authService.loginByWechat({
      code,
      scene: config.enableDemoLogin ? 'demo' : 'wechat'
    })).then((res) => {
      wx.setStorageSync('token', res.data.token)
      wx.setStorageSync('userInfo', res.data.userInfo)
      return authService.bindDevice({ deviceCode: this.data.deviceCode })
    }).then(() => {
      wx.showToast({ title: '设备已绑定', icon: 'success' })
      setTimeout(() => wx.reLaunch({ url: '/pages/home/index' }), 500)
    }).catch((error) => {
      wx.showToast({
        title: error.message || '登录失败',
        icon: 'none',
        duration: 2600
      })
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
