<template>
  <el-card class="chat-panel" shadow="hover">
    <template #header>
      <div class="panel-header">
        <span class="panel-title">
          <el-icon><ChatDotRound /></el-icon>
          智能问答
        </span>
        <div class="header-actions">
          <el-tooltip content="重排序：对检索结果精排，提高准确性">
            <el-switch
              v-model="options.use_rerank"
              active-text="重排序"
              size="small"
              style="margin-right: 12px"
            />
          </el-tooltip>
          <el-tooltip content="查询改写：从多个角度检索，提高召回率">
            <el-switch
              v-model="options.use_rewrite"
              active-text="查询改写"
              size="small"
            />
          </el-tooltip>
        </div>
      </div>
    </template>

    <!-- 对话消息区域 -->
    <div class="chat-messages" ref="messagesRef">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome">
        <el-icon :size="48" color="#409eff"><ChatDotRound /></el-icon>
        <h3>欢迎使用企业知识库</h3>
        <p>请先上传文档，然后基于知识库内容进行提问</p>
        <div class="example-questions">
          <p>示例问题：</p>
          <el-tag
            v-for="q in exampleQuestions"
            :key="q"
            class="example-tag"
            effect="plain"
            @click="sendMessage(q)"
          >
            {{ q }}
          </el-tag>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-for="(msg, index) in messages" :key="index" class="message-item" :class="msg.role">
        <div class="message-avatar">
          <el-icon v-if="msg.role === 'user'" :size="20"><User /></el-icon>
          <el-icon v-else :size="20"><Service /></el-icon>
        </div>
        <div class="message-content">
          <!-- 消息文本 -->
          <div class="message-text" v-html="renderMarkdown(msg.content)"></div>

          <!-- 改写查询展示 -->
          <div v-if="msg.rewritten_queries?.length" class="rewritten-queries">
            <div class="rq-label">
              <el-icon><MagicStick /></el-icon>
              查询改写：
            </div>
            <el-tag v-for="q in msg.rewritten_queries" :key="q" size="small" type="info">
              {{ q }}
            </el-tag>
          </div>

          <!-- 引用来源 -->
          <div v-if="msg.sources?.length" class="sources">
            <div class="sources-label">
              <el-icon><Link /></el-icon>
              引用来源：
            </div>
            <el-collapse>
              <el-collapse-item
                v-for="(src, i) in msg.sources"
                :key="i"
                :title="`${src.source} (相关度: ${(src.score * 100).toFixed(1)}%)`"
              >
                <p class="source-content">{{ src.content }}</p>
              </el-collapse-item>
            </el-collapse>
          </div>

          <!-- 处理时间 -->
          <div v-if="msg.processing_time" class="message-meta">
            耗时 {{ msg.processing_time }}s
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="chatting" class="message-item assistant">
        <div class="message-avatar">
          <el-icon :size="20"><Service /></el-icon>
        </div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="2"
        placeholder="输入你的问题，基于知识库内容回答..."
        :disabled="chatting"
        @keydown.enter.exact.prevent="sendMessage()"
        resize="none"
      />
      <el-button
        type="primary"
        :icon="Promotion"
        :loading="chatting"
        :disabled="!inputText.trim()"
        @click="sendMessage()"
      >
        发送
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref, nextTick, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { chat } from '../api'

const messagesRef = ref(null)
const messages = ref([])
const inputText = ref('')
const chatting = ref(false)

const options = reactive({
  use_rerank: true,
  use_rewrite: true,
})

const exampleQuestions = [
  '公司的核心业务是什么？',
  '介绍一下组织架构',
  '有哪些重要的规章制度？',
]

// 发送消息
const sendMessage = async (text) => {
  const question = text || inputText.value.trim()
  if (!question || chatting.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: question })
  inputText.value = ''
  chatting.value = true
  await scrollToBottom()

  try {
    const { data } = await chat(question, options)

    // 添加助手回复
    messages.value.push({
      role: 'assistant',
      content: data.answer,
      sources: data.sources,
      rewritten_queries: data.rewritten_queries,
      processing_time: data.processing_time,
    })
  } catch (err) {
    const msg = err.response?.data?.detail || '请求失败，请稍后重试'
    messages.value.push({
      role: 'assistant',
      content: `❌ ${msg}`,
    })
    ElMessage.error(msg)
  } finally {
    chatting.value = false
    await scrollToBottom()
  }
}

// Markdown 渲染
const renderMarkdown = (text) => {
  return marked(text || '', { breaks: true })
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-panel :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
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

.header-actions {
  display: flex;
  align-items: center;
}

/* ===== 消息区域 ===== */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 欢迎页 */
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  gap: 12px;
}

.welcome h3 {
  color: #303133;
  font-size: 18px;
}

.example-questions {
  margin-top: 16px;
  text-align: center;
}

.example-questions p {
  font-size: 13px;
  margin-bottom: 8px;
}

.example-tag {
  cursor: pointer;
  margin: 4px;
}

.example-tag:hover {
  color: #409eff;
  border-color: #409eff;
}

/* 消息项 */
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background: #409eff;
  color: #fff;
}

.message-item.assistant .message-avatar {
  background: #67c23a;
  color: #fff;
}

.message-content {
  max-width: 75%;
  min-width: 120px;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message-item.user .message-text {
  background: #409eff;
  color: #fff;
  border-top-right-radius: 4px;
}

.message-item.assistant .message-text {
  background: #f4f4f5;
  color: #303133;
  border-top-left-radius: 4px;
}

.message-text :deep(p) {
  margin: 0 0 8px;
}

.message-text :deep(p:last-child) {
  margin: 0;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

/* 改写查询 */
.rewritten-queries {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fdf6ec;
  border-radius: 8px;
  font-size: 12px;
}

.rq-label {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #e6a23c;
  margin-bottom: 6px;
  font-weight: 500;
}

.rewritten-queries .el-tag {
  margin: 2px 4px 2px 0;
}

/* 引用来源 */
.sources {
  margin-top: 8px;
}

.sources-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.sources :deep(.el-collapse) {
  border: none;
}

.sources :deep(.el-collapse-item__header) {
  font-size: 12px;
  height: 32px;
  background: transparent;
  color: #606266;
}

.sources :deep(.el-collapse-item__content) {
  padding-bottom: 8px;
}

.source-content {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  white-space: pre-wrap;
}

.message-meta {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 4px;
  text-align: right;
}

/* 打字动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 16px;
  background: #f4f4f5;
  border-radius: 12px;
  border-top-left-radius: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c0c4cc;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* ===== 输入区域 ===== */
.chat-input {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  padding: 10px 12px;
}

.chat-input .el-button {
  align-self: flex-end;
  height: 40px;
  border-radius: 8px;
}
</style>
