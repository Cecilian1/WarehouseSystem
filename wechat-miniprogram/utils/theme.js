const STORAGE_KEY = 'theme'
const DEFAULT_THEME = 'dark'

const FRESHNESS_COLORS = {
  fresh: '#22c55e',
  mild: '#fbbf24',
  expiring: '#f59e0b',
  spoiled: '#ef4444'
}

function getTheme() {
  const app = getApp()
  return (app && app.globalData && app.globalData.theme) || DEFAULT_THEME
}

function setTheme(name) {
  const theme = name === 'light' ? 'light' : 'dark'
  const app = getApp()
  if (app && app.globalData) {
    app.globalData.theme = theme
  }
  wx.setStorageSync(STORAGE_KEY, theme)
  syncTabBarTheme(theme)
  return theme
}

function toggleTheme() {
  return setTheme(getTheme() === 'dark' ? 'light' : 'dark')
}

function applyThemeClass(pageInstance) {
  if (!pageInstance || typeof pageInstance.setData !== 'function') return
  pageInstance.setData({ themeClass: 'theme-' + getTheme() })
}

function syncTabBarTheme(theme) {
  const app = getApp()
  const tabBar = app && app.globalData && app.globalData.tabBarInstance
  if (tabBar && typeof tabBar.setData === 'function') {
    tabBar.setData({ themeClass: 'theme-' + theme })
  }
}

module.exports = {
  getTheme,
  setTheme,
  toggleTheme,
  applyThemeClass,
  syncTabBarTheme,
  FRESHNESS_COLORS
}
