import request from './request'

export function startTraining(params) {
  return request.post('/train/start', params)
}

export function getTrainTask(taskId) {
  return request.get(`/train/${taskId}`)
}

export function getTrainLog(taskId) {
  return request.get(`/train/${taskId}/log`)
}
