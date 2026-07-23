const { inventoryService } = require('../../services/api')
const { freshnessText, freshnessTone } = require('../../utils/format')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    item: null,
    tagText: '',
    tagTone: 'fresh',
    sheetVisible: false
  },
  onLoad(query) {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    this.load(query.id)
  },
  load(id) {
    inventoryService.getDetail(id).then((res) => {
      this.setData({
        item: res.data,
        tagText: freshnessText(res.data.freshness),
        tagTone: freshnessTone(res.data.freshness)
      })
    })
  },
  back() {
    wx.navigateBack()
  },
  showOutbound() {
    this.setData({ sheetVisible: true })
  },
  cancelSheet() {
    this.setData({ sheetVisible: false })
  },
  confirmSheet() {
    inventoryService.outbound({ id: this.data.item.id, quantity: 1 }).then(() => {
      wx.showToast({ title: '已手动出库', icon: 'success' })
      this.setData({ sheetVisible: false })
    })
  },
  edit() {
    wx.showToast({ title: '修改信息入口已预留', icon: 'none' })
  },
  markHandled() {
    wx.showToast({ title: '已标记处理', icon: 'success' })
  }
})
