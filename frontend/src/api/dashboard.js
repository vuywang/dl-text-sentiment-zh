import request from './request'

export function getDashboardSummary() {
  return request.get('/dashboard/summary')
}

export function getDashboardCharts() {
  return request.get('/dashboard/charts')
}
