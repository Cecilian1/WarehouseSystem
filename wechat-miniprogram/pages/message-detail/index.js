const { alertService } = require('../../services/api')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    message: null
  },
  onLoad(query) {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    alertService.getMessageDetail(query.id).then((res) => {
      this.setData({ message: res.data })
    })
  },
  back() {
    wx.navigateBack()
  },
  handle() {
    wx.showToast({ title: '已处理', icon: 'success' })
  },
  outbound() {
    wx.showToast({ title: '出库入口已预留', icon: 'none' })
  }
})
