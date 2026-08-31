# 企业知识库 RAG 系统

基于 **RAG（Retrieval-Augmented Generation）** 技术的企业级知识库问答系统，支持文档上传解析、向量检索、语义问答、引用溯源和多种 RAG 优化策略。

## 📸 系统预览

```
┌─────────────────────────────────────────────────────────────────┐
│  🏢 企业知识库 RAG 系统                              ● 系统正常  │
├────────────────────────┬────────────────────────────────────────┤
│  📁 文档管理 (3)       │  💬 智能问答            [重排序] [改写]  │
│                        │                                        │
│  ┌──────────────────┐  │  ┌────────────────────────────────────┐│
│  │  📎 拖拽上传文件  │  │  │  👤 公司的核心业务是什么？          ││
│  └──────────────────┘  │  │                                    ││
│                        │  │  🤖 根据文档，公司主要业务包括...    ││
│  📄 公司制度手册.pdf    │  │                                    ││
│   23个文本块 ✓         │  │  📎 引用来源:                       ││
│                        │  │   • 公司制度手册.pdf (92.3%)        ││
│  📄 产品介绍.docx       │  │   • 年度报告.pdf (87.1%)           ││
│   15个文本块 ✓         │  │                                    ││
│                        │  │  ┌──────────────────────────────┐  ││
│  📄 年度报告.pdf        │  │  │  输入你的问题...      [发送]  │  ││
│   42个文本块 ✓         │  │  └──────────────────────────────┘  ││
│                        │  └────────────────────────────────────┘│
└────────────────────────┴────────────────────────────────────────┘
```

## 🏗️ 技术架构

```
┌──────────────────────────────────────────────────────────────┐
│                        Vue3 前端                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ 文档上传面板 │  │  对话聊天界面 │  │  RAG 优化开关面板    │ │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘ │
└─────────┼────────────────┼──────────────────────┼─────────────┘
          │                │                      │
          ▼                ▼                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务                            │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐   │
│  │                    RAG 链 (RAGChain)                   │   │
│  │                                                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐  │   │
│  │  │ 查询改写 │→│ 向量检索 │→│ 重排序   │→│ 生成 │  │   │
│  │  │ Rewrite  │  │ Retrieve │  │ Rerank   │  │ Gen  │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────┘  │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ 文档解析器   │  │ 向量存储     │  │ LLM / Embedding   │  │
│  │ PDF/DOCX/TXT │  │ Chroma DB    │  │ OpenAI API        │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## ✨ 核心功能

### 1. 📄 文档上传解析
- 支持格式：**PDF、DOCX、TXT、Markdown**
- 智能分块：递归字符分割，支持中文语义断句
- 自动向量化：上传后自动 Embedding 并存入 Chroma

### 2. 🔍 向量检索
- 基于 Chroma 向量数据库的高效相似度检索
- 支持多文档跨库检索
- 支持按文件名过滤

### 3. 💬 语义问答
- 基于 LangChain 的 RAG 问答链
- 多轮对话支持
- 回答中自动引用来源文档

### 4. 📎 引用溯源
- 每个回答附带引用来源列表
- 显示来源文件名、相关度分数、文本片段
- 可展开查看具体引用内容

### 5. ⚡ RAG 优化

#### 查询改写（Query Rewriting）
- LLM 自动将用户问题改写为多个不同角度的查询
- 多查询检索后合并去重，提高召回率

#### 重排序（Reranking）
- 使用 Cross-Encoder 模型（BAAI/bge-reranker-v2-m3）对检索结果精排
- 支持 LLM-based 重排序备选方案
- 显著提高最终回答的准确性

## 📁 项目结构

```
企业知识库RAG系统/
├── backend/                        # 后端服务
│   ├── app/
│   │   ├── main.py                 # FastAPI 应用入口
│   │   ├── config.py               # 配置管理
│   │   ├── api/
│   │   │   ├── upload.py           # 文档上传 API
│   │   │   └── chat.py             # 问答对话 API
│   │   ├── services/
│   │   │   ├── document_parser.py  # 文档解析服务
│   │   │   ├── vector_store.py     # 向量存储服务
│   │   │   ├── rag_chain.py        # RAG 链核心逻辑
│   │   │   └── reranker.py         # 重排序服务
│   │   └── models/
│   │       └── schemas.py          # 数据模型定义
│   ├── uploads/                    # 上传文件存储
│   ├── data/chroma/                # Chroma 向量数据库
│   ├── requirements.txt            # Python 依赖
│   ├── .env.example                # 环境变量模板
│   └── Dockerfile                  # 后端容器配置
│
├── frontend/                       # 前端应用
│   ├── src/
│   │   ├── App.vue                 # 主应用组件
│   │   ├── main.js                 # 入口文件
│   │   ├── api/index.js            # API 请求封装
│   │   └── components/
│   │       ├── DocumentPanel.vue   # 文档管理面板
│   │       └── ChatPanel.vue       # 对话聊天面板
│   ├── package.json                # 前端依赖
│   ├── vite.config.js              # Vite 配置
│   ├── nginx.conf                  # Nginx 配置
│   └── Dockerfile                  # 前端容器配置
│
├── docker-compose.yml              # Docker 编排配置
├── start-backend.bat               # Windows 启动后端
├── start-frontend.bat              # Windows 启动前端
├── start-all.bat                   # Windows 一键启动
└── README.md                       # 项目文档
```

## 🚀 快速开始

### 方式一：本地开发（推荐）

#### 1. 环境准备

- Python 3.11+
- Node.js 18+
- OpenAI API Key（或兼容接口）

#### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

关键配置项：
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1    # 可替换为兼容接口
LLM_MODEL=gpt-4o-mini                         # 可替换为其他模型
EMBEDDING_MODEL=text-embedding-3-small         # Embedding 模型
```

#### 3. 一键启动（Windows）

双击运行 `start-all.bat`，自动启动前后端服务。

#### 4. 手动启动

**启动后端：**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**启动前端：**
```bash
cd frontend
npm install
npm run dev
```

#### 5. 访问系统

- 前端界面：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 方式二：Docker 部署

```bash
# 1. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env

# 2. 构建并启动
docker-compose up -d --build

# 3. 访问
# 前端: http://localhost:3000
# 后端: http://localhost:8000
```

## 📡 API 接口

### 文档管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/documents/upload` | 上传文档 |
| GET | `/api/documents/` | 获取文档列表 |
| GET | `/api/documents/{doc_id}` | 获取文档详情 |
| DELETE | `/api/documents/{doc_id}` | 删除文档 |

### 智能问答

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/` | 发送问答请求 |
| GET | `/api/chat/health` | 健康检查 |

### 问答请求示例

```json
POST /api/chat/
{
  "question": "公司的核心业务是什么？",
  "top_k": 10,
  "use_rerank": true,
  "use_rewrite": true
}
```

### 问答响应示例

```json
{
  "answer": "根据公司文档，核心业务包括...",
  "sources": [
    {
      "content": "公司主要从事...",
      "source": "公司制度手册.pdf",
      "page": 3,
      "score": 0.9234,
      "chunk_id": "abc-123"
    }
  ],
  "rewritten_queries": [
    "公司的主营业务有哪些？",
    "企业核心竞争力是什么？"
  ],
  "processing_time": 2.35
}
```

## ⚙️ 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `CHUNK_SIZE` | 500 | 文本分块大小（字符） |
| `CHUNK_OVERLAP` | 50 | 分块重叠字符数 |
| `RETRIEVER_TOP_K` | 10 | 初始检索返回数 |
| `RERANK_TOP_N` | 5 | 重排序后保留数 |
| `USE_RERANKER` | true | 是否启用重排序 |
| `USE_QUERY_REWRITE` | true | 是否启用查询改写 |
| `QUERY_REWRITE_NUM` | 3 | 改写查询数量 |

## 🔧 扩展建议

### 生产环境优化
- 使用 **PostgreSQL + pgvector** 替换 Chroma 作为向量数据库
- 添加用户认证和权限管理（JWT）
- 使用 **Redis** 缓存热门问答结果
- 接入 **Celery** 异步处理大文件上传

### RAG 优化方向
- **HyDE**：先让 LLM 生成假设性回答，再用回答做检索
- **Parent-Child Chunking**：小块检索，大块上下文
- **知识图谱增强**：结合实体关系进行图检索
- **多模态支持**：支持图片、表格的解析和检索

### 模型替换
- 本地模型：使用 **Ollama** 部署 Qwen2.5、Llama3 等开源模型
- 国内接口：替换 `OPENAI_BASE_URL` 为国内兼容接口
- 专用 Embedding：使用 **BGE-M3** 等中文优化 Embedding 模型

## 📝 更新日志

### v1.0.0 (2025-01)
- ✅ 文档上传解析（PDF/DOCX/TXT/MD）
- ✅ Chroma 向量存储和检索
- ✅ RAG 问答链
- ✅ 查询改写优化
- ✅ Cross-Encoder 重排序
- ✅ 引用溯源展示
- ✅ Vue3 可视化界面
- ✅ Docker 部署支持

## 📄 许可证

MIT License
