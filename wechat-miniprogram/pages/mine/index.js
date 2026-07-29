const { applyThemeClass, getTheme, toggleTheme } = require('../../utils/theme')
const config = require('../../config/index')

const DEFAULT_NOTIFY_SWITCHES = { alert: true, device: true, sound: false }
const DEFAULT_THRESHOLDS = { expireDays: 2, tempHigh: 8, humidityHigh: 95, abnormalDuration: 10 }

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    isDark: true,
    user: {
      nickName: '芯鲜家庭',
      familyName: '青屿之家'
    },
    sync: {
      state: 'online',
      text: '本地数据已同步',
      time: '刚刚'
    },
    groupsBefore: [
      {
        title: '家庭与设备',
        items: [
          { title: '我的设备', desc: '查看开发板、摄像头和传感器状态', icon: 'device', url: '/pages/devices/index' },
          { title: '家庭成员管理', desc: '为子女或老人添加查看权限', icon: 'mine' }
        ]
      }
    ],
    groupsAfter: [
      {
        title: '更多',
        items: [
          { title: '数据同步状态', desc: '本地 SQLite 与小程序缓存状态', icon: 'check' },
          { title: '意见反馈', desc: '告诉我们你的使用感受', icon: 'edit' },
          { title: '关于芯鲜管家', desc: 'LoongArch 端侧 AI 智能果蔬仓储系统', icon: 'box' }
        ]
      }
    ],
    accounts: [
      { name: '系统管理员', account: 'admin', role: '超级管理员', state: '启用', lastLogin: '刚刚' },
      { name: '演示账号', account: 'demo', role: '运维人员', state: '启用', lastLogin: '2 小时前' },
      { name: '设备维护员', account: 'operator', role: '只读观察员', state: '禁用', lastLogin: '3 天前' }
    ],
    roles: [
      { name: '超级管理员', desc: '拥有全部功能与数据权限', count: 1 },
      { name: '运维人员', desc: '可查看并处理预警、设备与库存', count: 1 },
      { name: '只读观察员', desc: '仅可查看数据，不可修改', count: 1 }
    ],
    accountsVisible: false,
    rolesVisible: false,
    notifySwitches: DEFAULT_NOTIFY_SWITCHES,
    thresholds: DEFAULT_THRESHOLDS,
    connection: {
      apiUrl: config.baseUrl,
      wsUrl: config.wsUrl,
      token: '••••••••',
      syncInterval: 15
    },
    serviceStatus: {
      sqlite: { label: 'SQLite · 检测中', tone: 'info' },
      api: { label: 'FastAPI · 检测中', tone: 'info' },
      ws: { label: 'WebSocket · 检测中', tone: 'info' }
    }
  },
  onLoad() {
    const app = getApp()
    const userInfo = wx.getStorageSync('userInfo')
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight,
      user: userInfo || this.data.user,
      notifySwitches: wx.getStorageSync('notifySwitches') || DEFAULT_NOTIFY_SWITCHES,
      thresholds: wx.getStorageSync('thresholds') || DEFAULT_THRESHOLDS
    })
    this.syncTheme()
  },
  onShow() {
    this.syncTheme()
    if (this.getTabBar) this.getTabBar().syncRoute()
    this.refreshServiceStatus()
    this._statusTimer = setInterval(() => this.refreshServiceStatus(), 8000)
  },
  onHide() {
    if (this._statusTimer) clearInterval(this._statusTimer)
  },
  onUnload() {
    if (this._statusTimer) clearInterval(this._statusTimer)
  },
  refreshServiceStatus() {
    this.refreshRealtimeStatus()
    wx.request({
      url: `${config.baseUrl}/health`,
      method: 'GET',
      timeout: config.timeout,
      success: (res) => {
        const ok = res.statusCode >= 200 && res.statusCode < 300 && res.data && res.data.code === 0
        const dbExists = ok && res.data.data && res.data.data.dbExists
        this.setData({
          'serviceStatus.sqlite': dbExists
            ? { label: 'SQLite 正常', tone: 'success' }
            : { label: 'SQLite 异常', tone: 'offline' },
          'serviceStatus.api': config.enableMock
            ? { label: 'FastAPI · Mock 模式', tone: 'info' }
            : ok
              ? { label: 'FastAPI · 已连接', tone: 'success' }
              : { label: 'FastAPI · 响应异常', tone: 'offline' }
        })
      },
      fail: () => {
        this.setData({
          'serviceStatus.sqlite': { label: 'SQLite 未知', tone: 'offline' },
          'serviceStatus.api': config.enableMock
            ? { label: 'FastAPI · Mock 模式', tone: 'info' }
            : { label: 'FastAPI · 未连接', tone: 'offline' }
        })
      }
    })
  },
  refreshRealtimeStatus() {
    const connected = getApp().globalData.realtimeConnected
    this.setData({
      'serviceStatus.ws': connected
        ? { label: 'WebSocket · 已连接', tone: 'success' }
        : { label: 'WebSocket · 未连接', tone: 'offline' }
    })
  },
  syncTheme() {
    applyThemeClass(this)
    this.setData({ isDark: getTheme() === 'dark' })
  },
  onThemeToggle() {
    toggleTheme()
    this.syncTheme()
  },
  navigate(event) {
    const url = event.currentTarget.dataset.url
    if (url) {
      wx.navigateTo({ url })
      return
    }
    wx.showToast({ title: '该设置入口已预留', icon: 'none' })
  },
  goRecords() {
    wx.navigateTo({ url: '/pages/records/index' })
  },
  goEnvironment() {
    wx.navigateTo({ url: '/pages/environment/index' })
  },
  openAccounts() {
    this.setData({ accountsVisible: true })
  },
  closeAccounts() {
    this.setData({ accountsVisible: false })
  },
  addAccount() {
    wx.showToast({ title: '该设置入口已预留', icon: 'none' })
  },
  openRoles() {
    this.setData({ rolesVisible: true })
  },
  closeRoles() {
    this.setData({ rolesVisible: false })
  },
  configureRole() {
    wx.showToast({ title: '该设置入口已预留', icon: 'none' })
  },
  onNotifyChange(event) {
    const key = event.currentTarget.dataset.key
    const notifySwitches = { ...this.data.notifySwitches, [key]: event.detail.value }
    this.setData({ notifySwitches })
    wx.setStorageSync('notifySwitches', notifySwitches)
  },
  onThresholdChange(event) {
    const key = event.currentTarget.dataset.key
    this.setData({ [`thresholds.${key}`]: event.detail.value })
  },
  saveThresholds() {
    wx.setStorageSync('thresholds', this.data.thresholds)
    wx.showToast({ title: '预警阈值已保存', icon: 'success' })
  },
  decreaseSyncInterval() {
    const next = Math.max(5, this.data.connection.syncInterval - 5)
    this.setData({ 'connection.syncInterval': next })
  },
  increaseSyncInterval() {
    const next = Math.min(60, this.data.connection.syncInterval + 5)
    this.setData({ 'connection.syncInterval': next })
  },
  saveConnection() {
    wx.showToast({ title: '连接设置已保存', icon: 'success' })
  }
})
