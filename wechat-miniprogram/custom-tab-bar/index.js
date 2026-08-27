const { getTheme } = require('../utils/theme')

Component({
  data: {
    selected: 0,
    themeClass: 'theme-dark',
    list: [
      { pagePath: '/pages/home/index', text: '首页', icon: 'home' },
      { pagePath: '/pages/inventory/index', text: '库存', icon: 'box' },
      { pagePath: '/pages/recognition/index', text: 'AI识别', icon: 'scan', center: true },
      { pagePath: '/pages/alerts/index', text: '预警', icon: 'alert' },
      { pagePath: '/pages/mine/index', text: '我的', icon: 'mine' }
    ]
  },
  lifetimes: {
    attached() {
      const app = getApp()
      if (app && app.globalData) app.globalData.tabBarInstance = this
      this.syncTheme()
      this.syncRoute()
    },
    detached() {
      const app = getApp()
      if (app && app.globalData && app.globalData.tabBarInstance === this) {
        app.globalData.tabBarInstance = null
      }
    }
  },
  pageLifetimes: {
    show() {
      this.syncTheme()
      this.syncRoute()
    }
  },
  methods: {
    syncTheme() {
      this.setData({ themeClass: 'theme-' + getTheme() })
    },
    syncRoute() {
      const pages = getCurrentPages()
      const route = pages.length ? `/${pages[pages.length - 1].route}` : ''
      const selected = this.data.list.findIndex((item) => item.pagePath === route)
      if (selected >= 0) this.setData({ selected })
    },
    switchTab(event) {
      const index = event.currentTarget.dataset.index
      const item = this.data.list[index]
      wx.switchTab({ url: item.pagePath })
    }
  }
})
