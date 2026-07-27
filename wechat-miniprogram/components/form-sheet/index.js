Component({
  properties: {
    visible: {
      type: Boolean,
      value: false
    },
    title: {
      type: String,
      value: '编辑信息'
    },
    fields: {
      type: Array,
      value: []
    },
    values: {
      type: Object,
      value: {}
    },
    confirmText: {
      type: String,
      value: '保存'
    }
  },
  data: {
    formValues: {}
  },
  observers: {
    'visible, values': function (visible, values) {
      if (visible) {
        this.setData({ formValues: JSON.parse(JSON.stringify(values || {})) })
      }
    }
  },
  methods: {
    noop() {},
    onInput(event) {
      const key = event.currentTarget.dataset.key
      this.setData({ [`formValues.${key}`]: event.detail.value })
    },
    onSelectOption(event) {
      const { key, value } = event.currentTarget.dataset
      this.setData({ [`formValues.${key}`]: value })
    },
    onStep(event) {
      const { key, delta } = event.currentTarget.dataset
      const current = Number(this.data.formValues[key]) || 0
      const next = Math.max(0, current + Number(delta))
      this.setData({ [`formValues.${key}`]: next })
    },
    cancel() {
      this.triggerEvent('cancel')
    },
    confirm() {
      this.triggerEvent('confirm', { values: this.data.formValues })
    }
  }
})
