Component({
  properties: {
    title: {
      type: String,
      value: '暂无数据'
    },
    desc: {
      type: String,
      value: ''
    },
    buttonText: {
      type: String,
      value: ''
    },
    icon: {
      type: String,
      value: 'box'
    }
  },
  methods: {
    onAction() {
      this.triggerEvent('action')
    }
  }
})
