import request from './request'

export function startTraining(params) {
  return request.post('/api/train/start', params)
}

export function getTrainTask(taskId) {
  return request.get(`/api/train/${taskId}`)
}

export function getTrainLog(taskId) {
  return request.get(`/api/train/${taskId}/log`)
}
