Component({
  properties: {
    visible: {
      type: Boolean,
      value: false
    },
    title: {
      type: String,
      value: ''
    }
  },
  methods: {
    noop() {},
    close() {
      this.triggerEvent('close')
    }
  }
})
