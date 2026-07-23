Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    user: {
      nickName: '芯鲜家庭',
      familyName: '青屿之家'
    },
    sync: {
      state: 'online',
      text: '本地数据已同步',
      time: '刚刚'
    },
    groups: [
      {
        title: '家庭与设备',
        items: [
          { title: '我的设备', desc: '查看开发板、摄像头和传感器状态', icon: 'device', url: '/pages/devices/index' },
          { title: '家庭成员管理', desc: '为子女或老人添加查看权限', icon: 'mine' }
        ]
      },
      {
        title: '提醒设置',
        items: [
          { title: '预警订阅设置', desc: '接收临期、腐败和设备异常消息', icon: 'alert' },
          { title: '果蔬预警提前天数', desc: '默认提前 2 天提醒', icon: 'clock' },
          { title: '消息通知设置', desc: '订阅消息与静默时段', icon: 'record' }
        ]
      },
      {
        title: '更多',
        items: [
          { title: '数据同步状态', desc: '本地 SQLite 与小程序缓存状态', icon: 'check' },
          { title: '意见反馈', desc: '告诉我们你的使用感受', icon: 'edit' },
          { title: '关于芯鲜管家', desc: 'LoongArch 端侧 AI 智能果蔬仓储系统', icon: 'box' }
        ]
      }
    ]
  },
  onLoad() {
    const app = getApp()
    const userInfo = wx.getStorageSync('userInfo')
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight,
      user: userInfo || this.data.user
    })
  },
  onShow() {
    if (this.getTabBar) this.getTabBar().syncRoute()
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
  }
})
