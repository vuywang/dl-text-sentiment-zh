export function formatPercent(value, digits = 1) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric)) {
    return '0.0%'
  }
  return `${(numeric * 100).toFixed(digits)}%`
}

export function formatDecimal(value, digits = 4) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) {
    return '--'
  }
  return numeric.toFixed(digits)
}

export function confidenceStatus(confidence) {
  const numeric = Number(confidence || 0)
  if (numeric >= 0.8) {
    return { label: '高可信', type: 'success', color: '#16a34a' }
  }
  if (numeric >= 0.6) {
    return { label: '一般可信', type: 'warning', color: '#f59e0b' }
  }
  return { label: '建议人工复核', type: 'danger', color: '#f97316' }
}

export function sentimentMeta(label) {
  if (label === '积极') {
    return { type: 'success', color: '#16a34a', text: '积极' }
  }
  if (label === '消极') {
    return { type: 'danger', color: '#ef4444', text: '消极' }
  }
  return { type: 'info', color: '#64748b', text: label || '--' }
}

export function truncateText(text, maxLength = 38) {
  if (!text || text.length <= maxLength) {
    return text || '--'
  }
  return `${text.slice(0, maxLength)}...`
}

export function buildTopWords(rows, topN = 10) {
  const counter = new Map()

  rows.forEach((row) => {
    const text = String(row.text || '')
      .replace(/[^\u4e00-\u9fffA-Za-z0-9]+/g, ' ')
      .trim()
    if (!text) {
      return
    }
    text.split(/\s+/).forEach((token) => {
      if (token.length < 2) {
        return
      }
      if (/^[\u4e00-\u9fff]{5,}$/.test(token)) {
        for (let index = 0; index < token.length - 1; index += 1) {
          const slice = token.slice(index, index + 2)
          counter.set(slice, (counter.get(slice) || 0) + 1)
        }
      } else {
        counter.set(token, (counter.get(token) || 0) + 1)
      }
    })
  })

  return [...counter.entries()]
    .sort((left, right) => right[1] - left[1])
    .slice(0, topN)
    .map(([word, count]) => ({ word, count }))
}

export function toChartArray(matrix) {
  if (!Array.isArray(matrix) || matrix.length === 0) {
    return []
  }
  const items = []
  matrix.forEach((row, rowIndex) => {
    row.forEach((value, columnIndex) => {
      items.push([columnIndex, rowIndex, value])
    })
  })
  return items
}
