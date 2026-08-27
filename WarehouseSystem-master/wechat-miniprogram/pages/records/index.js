const { recordService, inventoryService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')
const { freshnessText } = require('../../utils/format')

function typeLabel(type) {
  if (type === 'inbound') return '入库'
  if (type === 'outbound') return '出库'
  return '手动'
}

function normalizeRecord(item) {
  const record = item || {}
  const confidence = Number(record.confidence) || 0
  return {
    ...record,
    typeLabel: typeLabel(record.type),
    confidenceText: confidence ? `${confidence}%` : '--',
    quantity: record.quantity || 0,
    name: record.name || '未知果蔬',
    action: record.action || typeLabel(record.type),
    detail: record.detail || record.name || '库存变动',
    operator: record.operator || '系统',
    time: record.time || '--'
  }
}

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    list: [],
    page: 1,
    pageSize: 20,
    total: 0,
    hasMore: true,
    loading: false,
    keyword: '',
    type: '全部',
    types: [
      { label: '全部', value: '全部' },
      { label: '入库', value: 'inbound' },
      { label: '出库', value: 'outbound' },
      { label: '手动', value: 'manual' }
    ],
    detailVisible: false,
    detailRecord: {
      id: '',
      name: '',
      type: '',
      typeLabel: '',
      quantity: 0,
      confidenceText: '--',
      freshnessLabel: '',
      latency: 0,
      time: ''
    }
  },
  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    applyPageTheme(this)
    this.load(true)
  },
  onShow() {
    applyPageTheme(this)
  },
  onPullDownRefresh() {
    this.load(true).finally(() => wx.stopPullDownRefresh())
  },
  onReachBottom() {
    this.load(false)
  },
  load(reset) {
    if (this.data.loading) return Promise.resolve()
    if (!reset && !this.data.hasMore) return Promise.resolve()
    const page = reset ? 1 : this.data.page
    this.setData({ loading: true })
    return recordService.getList({
      keyword: this.data.keyword,
      type: this.data.type,
      page,
      pageSize: this.data.pageSize
    }).then((res) => {
      const payload = res.data || {}
      const chunk = (payload.list || []).map(normalizeRecord)
      const total = Number(payload.total) || 0
      const list = reset ? chunk : this.data.list.concat(chunk)
      this.setData({
        list,
        total,
        page: page + 1,
        hasMore: list.length < total && chunk.length > 0,
        loading: false
      })
    }).catch(() => {
      this.setData({
        list: reset ? [] : this.data.list,
        total: reset ? 0 : this.data.total,
        hasMore: false,
        loading: false
      })
    })
  },
  inputKeyword(event) {
    this.setData({ keyword: event.detail.value })
  },
  clearKeyword() {
    this.setData({ keyword: '' }, () => this.load(true))
  },
  selectType(event) {
    this.setData({ type: event.currentTarget.dataset.value }, () => this.load(true))
  },
  search() {
    this.load(true)
  },
  openDetail(event) {
    const id = event.currentTarget.dataset.id
    const record = this.data.list.find((item) => String(item.id) === String(id))
    if (!record) return
    this.setData({
      detailVisible: true,
      detailRecord: { ...record, freshnessLabel: record.freshnessLabel || '' }
    })
    if (!record.produceId) return
    inventoryService.getDetail(record.produceId).then((res) => {
      this.setData({ 'detailRecord.freshnessLabel': freshnessText(res.data && res.data.freshness) })
    }).catch(() => {
      this.setData({ 'detailRecord.freshnessLabel': '暂无' })
    })
  },
  closeDetail() {
    this.setData({ detailVisible: false })
  },
  back() {
    wx.navigateBack()
  }
})
