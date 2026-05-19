import request from './request'

export function getLatestEvaluation() {
  return request.get('/evaluate/latest')
}

export function getErrorSamples(params) {
  return request.get('/error-samples', { params })
}
