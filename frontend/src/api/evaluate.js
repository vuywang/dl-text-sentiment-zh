import request from './request'

export function getLatestEvaluation() {
  return request.get('/api/evaluate/latest')
}

export function getErrorSamples(params) {
  return request.get('/api/error-samples', { params })
}
