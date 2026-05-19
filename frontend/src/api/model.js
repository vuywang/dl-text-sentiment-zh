import request from './request'

export function getModels() {
  return request.get('/models')
}

export function activateModel(modelId) {
  return request.post(`/models/${modelId}/activate`)
}
