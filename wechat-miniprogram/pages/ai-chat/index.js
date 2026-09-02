const { assistantService, voiceService } = require('../../services/api')
const { applyPageTheme } = require('../../utils/theme')

const PRESETS = {
  voice: {
    title: '语音对话',
    subtitle: '说出问题，芯鲜助手会马上回答',
    question: '',
    placeholder: '也可以输入文字提问…',
    icon: 'voice'
  },
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
    scrollTarget: '',
    voiceMode: false,
    recording: false,
    voiceStatus: '按住麦克风说话'
  },

  onLoad(options) {
    const app = getApp()
    const type = PRESETS[options.type] ? options.type : 'freshness'
    const preset = PRESETS[type]
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight,
      type,
      preset,
      voiceMode: type === 'voice'
    })
    applyPageTheme(this)
    if (preset.question) this.sendQuestion(preset.question)
    if (type === 'voice') this.initRecorder()
  },

  onShow() {
    applyPageTheme(this)
  },

  onHide() {
    this.stopVoice()
  },

  onUnload() {
    this.stopVoice()
    if (this.currentAudio) {
      this.currentAudio.destroy()
      this.currentAudio = null
    }
    if (this.recorder) {
      if (this.recorder.offStart) this.recorder.offStart(this.handleRecorderStart)
      if (this.recorder.offStop) this.recorder.offStop(this.handleRecorderStop)
      if (this.recorder.offError) this.recorder.offError(this.handleRecorderError)
    }
  },

  initRecorder() {
    this.recorder = wx.getRecorderManager()
    this.handleRecorderStart = () => {
      this.setData({ recording: true, voiceStatus: '正在聆听，松开后识别…' })
    }
    this.handleRecorderStop = (result) => {
      this.setData({ recording: false, voiceStatus: '正在识别…' })
      if (!result || !result.tempFilePath) {
        this.setData({ voiceStatus: '没有获取到录音，请重试' })
        return
      }
      voiceService.transcribe(result.tempFilePath).then((response) => {
        const transcript = response.data && response.data.transcript
        if (!transcript) throw new Error('没有识别到清晰语音')
        this.sendVoiceQuestion(transcript)
      }).catch((error) => {
        this.setData({ voiceStatus: error.message || '语音识别失败，请重试' })
      })
    }
    this.handleRecorderError = (error) => {
      const message = error && error.errMsg && error.errMsg.includes('auth')
        ? '请先允许小程序使用麦克风'
        : '录音失败，请重试'
      this.setData({ recording: false, voiceStatus: message })
    }
    this.recorder.onStart(this.handleRecorderStart)
    this.recorder.onStop(this.handleRecorderStop)
    this.recorder.onError(this.handleRecorderError)
  },

  startVoice() {
    if (!this.data.voiceMode || this.data.sending || this.data.recording) return
    if (!this.recorder) this.initRecorder()
    this.setData({ recording: true, voiceStatus: '正在启动麦克风…' })
    try {
      this.recorder.start({
        duration: 60000,
        format: 'mp3',
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000
      })
    } catch (error) {
      this.setData({ recording: false, voiceStatus: '请允许小程序使用麦克风' })
    }
  },

  stopVoice() {
    if (!this.recorder || !this.data.recording) return
    try {
      this.recorder.stop()
    } catch (error) {
      this.setData({ recording: false, voiceStatus: '录音结束失败，请重试' })
    }
  },

  playAnswer(filePath) {
    if (!filePath) return
    if (this.currentAudio) this.currentAudio.destroy()
    const audio = wx.createInnerAudioContext()
    this.currentAudio = audio
    audio.src = filePath
    audio.onEnded(() => {
      audio.destroy()
      if (this.currentAudio === audio) this.currentAudio = null
      this.setData({ voiceStatus: '回答完成，按住麦克风继续提问' })
    })
    audio.onError(() => {
      audio.destroy()
      if (this.currentAudio === audio) this.currentAudio = null
      this.setData({ voiceStatus: '文字回答完成，语音播放失败' })
    })
    audio.play()
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
    if (this.data.voiceMode) this.sendVoiceQuestion(question)
    else this.sendQuestion(question)
  },

  retry(event) {
    if (this.data.sending) return
    const sender = this.data.voiceMode ? this.sendVoiceQuestion : this.sendQuestion
    sender.call(this, event.currentTarget.dataset.question, {
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

  sendVoiceQuestion(question, options = {}) {
    const normalizedQuestion = String(question || '').trim()
    if (!normalizedQuestion || this.data.sending) return Promise.resolve()

    let messages = this.data.messages.slice()
    if (options.removeMessageId) {
      messages = messages.filter((message) => message.id !== options.removeMessageId)
    }
    const history = this.historyFrom(messages, normalizedQuestion)
    if (options.appendUser !== false) {
      messages.push({ id: nextMessageId(), role: 'user', content: normalizedQuestion })
    }
    const waitingId = nextMessageId()
    messages.push({ id: waitingId, role: 'assistant', content: '', loading: true })
    this.setData({
      messages,
      sending: true,
      voiceStatus: '正在查询仓储数据并生成回答…'
    }, () => this.scrollTo(waitingId))

    return voiceService.chat(normalizedQuestion, history).then((response) => {
      const answer = response.data || {}
      const reply = answer.reply || '暂时没有得到回答'
      const updated = this.data.messages.map((message) => (
        message.id === waitingId
          ? {
            id: waitingId,
            role: 'assistant',
            content: reply,
            urgency: { label: '已回答', tone: 'normal' },
            bullets: [],
            format: 'paragraph',
            sourceLabel: '芯鲜 AI 语音助手',
            generatedTime: '刚刚',
            grounded: true
          }
          : message
      ))
      this.setData({
        messages: updated,
        sending: false,
        voiceStatus: '正在播报回答…'
      }, () => this.scrollTo(waitingId))

      return voiceService.synthesize(reply).then((audioResult) => {
        this.playAnswer(audioResult.tempFilePath)
      }).catch(() => {
        this.setData({ voiceStatus: '文字回答完成，语音合成失败' })
      })
    }).catch((error) => {
      const updated = this.data.messages.map((message) => (
        message.id === waitingId
          ? {
            id: waitingId,
            role: 'assistant',
            content: '',
            error: error.message || '语音助手暂时无法回答，请稍后再试',
            question: normalizedQuestion
          }
          : message
      ))
      this.setData({
        messages: updated,
        sending: false,
        voiceStatus: error.message || '语音回答失败，请重试'
      }, () => this.scrollTo(waitingId))
    })
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
