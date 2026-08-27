Component({
  properties: {
    visible: {
      type: Boolean,
      value: false
    },
    title: {
      type: String,
      value: '确认操作'
    },
    desc: {
      type: String,
      value: ''
    },
    confirmText: {
      type: String,
      value: '确认'
    },
    danger: {
      type: Boolean,
      value: false
    }
  },
  methods: {
    noop() {},
    cancel() {
      this.triggerEvent('cancel')
    },
    confirm() {
      this.triggerEvent('confirm')
    }
  }
})
