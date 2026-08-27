function pad(value) {
  return String(value).padStart(2, '0')
}

function formatTime(dateLike) {
  const date = dateLike ? new Date(dateLike.replace(/-/g, '/')) : new Date()
  if (Number.isNaN(date.getTime())) return ''
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function formatDate(dateLike) {
  const date = dateLike ? new Date(dateLike.replace(/-/g, '/')) : new Date()
  if (Number.isNaN(date.getTime())) return ''
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function freshnessText(level) {
  const map = {
    fresh: '新鲜',
    mild: '轻度不新鲜',
    expiring: '临近过期',
    spoiled: '腐败变质',
    warning: '临近过期'
  }
  return map[level] || '待识别'
}

function freshnessTone(level) {
  const map = {
    fresh: 'fresh',
    mild: 'mild',
    expiring: 'expiring',
    spoiled: 'spoiled',
    warning: 'expiring'
  }
  return map[level] || 'info'
}

function deviceStateText(state) {
  const map = {
    online: '在线',
    warning: '需关注',
    offline: '离线'
  }
  return map[state] || '未知'
}

const INVENTORY_FORM_FIELDS = [
  { key: 'name', label: '名称', type: 'text', placeholder: '请输入果蔬名称' },
  { key: 'category', label: '分类', type: 'select', options: ['水果', '蔬菜'] },
  { key: 'quantity', label: '数量', type: 'stepper' },
  { key: 'unit', label: '单位', type: 'text', placeholder: '如 个/根/盒' },
  { key: 'shelfLife', label: '保质期天数', type: 'number', placeholder: '天' },
  { key: 'location', label: '货位', type: 'text', placeholder: '如 A-01 上层' },
  { key: 'storageAdvice', label: '温湿度建议', type: 'text', placeholder: '如 0-4°C · 85-90%RH' }
]

module.exports = {
  formatTime,
  formatDate,
  freshnessText,
  freshnessTone,
  deviceStateText,
  INVENTORY_FORM_FIELDS
}
