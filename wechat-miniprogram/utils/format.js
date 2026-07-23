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

module.exports = {
  formatTime,
  formatDate,
  freshnessText,
  freshnessTone,
  deviceStateText
}
