import request from './request'

export function getModels() {
  return request.get('/api/models')
}

export function activateModel(modelId) {
  return request.post(`/api/models/${modelId}/activate`)
}
