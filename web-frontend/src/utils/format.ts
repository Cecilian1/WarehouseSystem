export const formatNumber = (value: number, digits = 0) =>
  new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)

export const formatPercent = (value: number, digits = 0) => `${(value * 100).toFixed(digits)}%`

export const formatDateTime = (date: Date | string) => {
  const value = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(value)
}

export const freshnessLabel = {
  fresh: '新鲜',
  warning: '临期',
  spoiled: '腐败',
} as const

export const freshnessTone = {
  fresh: 'success',
  warning: 'warning',
  spoiled: 'danger',
} as const
