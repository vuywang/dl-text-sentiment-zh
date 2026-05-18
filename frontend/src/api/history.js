import request from './request'

export function getAnalysisHistory() {
  return request.get('/api/history/analysis')
}

export function getBatchHistory() {
  return request.get('/api/history/batch')
}

export function getTrainHistory() {
  return request.get('/api/history/train')
}

export function getLowConfidenceRecords(params) {
  return request.get('/api/review/low-confidence', { params })
}
