const config = require('../config/index')

let task = null
let listeners = {}

function dispatch(type, payload) {
  if (listeners[type]) listeners[type](payload)
  if (listeners.message) listeners.message({ type, payload })
}

function connectRealtime(options = {}) {
  listeners = {
    open: options.onOpen,
    close: options.onClose,
    message: options.onMessage
  }

  if (config.enableMock) {
    listeners.open && listeners.open()
    return
  }

  task = wx.connectSocket({
    url: config.wsUrl,
    success: () => {}
  })

  task.onOpen(() => listeners.open && listeners.open())
  task.onClose(() => listeners.close && listeners.close())
  task.onMessage((message) => {
    try {
      const event = JSON.parse(message.data)
      dispatch(event.type, event.payload)
    } catch (error) {
      dispatch('message', message.data)
    }
  })
}

function onRealtime(type, callback) {
  listeners[type] = callback
}

function closeRealtime() {
  if (task) {
    task.close()
    task = null
  }
  listeners.close && listeners.close()
}

module.exports = {
  connectRealtime,
  onRealtime,
  closeRealtime
}
