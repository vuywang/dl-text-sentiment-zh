import request from './request'

export function getAnalysisHistory() {
  return request.get('/history/analysis')
}

export function getBatchHistory() {
  return request.get('/history/batch')
}

export function getTrainHistory() {
  return request.get('/history/train')
}

export function getLowConfidenceRecords(params) {
  return request.get('/review/low-confidence', { params })
}
