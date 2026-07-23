const { inventoryService } = require('../../services/api')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    list: [],
    keyword: '',
    category: '全部',
    freshness: '全部',
    sort: '保质期',
    viewMode: 'card',
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
    pendingItem: null
  },
  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    this.load()
  },
  onShow() {
    if (this.getTabBar) this.getTabBar().syncRoute()
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
      this.setData({ list: res.data })
    })
  },
  inputKeyword(event) {
    this.setData({ keyword: event.detail.value })
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
      : Promise.resolve({ data: { success: true } })
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
    wx.showModal({
      title: '手动入库',
      content: '当前小程序端已预留手动入库入口，正式接入后将写入开发板 API。',
      showCancel: false
    })
  }
})
