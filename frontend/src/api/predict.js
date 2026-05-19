import request from './request'

export function predictText(text) {
  return request.post('/predict', { text })
}
