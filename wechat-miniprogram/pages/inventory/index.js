const { inventoryService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')
const { INVENTORY_FORM_FIELDS } = require('../../utils/format')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    list: [],
    keyword: '',
    category: '全部',
    freshness: '全部',
    sort: '保质期',
    viewMode: 'list',
    categories: ['全部', '水果', '蔬菜'],
    freshnessOptions: [
      { label: '全部', value: '全部' },
      { label: '新鲜', value: 'fresh' },
      { label: '轻度', value: 'mild' },
      { label: '临期', value: 'expiring' },
      { label: '腐败', value: 'spoiled' }
    ],
    sortOptions: ['保质期', '新鲜度', '入库时间'],
    sheetVisible: false,
    pendingAction: { title: '', desc: '', danger: false },
    pendingItem: null,
    formVisible: false,
    formFields: INVENTORY_FORM_FIELDS,
    formValues: {},
    stats: { categories: 0, total: 0, fresh: 0, urgent: 0 }
  },
  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    applyPageTheme(this)
    this.load()
  },
  onShow() {
    applyPageTheme(this)
  },
  onPullDownRefresh() {
    this.load().finally(() => wx.stopPullDownRefresh())
  },
  onReachBottom() {
    wx.showToast({ title: '已加载全部库存', icon: 'none' })
  },
  load() {
    return inventoryService.getList({
      keyword: this.data.keyword,
      category: this.data.category,
      freshness: this.data.freshness,
      sort: this.data.sort
    }).then((res) => {
      const list = Array.isArray(res.data) ? res.data : []
      const stats = {
        categories: new Set(list.map((item) => item.category).filter(Boolean)).size,
        total: list.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0),
        fresh: list.filter((item) => item.freshness === 'fresh').length,
        urgent: list.filter((item) => item.freshness === 'expiring' || item.freshness === 'spoiled').length
      }
      this.setData({ list, stats })
    }).catch(() => {
      this.setData({
        list: [],
        stats: { categories: 0, total: 0, fresh: 0, urgent: 0 }
      })
    })
  },
  inputKeyword(event) {
    this.setData({ keyword: event.detail.value })
  },
  clearKeyword() {
    this.setData({ keyword: '' }, () => this.load())
  },
  search() {
    this.load()
  },
  selectCategory(event) {
    this.setData({ category: event.currentTarget.dataset.value }, () => this.load())
  },
  selectFreshness(event) {
    this.setData({ freshness: event.currentTarget.dataset.value }, () => this.load())
  },
  selectSort(event) {
    this.setData({ sort: event.currentTarget.dataset.value }, () => this.load())
  },
  toggleMode() {
    this.setData({ viewMode: this.data.viewMode === 'card' ? 'list' : 'card' })
  },
  goDetail(event) {
    wx.navigateTo({ url: `/pages/detail/index?id=${event.detail.id}` })
  },
  handleAction(event) {
    const { type, item } = event.detail
    const titleMap = { edit: '修改库存信息', outbound: '确认手动出库', delete: '删除库存记录' }
    const descMap = {
      edit: `将进入“${item.name}”的详情页修改信息。`,
      outbound: `确认将“${item.name}”手动出库 1 ${item.unit}？`,
      delete: `删除后将不再在库存列表展示“${item.name}”。`
    }
    if (type === 'edit') {
      wx.navigateTo({ url: `/pages/detail/index?id=${item.id}&edit=1` })
      return
    }
    this.setData({
      sheetVisible: true,
      pendingAction: { type, title: titleMap[type], desc: descMap[type], danger: type === 'delete' },
      pendingItem: item
    })
  },
  cancelSheet() {
    this.setData({ sheetVisible: false })
  },
  confirmSheet() {
    const { pendingAction, pendingItem } = this.data
    if (!pendingAction || !pendingItem) return
    const task = pendingAction.type === 'outbound'
      ? inventoryService.outbound({ id: pendingItem.id, quantity: 1 })
      : inventoryService.remove(pendingItem.id)
    task.then(() => {
      wx.showToast({ title: pendingAction.type === 'delete' ? '已删除' : '已出库', icon: 'success' })
      this.setData({ sheetVisible: false })
      this.load()
    })
  },
  startRecognition() {
    wx.switchTab({ url: '/pages/recognition/index' })
  },
  manualInbound() {
    this.setData({
      formVisible: true,
      formValues: { name: '', category: '水果', quantity: 1, unit: '个', shelfLife: 7, location: '', storageAdvice: '' }
    })
  },
  cancelForm() {
    this.setData({ formVisible: false })
  },
  confirmForm(event) {
    const values = event.detail.values
    inventoryService.inbound(values).then(() => {
      this.setData({ formVisible: false })
      wx.showToast({ title: '库存记录已创建', icon: 'success' })
      return this.load()
    })
  }
})
