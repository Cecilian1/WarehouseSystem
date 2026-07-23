const { recordService } = require('../../services/api')

Page({
  data: {
    navHeight: 100,
    statusTop: 40,
    list: [],
    keyword: '',
    type: '全部',
    types: [
      { label: '全部', value: '全部' },
      { label: '入库', value: 'inbound' },
      { label: '出库', value: 'outbound' },
      { label: '手动修改', value: 'manual' }
    ]
  },
  onLoad() {
    const app = getApp()
    this.setData({
      navHeight: app.globalData.navHeight,
      statusTop: app.globalData.statusBarHeight
    })
    this.load()
  },
  onReachBottom() {
    wx.showToast({ title: '已加载全部记录', icon: 'none' })
  },
  load() {
    return recordService.getList({ keyword: this.data.keyword, type: this.data.type }).then((res) => {
      this.setData({ list: res.data })
    })
  },
  inputKeyword(event) {
    this.setData({ keyword: event.detail.value })
  },
  selectType(event) {
    this.setData({ type: event.currentTarget.dataset.value }, () => this.load())
  },
  search() {
    this.load()
  },
  back() {
    wx.navigateBack()
  }
})
