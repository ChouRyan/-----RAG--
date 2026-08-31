<template>
  <div class="app-container">
    <!-- 顶部导航 -->
    <el-header class="app-header">
      <div class="header-left">
        <el-icon :size="24" color="#409eff"><Collection /></el-icon>
        <h1 class="app-title">企业知识库 RAG 系统</h1>
      </div>
      <div class="header-right">
        <el-tag :type="healthStatus === 'healthy' ? 'success' : 'danger'" size="small">
          {{ healthStatus === 'healthy' ? '系统正常' : '系统异常' }}
        </el-tag>
      </div>
    </el-header>

    <!-- 主体区域 -->
    <el-main class="app-main">
      <el-row :gutter="20" class="main-row">
        <!-- 左侧：文档管理 -->
        <el-col :span="8">
          <DocumentPanel @refresh="checkHealth" />
        </el-col>

        <!-- 右侧：问答对话 -->
        <el-col :span="16">
          <ChatPanel />
        </el-col>
      </el-row>
    </el-main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { healthCheck } from './api'
import DocumentPanel from './components/DocumentPanel.vue'
import ChatPanel from './components/ChatPanel.vue'

const healthStatus = ref('unknown')

const checkHealth = async () => {
  try {
    const { data } = await healthCheck()
    healthStatus.value = data.status
  } catch {
    healthStatus.value = 'error'
  }
}

onMounted(checkHealth)
</script>

<style>
/* ===== 全局样式重置 ===== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f0f2f5;
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ===== 顶部导航 ===== */
.app-header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  z-index: 10;
  height: 60px !important;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

/* ===== 主体区域 ===== */
.app-main {
  flex: 1;
  padding: 20px;
  overflow: hidden;
}

.main-row {
  height: 100%;
}

.main-row .el-col {
  height: 100%;
}
</style>
