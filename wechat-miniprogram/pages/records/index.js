const { recordService, inventoryService } = require('../../services/api')
const { applyThemeClass } = require('../../utils/theme')
const { freshnessText } = require('../../utils/format')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    list: [],
    keyword: '',
    type: '全部',
    types: [
      { label: '全部', value: '全部' },
      { label: '入库', value: 'inbound' },
      { label: '出库', value: 'outbound' },
      { label: '手动修改', value: 'manual' }
    ],
    detailVisible: false,
    detailRecord: { id: '', name: '', type: '', quantity: 0, confidence: 0, freshnessLabel: '', latency: 0, time: '' }
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
  onReachBottom() {
    wx.showToast({ title: '已加载全部记录', icon: 'none' })
  },
  load() {
    return recordService.getList({ keyword: this.data.keyword, type: this.data.type }).then((res) => {
      this.setData({ list: res.data })
    })
  },
  inputKeyword(event) {
    this.setData({ keyword: event.detail.value })
  },
  selectType(event) {
    this.setData({ type: event.currentTarget.dataset.value }, () => this.load())
  },
  search() {
    this.load()
  },
  openDetail(event) {
    const id = event.currentTarget.dataset.id
    const record = this.data.list.find((item) => item.id === id)
    if (!record) return
    this.setData({ detailVisible: true, detailRecord: record })
    inventoryService.getDetail(record.produceId).then((res) => {
      this.setData({ 'detailRecord.freshnessLabel': freshnessText(res.data.freshness) })
    })
  },
  closeDetail() {
    this.setData({ detailVisible: false })
  },
  back() {
    wx.navigateBack()
  }
})
