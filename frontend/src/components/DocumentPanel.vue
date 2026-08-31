<template>
  <el-card class="document-panel" shadow="hover">
    <template #header>
      <div class="panel-header">
        <span class="panel-title">
          <el-icon><FolderOpened /></el-icon>
          文档管理
        </span>
        <el-tag size="small">{{ documents.length }} 个文档</el-tag>
      </div>
    </template>

    <!-- 上传区域 -->
    <el-upload
      class="upload-area"
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      :show-file-list="false"
      accept=".pdf,.docx,.txt,.md"
    >
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <div class="upload-text">拖拽文件到此处，或 <em>点击上传</em></div>
      <div class="upload-hint">支持 PDF / DOCX / TXT / Markdown</div>
    </el-upload>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <el-progress :percentage="uploadProgress" :status="uploadProgress === 100 ? 'success' : ''" />
      <span class="progress-text">{{ uploadingFile }}</span>
    </div>

    <!-- 文档列表 -->
    <div class="doc-list">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中...
      </div>

      <div v-else-if="documents.length === 0" class="empty-state">
        <el-icon :size="40"><Document /></el-icon>
        <p>暂无文档，请上传文件</p>
      </div>

      <div v-else class="doc-items">
        <div v-for="doc in documents" :key="doc.doc_id" class="doc-item">
          <div class="doc-icon">
            <el-icon :size="20" :color="getFileColor(doc.file_type)">
              <Document />
            </el-icon>
          </div>
          <div class="doc-info">
            <div class="doc-name" :title="doc.filename">{{ doc.filename }}</div>
            <div class="doc-meta">
              <span>{{ formatSize(doc.file_size) }}</span>
              <span>{{ doc.chunk_count }} 个文本块</span>
              <el-tag :type="getStatusType(doc.status)" size="small">
                {{ getStatusText(doc.status) }}
              </el-tag>
            </div>
          </div>
          <el-button
            type="danger"
            :icon="Delete"
            circle
            size="small"
            @click="handleDelete(doc)"
          />
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { uploadDocument, getDocuments, deleteDocument } from '../api'

const emit = defineEmits(['refresh'])

const documents = ref([])
const loading = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadingFile = ref('')

// 加载文档列表
const loadDocuments = async () => {
  loading.value = true
  try {
    const { data } = await getDocuments()
    documents.value = data.documents
  } catch (err) {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

// 处理文件选择
const handleFileChange = async (uploadFile) => {
  uploading.value = true
  uploadProgress.value = 0
  uploadingFile.value = uploadFile.name

  try {
    await uploadDocument(uploadFile.raw, (progress) => {
      uploadProgress.value = progress
    })
    ElMessage.success(`文档 "${uploadFile.name}" 上传成功`)
    await loadDocuments()
    emit('refresh')
  } catch (err) {
    const msg = err.response?.data?.detail || '上传失败'
    ElMessage.error(msg)
  } finally {
    uploading.value = false
  }
}

// 删除文档
const handleDelete = async (doc) => {
  try {
    await ElMessageBox.confirm(
      `确定删除文档 "${doc.filename}" 吗？相关向量数据也将被清除。`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteDocument(doc.doc_id)
    ElMessage.success('文档已删除')
    await loadDocuments()
    emit('refresh')
  } catch {
    // 用户取消
  }
}

// 工具函数
const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getFileColor = (type) => {
  const colors = { '.pdf': '#e74c3c', '.docx': '#3498db', '.txt': '#95a5a6', '.md': '#2ecc71' }
  return colors[type] || '#909399'
}

const getStatusType = (status) => {
  const map = { completed: 'success', processing: 'warning', failed: 'danger', pending: 'info' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { completed: '已完成', processing: '处理中', failed: '失败', pending: '等待中' }
  return map[status] || status
}

onMounted(loadDocuments)
</script>

<style scoped>
.document-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.document-panel :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}

/* 上传区域 */
.upload-area {
  margin-bottom: 16px;
}

.upload-area :deep(.el-upload-dragger) {
  padding: 20px;
  border-radius: 8px;
}

.upload-icon {
  font-size: 40px;
  color: #c0c4cc;
  margin-bottom: 8px;
}

.upload-text {
  color: #606266;
  font-size: 14px;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
}

.upload-hint {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

/* 上传进度 */
.upload-progress {
  margin-bottom: 16px;
}

.progress-text {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  display: block;
}

/* 文档列表 */
.doc-list {
  flex: 1;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: #909399;
  gap: 12px;
}

.doc-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: background 0.2s;
}

.doc-item:hover {
  background: #ecf5ff;
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
