/**
 * API 请求封装
 * 统一管理所有后端接口调用
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

// ===== 文档管理 =====

/**
 * 上传文档
 * @param {File} file - 文件对象
 * @param {Function} onProgress - 上传进度回调
 */
export function uploadDocument(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
}

/**
 * 获取文档列表
 */
export function getDocuments(params = {}) {
  return api.get('/documents/', { params })
}

/**
 * 删除文档
 */
export function deleteDocument(docId) {
  return api.delete(`/documents/${docId}`)
}

// ===== 智能问答 =====

/**
 * 发送问答请求
 */
export function chat(question, options = {}) {
  return api.post('/chat/', {
    question,
    ...options,
  })
}

/**
 * 健康检查
 */
export function healthCheck() {
  return api.get('/chat/health')
}

export default api
