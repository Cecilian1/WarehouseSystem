const ACTIONS = {
  voice: '/pages/ai-chat/index?type=voice',
  report: '/pages/daily-report/index',
  freshness: '/pages/ai-chat/index?type=freshness',
  environment: '/pages/ai-chat/index?type=environment',
  alerts: '/pages/ai-chat/index?type=alerts'
}

const POSITION_KEY = 'ai-assistant-position'

function windowMetrics() {
  const info = typeof wx.getWindowInfo === 'function'
    ? wx.getWindowInfo()
    : wx.getSystemInfoSync()
  const safeArea = info.safeArea || {}
  return {
    width: info.windowWidth,
    height: info.windowHeight,
    statusTop: info.statusBarHeight || 0,
    safeBottom: Math.max(0, info.windowHeight - (safeArea.bottom || info.windowHeight))
  }
}

Component({
  data: {
    open: false,
    dockStyle: '',
    dockClass: 'dock-right dock-bottom',
    fabX: 0,
    fabY: 0,
    actions: [
      { key: 'voice', title: '语音对话', desc: '按住麦克风，与芯鲜助手交流', icon: 'voice' },
      { key: 'report', title: 'AI 每日报告', desc: '汇总今日全部仓储信息', icon: 'report' },
      { key: 'freshness', title: '新鲜度分析', desc: 'AI分析当前新鲜度与处理顺序', icon: 'freshness' },
      { key: 'environment', title: '温湿度诊断', desc: 'AI诊断当前环境与异常原因', icon: 'environment' },
      { key: 'alerts', title: '风险预警', desc: 'AI按紧急程度总结待办事项', icon: 'alerts' }
    ]
  },

  lifetimes: {
    attached() {
      this.initPosition()
    }
  },

  methods: {
    initPosition() {
      const metrics = windowMetrics()
      const fabSize = metrics.width * 80 / 750
      const edge = Math.max(8, metrics.width * 20 / 750)
      const tabOffset = metrics.width * 176 / 750 + metrics.safeBottom
      const saved = wx.getStorageSync(POSITION_KEY) || {}
      const maxX = metrics.width - fabSize - edge
      const maxY = metrics.height - fabSize - metrics.safeBottom - edge
      const defaultX = metrics.width - fabSize - metrics.width * 26 / 750
      const defaultY = metrics.height - fabSize - tabOffset
      const x = Math.max(edge, Math.min(maxX, Number.isFinite(saved.x) ? saved.x : defaultX))
      const y = Math.max(metrics.statusTop + edge, Math.min(maxY, Number.isFinite(saved.y) ? saved.y : defaultY))

      this._dragBounds = { ...metrics, fabSize, edge, maxX, maxY }
      this.updatePosition(x, y)
    },

    updatePosition(x, y) {
      const bounds = this._dragBounds
      if (!bounds) return
      const horizontal = x + bounds.fabSize / 2 < bounds.width / 2 ? 'dock-left' : 'dock-right'
      const vertical = y + bounds.fabSize / 2 < bounds.height / 2 ? 'dock-top' : 'dock-bottom'
      this.setData({
        fabX: x,
        fabY: y,
        dockStyle: `left:${Math.round(x)}px;top:${Math.round(y)}px;right:auto;bottom:auto;`,
        dockClass: `${horizontal} ${vertical}`
      })
    },

    toggle() {
      if (this._suppressTap) return
      this.setData({ open: !this.data.open })
    },

    close() {
      if (this.data.open) this.setData({ open: false })
    },

    dragStart(event) {
      if (this.data.open || !event.touches.length) return
      const touch = event.touches[0]
      this._dragStart = {
        touchX: touch.clientX,
        touchY: touch.clientY,
        x: this.data.fabX,
        y: this.data.fabY
      }
      this._didDrag = false
    },

    dragMove(event) {
      if (this.data.open || !this._dragStart || !event.touches.length) return
      const touch = event.touches[0]
      const deltaX = touch.clientX - this._dragStart.touchX
      const deltaY = touch.clientY - this._dragStart.touchY
      if (Math.abs(deltaX) + Math.abs(deltaY) > 5) this._didDrag = true
      if (!this._didDrag) return

      const bounds = this._dragBounds
      const x = Math.max(bounds.edge, Math.min(bounds.maxX, this._dragStart.x + deltaX))
      const y = Math.max(bounds.statusTop + bounds.edge, Math.min(bounds.maxY, this._dragStart.y + deltaY))
      this.updatePosition(x, y)
    },

    dragEnd() {
      if (!this._dragStart) return
      this._dragStart = null
      if (!this._didDrag) return

      wx.setStorageSync(POSITION_KEY, { x: this.data.fabX, y: this.data.fabY })
      this._suppressTap = true
      this._didDrag = false
      setTimeout(() => {
        this._suppressTap = false
      }, 180)
    },

    select(event) {
      const key = event.currentTarget.dataset.key
      const url = ACTIONS[key]
      if (!url) return
      this.setData({ open: false })

      wx.navigateTo({ url })
    }
  }
})
