const { freshnessText, freshnessTone } = require('../../utils/format')

Component({
  properties: {
    item: {
      type: Object,
      value: {}
    },
    mode: {
      type: String,
      value: 'card'
    }
  },
  data: {
    startX: 0,
    opened: false
  },
  observers: {
    item(value) {
      this.setData({
        tagText: freshnessText(value.freshness),
        tagTone: freshnessTone(value.freshness)
      })
    }
  },
  lifetimes: {
    attached() {
      const item = this.properties.item || {}
      this.setData({
        tagText: freshnessText(item.freshness),
        tagTone: freshnessTone(item.freshness)
      })
    }
  },
  methods: {
    touchStart(event) {
      if (this.properties.mode === 'card') return
      this.setData({ startX: event.touches[0].clientX })
    },
    touchEnd(event) {
      if (this.properties.mode === 'card') return
      const delta = event.changedTouches[0].clientX - this.data.startX
      if (delta < -35) this.setData({ opened: true })
      if (delta > 35) this.setData({ opened: false })
    },
    tapCard() {
      this.triggerEvent('detail', { id: this.properties.item.id })
    },
    action(event) {
      const type = event.currentTarget.dataset.type
      this.triggerEvent('action', { type, item: this.properties.item })
      this.setData({ opened: false })
    }
  }
})
