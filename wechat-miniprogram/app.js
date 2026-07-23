const { connectRealtime, closeRealtime } = require('./utils/socket')

App({
  globalData: {
    userInfo: null,
    currentDeviceId: 'fridge-01',
    statusBarHeight: 0,
    capsuleTop: 0,
    navHeight: 88,
    realtimeConnected: false
  },

  onLaunch() {
    const system = wx.getSystemInfoSync()
    const capsule = wx.getMenuButtonBoundingClientRect()
    this.globalData.statusBarHeight = system.statusBarHeight || 0
    this.globalData.capsuleTop = capsule.top || this.globalData.statusBarHeight
    this.globalData.navHeight = (capsule.bottom || 80) + 10

    connectRealtime({
      onOpen: () => {
        this.globalData.realtimeConnected = true
      },
      onClose: () => {
        this.globalData.realtimeConnected = false
      },
      onMessage: (event) => {
        this.globalData.lastRealtimeEvent = event
      }
    })
  },

  onHide() {
    closeRealtime()
  }
})
