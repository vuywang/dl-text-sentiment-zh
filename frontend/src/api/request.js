import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '/',
  timeout: 60000,
})

service.interceptors.response.use(
  (response) => {
    if (response.config.responseType === 'blob' || response.config.rawResponse) {
      return response
    }

    const payload = response.data
    if (payload && typeof payload === 'object' && 'code' in payload) {
      if (payload.code === 0) {
        return payload.data
      }
      const message = payload.message || '请求失败'
      if (!response.config.silentError) {
        ElMessage.error(message)
      }
      return Promise.reject(new Error(message))
    }

    return payload
  },
  (error) => {
    const message = error.response?.data?.message || error.message || '网络请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default service
