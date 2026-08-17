const { recognitionService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')
const { freshnessText, freshnessTone } = require('../../utils/format')
const config = require('../../config/index')

function imageUrl(path) {
  if (/^https?:\/\//.test(path || '')) {
    const separator = path.includes('?') ? '&' : '?'
    return `${path}${separator}t=${Date.now()}`
  }
  const apiOrigin = config.baseUrl.replace(/\/api\/?$/, '')
  const normalizedPath = path && path.startsWith('/') ? path : `/${path || 'api/frames/latest/image'}`
  const separator = normalizedPath.includes('?') ? '&' : '?'
  return `${apiOrigin}${normalizedPath}${separator}t=${Date.now()}`
}

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    result: null,
    targets: [],
    sheetVisible: false,
    selectedTarget: null,
    avgConfidence: 0,
    latencyBars: [],
    imageLoading: false,
    imageError: false,
    usingLatestFrame: false,
    themeClass: 'theme-dark'
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
    return recognitionService.getResult().then((res) => {
      const hasInference = res.data.hasInference === true
      const targets = (hasInference ? (res.data.targets || []) : []).map((item) => ({
        ...item,
        freshnessLabel: freshnessText(item.freshness),
        tone: freshnessTone(item.freshness)
      }))

      const confidences = targets.map((item) => item.confidence)
      const avgConfidence = confidences.length
        ? Math.round(confidences.reduce((sum, value) => sum + value, 0) / confidences.length)
        : 0

      const latencyTrend = res.data.latencyTrend || []
      const maxLatency = Math.max(1, ...latencyTrend)
      const latencyBars = latencyTrend.map((value) => ({
        value,
        height: Math.max(10, Math.round((value / maxLatency) * 80))
      }))

      const result = {
        ...res.data,
        hasInference,
        imageUrl: imageUrl(res.data.image || '/api/frames/latest/image')
      }

      this.setData({
        result,
        targets,
        avgConfidence,
        latencyBars,
        imageLoading: true,
        imageError: false,
        usingLatestFrame: !hasInference
      })
    })
  },
  handleImageLoad() {
    this.setData({ imageLoading: false, imageError: false })
  },
  handleImageError() {
    if (!this.data.result) return
    if (!this.data.usingLatestFrame) {
      this.setData({
        'result.imageUrl': imageUrl('/api/frames/latest/image'),
        imageLoading: true,
        imageError: false,
        usingLatestFrame: true
      })
      return
    }
    this.setData({ imageLoading: false, imageError: true })
  },
  refreshFrame() {
    if (!this.data.result) return
    this.setData({
      'result.imageUrl': imageUrl('/api/frames/latest/image'),
      imageLoading: true,
      imageError: false,
      usingLatestFrame: true
    })
  },
  editTarget(event) {
    if (!this.data.result || !this.data.result.hasInference) return
    const id = event.currentTarget.dataset.id
    const selectedTarget = this.data.targets.find((item) => item.id === id)
    this.setData({ selectedTarget, sheetVisible: true })
  },
  addTarget() {
    if (!this.data.result || !this.data.result.hasInference) return
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
      confirmColor: '#ef4444',
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
    if (!this.data.result || !this.data.result.hasInference) {
      wx.showToast({ title: '尚无识别结果', icon: 'none' })
      return
    }
    recognitionService.confirm({ frameId: this.data.result.id, targets: this.data.targets }).then(() => {
      wx.showToast({ title: '库存已更新', icon: 'success' })
    })
  }
})
