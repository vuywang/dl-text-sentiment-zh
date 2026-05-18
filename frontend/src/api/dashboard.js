import request from './request'

export function getDashboardSummary() {
  return request.get('/api/dashboard/summary')
}

export function getDashboardCharts() {
  return request.get('/api/dashboard/charts')
}
