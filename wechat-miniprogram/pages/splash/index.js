const { applyPageTheme } = require('../../utils/theme')

Page({
  data: {
    entered: false,
    themeClass: 'theme-dark'
  },
  onShow() {
    applyPageTheme(this)
    this.timer = setTimeout(() => {
      const token = wx.getStorageSync('token')
      wx.reLaunch({ url: token ? '/pages/home/index' : '/pages/login/index' })
    }, 1500)
  },
  onHide() {
    clearTimeout(this.timer)
  }
})
