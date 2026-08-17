const { deviceService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    devices: [],
    board: { name: '开发板', model: 'LoongArch', lastSync: '暂无', state: 'offline' },
    avgUptime: 0,
    onlineCount: 0,
    attentionCount: 0
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
  load() {
    return deviceService.getList().then((res) => {
      const devices = (res.data || []).map((item, index) => ({
        id: item.id || `device-${index}`,
        name: item.name || '未命名设备',
        type: item.type || item.category || '设备',
        model: item.model || item.code || '--',
        state: item.state || 'offline',
        uptime: Math.round(Number(item.uptime || 0)),
        value: item.value || item.cameraStatus || item.sensorStatus || '未上报',
        lastSync: item.lastSync || item.lastHeartbeat || '暂无',
        canSwitch: index === 0 || item.type === '边缘计算节点'
      }))
      const onlineCount = devices.filter((item) => item.state === 'online').length
      const avgUptime = devices.length
        ? Math.round(devices.reduce((sum, item) => sum + Number(item.uptime || 0), 0) / devices.length)
        : 0
      this.setData({
        devices,
        board: devices[0] || this.data.board,
        avgUptime,
        onlineCount,
        attentionCount: devices.length - onlineCount
      })
    })
  },
  back() {
    wx.navigateBack()
  },
  switchDevice(event) {
    getApp().globalData.currentDeviceId = event.currentTarget.dataset.id
    wx.showToast({ title: '已切换设备', icon: 'success' })
  },
  addDevice() {
    wx.showToast({ title: '添加设备入口已预留', icon: 'none' })
  },
  unbindDevice() {
    wx.showModal({
      title: '解除绑定',
      content: '危险操作需要二次确认。演示版不会真正解绑设备。',
      confirmText: '知道了',
      showCancel: false
    })
  }
})
