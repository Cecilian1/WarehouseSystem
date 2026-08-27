const { reportService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')

const RISK_META = {
  normal: { label: '状态良好', tone: 'normal' },
  attention: { label: '需要关注', tone: 'attention' },
  high: { label: '优先处理', tone: 'high' }
}

function displayTime(value) {
  if (!value) return '刚刚'
  return String(value).replace('T', ' ').slice(0, 16)
}

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    loading: true,
    refreshing: false,
    error: '',
    hasReport: false,
    report: {},
    risk: RISK_META.normal,
    generatedTime: ''
  },

  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    applyPageTheme(this)
    this.load(false)
  },

  onShow() {
    applyPageTheme(this)
  },

  onPullDownRefresh() {
    this.load(true).finally(() => wx.stopPullDownRefresh())
  },

  load(refresh) {
    this.setData({
      loading: !this.data.hasReport,
      refreshing: Boolean(refresh),
      error: ''
    })
    return reportService.getDaily(Boolean(refresh)).then((res) => {
      const report = res.data || {}
      const riskyItems = report.freshness && Array.isArray(report.freshness.riskyItems)
        ? report.freshness.riskyItems.map((item) => ({
          ...item,
          initial: String(item.name || '果').slice(0, 1)
        }))
        : []
      report.freshness = { ...(report.freshness || {}), riskyItems }
      this.setData({
        report,
        risk: RISK_META[report.riskLevel] || RISK_META.attention,
        generatedTime: displayTime(report.generatedAt),
        hasReport: true,
        loading: false,
        refreshing: false
      })
    }).catch((error) => {
      this.setData({
        error: error.message || '报告生成失败，请稍后重试',
        loading: false,
        refreshing: false
      })
    })
  },

  refresh() {
    if (!this.data.refreshing) this.load(true)
  },

  retry() {
    this.load(false)
  },

  back() {
    wx.navigateBack({
      fail() {
        wx.switchTab({ url: '/pages/home/index' })
      }
    })
  },

  goInventory() {
    wx.switchTab({ url: '/pages/inventory/index' })
  },

  goEnvironment() {
    wx.navigateTo({ url: '/pages/environment/index' })
  },

  goAlerts() {
    wx.switchTab({ url: '/pages/alerts/index' })
  }
})
