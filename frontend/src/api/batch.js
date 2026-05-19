import request from './request'

export function uploadBatchFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/batch/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export function getBatchDetail(taskId) {
  return request.get(`/batch/${taskId}`)
}

export function getBatchDownloadUrl(taskId) {
  return `/api/batch/${taskId}/download`
}
