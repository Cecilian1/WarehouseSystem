const STORAGE_KEY = 'theme'
const DEFAULT_THEME = 'dark'

const FRESHNESS_COLORS = {
  fresh: '#22c55e',
  mild: '#fbbf24',
  expiring: '#f59e0b',
  spoiled: '#ef4444'
}

const CHROME = {
  dark: {
    backgroundColor: '#07111f',
    backgroundColorTop: '#07111f',
    backgroundColorBottom: '#111f33',
    tabBarBackground: '#111f33',
    tabBarColor: '#70829a',
    tabBarSelected: '#4f8cff',
    tabBarBorder: 'black',
    textStyle: 'light'
  },
  light: {
    backgroundColor: '#eef4fa',
    backgroundColorTop: '#eef4fa',
    backgroundColorBottom: '#ffffff',
    tabBarBackground: '#ffffff',
    tabBarColor: '#8b9bb0',
    tabBarSelected: '#4f8cff',
    tabBarBorder: 'white',
    textStyle: 'dark'
  }
}

function getTheme() {
  const app = getApp()
  return (app && app.globalData && app.globalData.theme) || DEFAULT_THEME
}

function applyNativeChrome(theme) {
  const chrome = CHROME[theme] || CHROME.dark
  wx.setBackgroundColor({
    backgroundColor: chrome.backgroundColor,
    backgroundColorTop: chrome.backgroundColorTop,
    backgroundColorBottom: chrome.backgroundColorBottom
  })
  wx.setBackgroundTextStyle({ textStyle: chrome.textStyle })
  wx.setTabBarStyle({
    color: chrome.tabBarColor,
    selectedColor: chrome.tabBarSelected,
    backgroundColor: chrome.tabBarBackground,
    borderStyle: chrome.tabBarBorder,
    fail() {}
  })
}

function syncCurrentTabBar(page) {
  const tabBar = page && typeof page.getTabBar === 'function' ? page.getTabBar() : null
  if (tabBar && typeof tabBar.setData === 'function') {
    if (typeof tabBar.syncTheme === 'function') tabBar.syncTheme()
    if (typeof tabBar.syncRoute === 'function') tabBar.syncRoute()
    return
  }
  const app = getApp()
  const fallback = app && app.globalData && app.globalData.tabBarInstance
  if (fallback && typeof fallback.syncTheme === 'function') fallback.syncTheme()
}

function applyThemeClass(pageInstance) {
  if (!pageInstance || typeof pageInstance.setData !== 'function') return
  pageInstance.setData({ themeClass: 'theme-' + getTheme() })
}

function applyPageTheme(pageInstance) {
  applyThemeClass(pageInstance)
  applyNativeChrome(getTheme())
  syncCurrentTabBar(pageInstance)
}

function setTheme(name) {
  const theme = name === 'light' ? 'light' : 'dark'
  const app = getApp()
  if (app && app.globalData) {
    app.globalData.theme = theme
  }
  wx.setStorageSync(STORAGE_KEY, theme)
  applyNativeChrome(theme)
  const pages = getCurrentPages()
  const current = pages.length ? pages[pages.length - 1] : null
  syncCurrentTabBar(current)
  return theme
}

function toggleTheme() {
  return setTheme(getTheme() === 'dark' ? 'light' : 'dark')
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
  applyPageTheme,
  applyNativeChrome,
  syncTabBarTheme,
  FRESHNESS_COLORS
}
