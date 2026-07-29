const { inventoryService } = require('../../services/api')
const { freshnessText, freshnessTone, INVENTORY_FORM_FIELDS } = require('../../utils/format')
const { applyThemeClass } = require('../../utils/theme')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    item: null,
    tagText: '',
    tagTone: 'fresh',
    sheetVisible: false,
    formVisible: false,
    formFields: INVENTORY_FORM_FIELDS,
    formValues: {}
  },
  onLoad(query) {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    applyThemeClass(this)
    this.load(query.id, query.edit === '1')
  },
  onShow() {
    applyThemeClass(this)
  },
  load(id, openEdit) {
    inventoryService.getDetail(id).then((res) => {
      this.setData({
        item: res.data,
        tagText: freshnessText(res.data.freshness),
        tagTone: freshnessTone(res.data.freshness)
      })
      if (openEdit) this.edit()
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
      return this.load(this.data.item.id, false)
    })
  },
  edit() {
    const item = this.data.item
    this.setData({
      formVisible: true,
      formValues: {
        name: item.name,
        category: item.category,
        quantity: item.quantity,
        unit: item.unit,
        shelfLife: item.shelfLife,
        location: item.location,
        storageAdvice: item.storageAdvice
      }
    })
  },
  cancelForm() {
    this.setData({ formVisible: false })
  },
  confirmForm(event) {
    inventoryService.update(this.data.item.id, event.detail.values).then(() => {
      this.setData({ formVisible: false })
      wx.showToast({ title: '库存信息已更新', icon: 'success' })
      return this.load(this.data.item.id, false)
    })
  },
  markHandled() {
    wx.showToast({ title: '已标记处理', icon: 'success' })
  }
})
