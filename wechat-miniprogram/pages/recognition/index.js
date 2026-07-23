const { recognitionService } = require('../../services/api')
const { freshnessText, freshnessTone } = require('../../utils/format')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    result: null,
    targets: [],
    sheetVisible: false,
    selectedTarget: null
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
  load() {
    return recognitionService.getResult().then((res) => {
      const targets = res.data.targets.map((item) => ({
        ...item,
        freshnessLabel: freshnessText(item.freshness),
        tone: freshnessTone(item.freshness)
      }))
      this.setData({ result: res.data, targets })
    })
  },
  editTarget(event) {
    const id = event.currentTarget.dataset.id
    const selectedTarget = this.data.targets.find((item) => item.id === id)
    this.setData({ selectedTarget, sheetVisible: true })
  },
  addTarget() {
    const next = {
      id: `manual-${Date.now()}`,
      name: '未识别果蔬',
      category: '蔬菜',
      quantity: 1,
      freshness: 'fresh',
      freshnessScore: 88,
      confidence: 0,
      freshnessLabel: '新鲜',
      tone: 'fresh',
      x: 22,
      y: 42,
      w: 22,
      h: 18
    }
    this.setData({ targets: this.data.targets.concat(next) })
  },
  deleteTarget(event) {
    const id = event.currentTarget.dataset.id
    wx.showModal({
      title: '删除识别目标',
      content: '确认删除这条错误目标吗？',
      confirmText: '删除',
      confirmColor: '#cb6259',
      success: (res) => {
        if (res.confirm) {
          this.setData({ targets: this.data.targets.filter((item) => item.id !== id) })
        }
      }
    })
  },
  cancelSheet() {
    this.setData({ sheetVisible: false })
  },
  confirmEdit() {
    const selected = this.data.selectedTarget
    if (!selected) return
    const targets = this.data.targets.map((item) => {
      if (item.id !== selected.id) return item
      const nextFreshness = item.freshness === 'fresh' ? 'mild' : item.freshness === 'mild' ? 'expiring' : 'fresh'
      return {
        ...item,
        freshness: nextFreshness,
        freshnessLabel: freshnessText(nextFreshness),
        tone: freshnessTone(nextFreshness)
      }
    })
    this.setData({ targets, sheetVisible: false })
  },
  confirmRecognition() {
    recognitionService.confirm({ frameId: this.data.result.id, targets: this.data.targets }).then(() => {
      wx.showToast({ title: '库存已更新', icon: 'success' })
    })
  }
})
