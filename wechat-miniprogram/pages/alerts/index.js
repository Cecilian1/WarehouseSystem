const { alertService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')

const STATUS_OPTIONS = [
  { label: '全部', value: 'all' },
  { label: '待处理', value: 'pending' },
  { label: '已确认', value: 'confirmed' },
  { label: '已忽略', value: 'ignored' }
]

const LEVEL_OPTIONS = [
  { label: '全部', value: 'all' },
  { label: '紧急', value: 'critical' },
  { label: '关注', value: 'warning' },
  { label: '普通', value: 'info' }
]

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    alerts: [],
    groups: [],
    filter: 'all',
    statusFilter: 'all',
    statusOptions: STATUS_OPTIONS,
    levelOptions: LEVEL_OPTIONS,
    keyword: '',
    selectedIds: [],
    sheetVisible: false,
    selected: { suggestion: '' },
    stats: []
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
  load() {
    return alertService.getList({
      level: this.data.filter,
      status: this.data.statusFilter,
      keyword: this.data.keyword
    }).then((res) => {
      const selectedIds = this.data.selectedIds
      const alerts = res.data.map((item) => ({ ...item, selected: selectedIds.includes(item.id) }))
      this.setData({
        alerts,
        stats: [
          { label: '待处理', value: alerts.filter((item) => item.status === 'pending').length, tone: 'warning' },
          { label: '严重预警', value: alerts.filter((item) => item.level === 'critical').length, tone: 'critical' },
          { label: '今日已确认', value: alerts.filter((item) => item.status === 'confirmed').length, tone: 'success' },
          { label: '设备异常', value: alerts.filter((item) => item.type === 'device').length, tone: 'info' }
        ],
        groups: [
          { title: '紧急', level: 'critical', list: alerts.filter((item) => item.level === 'critical') },
          { title: '需要关注', level: 'warning', list: alerts.filter((item) => item.level === 'warning') },
          { title: '普通提醒', level: 'info', list: alerts.filter((item) => item.level === 'info') }
        ]
      })
    })
  },
  setFilter(event) {
    this.setData({ filter: event.currentTarget.dataset.value }, () => this.load())
  },
  selectStatus(event) {
    this.setData({ statusFilter: event.currentTarget.dataset.value }, () => this.load())
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
  toggleSelect(event) {
    const id = event.currentTarget.dataset.id
    const selectedIds = this.data.selectedIds.includes(id)
      ? this.data.selectedIds.filter((item) => item !== id)
      : this.data.selectedIds.concat(id)
    this.setData({
      selectedIds,
      alerts: this.data.alerts.map((item) => ({ ...item, selected: selectedIds.includes(item.id) })),
      groups: this.data.groups.map((group) => ({
        ...group,
        list: group.list.map((item) => ({ ...item, selected: selectedIds.includes(item.id) }))
      }))
    })
  },
  batchHandle() {
    const ids = this.data.selectedIds
    if (!ids.length) return
    Promise.all(ids.map((id) => alertService.handle({ id, action: 'confirmed' }))).then(() => {
      wx.showToast({ title: `已处理 ${ids.length} 条预警`, icon: 'success' })
      this.setData({ selectedIds: [] })
      this.load()
    })
  },
  ignoreAlert(event) {
    const id = event.currentTarget.dataset.id
    alertService.handle({ id, action: 'ignored' }).then(() => {
      wx.showToast({ title: '已忽略', icon: 'none' })
      this.load()
    })
  },
  openHandle(event) {
    const id = event.currentTarget.dataset.id
    const selected = this.data.alerts.find((item) => item.id === id)
    this.setData({ selected, sheetVisible: true })
  },
  goDetail(event) {
    wx.navigateTo({ url: `/pages/message-detail/index?id=${event.currentTarget.dataset.id}` })
  },
  cancelSheet() {
    this.setData({ sheetVisible: false })
  },
  confirmSheet() {
    alertService.handle({ id: this.data.selected.id, action: 'confirmed' }).then(() => {
      wx.showToast({ title: '已标记处理', icon: 'success' })
      this.setData({ sheetVisible: false })
      this.load()
    })
  }
})
