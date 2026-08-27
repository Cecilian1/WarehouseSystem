const { assistantService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')

const PRESETS = {
  freshness: {
    title: '新鲜度分析',
    subtitle: '结合当前库存与识别结果',
    question: '当前果蔬的新鲜度怎么样？哪些需要优先处理？',
    placeholder: '继续询问库存或新鲜度…',
    icon: 'leaf'
  },
  environment: {
    title: '温湿度诊断',
    subtitle: '结合当前与今日环境数据',
    question: '当前温湿度是否适宜？需要注意什么？',
    placeholder: '继续询问温湿度情况…',
    icon: 'temp'
  },
  alerts: {
    title: '风险预警',
    subtitle: '按紧急程度快速安排事项',
    question: '请根据当前紧急程度，分点总结现在需要做什么。',
    placeholder: '继续询问风险或处理顺序…',
    icon: 'alert'
  }
}

const URGENCY = {
  normal: { label: '状态正常', tone: 'normal' },
  attention: { label: '需要关注', tone: 'attention' },
  high: { label: '优先处理', tone: 'high' }
}

function displayTime(value) {
  if (!value) return '刚刚'
  return String(value).replace('T', ' ').slice(11, 16)
}

let messageSequence = 0

function nextMessageId() {
  messageSequence += 1
  return `${Date.now()}-${messageSequence}`
}

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    themeClass: 'theme-dark',
    type: 'freshness',
    preset: PRESETS.freshness,
    input: '',
    messages: [],
    sending: false,
    scrollTarget: ''
  },

  onLoad(options) {
    const app = getApp()
    const type = PRESETS[options.type] ? options.type : 'freshness'
    const preset = PRESETS[type]
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight,
      type,
      preset
    })
    applyPageTheme(this)
    this.sendQuestion(preset.question)
  },

  onShow() {
    applyPageTheme(this)
  },

  onPullDownRefresh() {
    wx.stopPullDownRefresh()
  },

  inputQuestion(event) {
    this.setData({ input: event.detail.value })
  },

  ask() {
    const question = String(this.data.input || '').trim()
    if (!question || this.data.sending) return
    this.setData({ input: '' })
    this.sendQuestion(question)
  },

  retry(event) {
    if (this.data.sending) return
    this.sendQuestion(event.currentTarget.dataset.question, {
      appendUser: false,
      removeMessageId: event.currentTarget.dataset.id
    })
  },

  historyFrom(messages, currentQuestion) {
    const history = messages.filter((message) => (
      !message.loading && !message.error && message.content
    )).map((message) => ({
      role: message.role,
      content: message.content
    })).slice(-12)
    const last = history[history.length - 1]
    if (last && last.role === 'user' && last.content === currentQuestion) history.pop()
    return history
  },

  scrollTo(messageId) {
    this.setData({ scrollTarget: `message-${messageId}` })
  },

  sendQuestion(question, options = {}) {
    const normalizedQuestion = String(question || '').trim()
    if (!normalizedQuestion) return Promise.resolve()

    let messages = this.data.messages.slice()
    if (options.removeMessageId) {
      messages = messages.filter((message) => message.id !== options.removeMessageId)
    }
    const history = this.historyFrom(messages, normalizedQuestion)
    if (options.appendUser !== false) {
      messages.push({
        id: nextMessageId(),
        role: 'user',
        content: normalizedQuestion
      })
    }
    const waitingId = nextMessageId()
    messages.push({
      id: waitingId,
      role: 'assistant',
      content: '',
      loading: true
    })
    this.setData({ messages, sending: true }, () => this.scrollTo(waitingId))

    return assistantService.analyze({
      type: this.data.type,
      question: normalizedQuestion,
      history
    }).then((res) => {
      const answer = res.data || {}
      const urgency = URGENCY[answer.urgency] || URGENCY.attention
      const updated = this.data.messages.map((message) => (
        message.id === waitingId
          ? {
            id: waitingId,
            role: 'assistant',
            content: answer.summary || '',
            bullets: answer.bullets || [],
            format: answer.format || ((answer.bullets || []).length ? 'list' : 'paragraph'),
            urgency,
            sourceLabel: answer.sourceLabel || '本地数据分析',
            fallbackReason: answer.fallbackReason || '',
            generatedTime: displayTime(answer.generatedAt),
            grounded: answer.grounded === true
          }
          : message
      ))
      this.setData({
        messages: updated,
        sending: false
      }, () => this.scrollTo(waitingId))
    }).catch((error) => {
      const updated = this.data.messages.map((message) => (
        message.id === waitingId
          ? {
            id: waitingId,
            role: 'assistant',
            content: '',
            error: error.message || 'AI 暂时无法回答，请稍后再试',
            question: normalizedQuestion
          }
          : message
      ))
      this.setData({
        messages: updated,
        sending: false
      }, () => this.scrollTo(waitingId))
    })
  },

  back() {
    wx.navigateBack({
      fail() {
        wx.switchTab({ url: '/pages/home/index' })
      }
    })
  }
})
