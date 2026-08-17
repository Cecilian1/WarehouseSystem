const { alertService, inventoryService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    message: null
  },
  onLoad(query) {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    applyPageTheme(this)
    alertService.getMessageDetail(query.id).then((res) => {
      this.setData({ message: res.data })
    })
  },
  onShow() {
    applyPageTheme(this)
  },
  back() {
    wx.navigateBack()
  },
  handle() {
    const message = this.data.message
    alertService.handle({ id: message.id, action: 'confirmed' }).then(() => {
      this.setData({ 'message.status': 'confirmed' })
      wx.showToast({ title: '已处理', icon: 'success' })
    })
  },
  outbound() {
    const message = this.data.message
    if (!message.produceId) {
      wx.showToast({ title: '该消息未关联库存品类', icon: 'none' })
      return
    }
    inventoryService.outbound({ id: message.produceId, quantity: 1 }).then(() => {
      wx.showToast({ title: '已手动出库', icon: 'success' })
    })
  }
})
