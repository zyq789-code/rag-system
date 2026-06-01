# RAG 智能知识库问答系统

基于 RAG（Retrieval-Augmented Generation）架构的企业级智能知识库问答系统，支持多格式文档解析、
语义检索、流式输出、多知识库管理、简历 AI 分析等功能。

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| **前端** | Vue 3 + TypeScript + Pinia + Vite 6 + Tailwind CSS 4 |
| **后端** | Python 3.11 + FastAPI + SQLAlchemy (async) + Alembic |
| **向量数据库** | ChromaDB |
| **关系数据库** | PostgreSQL 16 |
| **任务队列** | Celery + Redis 7 |
| **LLM** | DeepSeek / OpenAI（多服务商适配器） |
| **文档解析** | pypdf + python-docx |
| **Embedding** | BGE-small-zh-v1.5（中文优化） |
| **重排序** | cross-encoder/ms-marco-MiniLM-L-6-v2 |

## 系统架构

```text
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vite)                          │
│         Vue 3 + Pinia + Tailwind CSS + Axios               │
│       http://localhost:3000 （开发） / :80 （生产）         │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP / SSE Streaming
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                     后端 (FastAPI)                          │
│                   http://localhost:8080                     │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Routers  │  │ Services │  │Integrations│  │ Repos     │ │
│  │  chat    │  │  RAG     │  │  LLM      │  │  Document │ │
│  │ documents│  │  Document│  │  Embedding│  │  KB       │ │
│  │ knowledge│  │  Resume  │  │  VectorDB │  │  Conv     │ │
│  │ resume   │  │  KB      │  │  Reranker │  │  Resume   │ │
│  └──────────┘  └──────────┘  │  Parser   │  └────────────┘ │
│                              └──────────┘                  │
└──────┬──────────────┬──────────────────────┬────────────────┘
       │              │                      │
       ▼              ▼                      ▼
┌──────────┐   ┌──────────┐          ┌──────────────┐
│PostgreSQL│   │ ChromaDB │          │    Redis     │
│ 元数据   │   │ 向量存储 │          │ Celery Broker│
└──────────┘   └──────────┘          └──────┬───────┘
                                            │
                                            ▼
                                     ┌──────────────┐
                                     │   Celery     │
                                     │  Worker      │
                                     │ 文档处理任务  │
                                     └──────────────┘
```

## 项目结构

```text
rag-system/
├── docker-compose.yml           # Docker 编排
├── .env.example                 # 环境变量模板
├── README.md
│
├── backend/
│   ├── main.py                  # FastAPI 入口
│   ├── requirements.txt
│   ├── run_worker.py            # Celery Worker 启动脚本
│   ├── Dockerfile
│   │
│   ├── core/                    # 核心配置
│   │   ├── config.py            # Pydantic Settings
│   │   ├── database.py          # SQLAlchemy 引擎/会话
│   │   ├── dependencies.py      # 依赖注入（单例）
│   │   ├── exceptions.py        # 统一异常处理
│   │   └── logging.py           # Loguru 配置
│   │
│   ├── models/                  # ORM 模型
│   │   ├── knowledge_base.py
│   │   ├── document.py
│   │   ├── conversation.py
│   │   └── resume.py
│   │
│   ├── schemas/                 # Pydantic 请求/响应
│   │   ├── chat.py
│   │   ├── document.py
│   │   ├── knowledge.py
│   │   └── resume.py
│   │
│   ├── repositories/            # 数据访问层
│   │   ├── base.py              # 通用 CRUD
│   │   ├── document.py
│   │   ├── knowledge_base.py
│   │   ├── conversation.py
│   │   └── resume.py
│   │
│   ├── services/                # 业务逻辑
│   │   ├── rag_service.py       # RAG 问答核心
│   │   ├── document_service.py
│   │   ├── knowledge_service.py
│   │   ├── resume_service.py
│   │   └── chunking.py          # 文本分块
│   │
│   ├── integrations/            # 外部服务适配器
│   │   ├── llm/
│   │   │   ├── base.py          # LLM 抽象接口
│   │   │   ├── deepseek.py
│   │   │   ├── openai.py
│   │   │   └── factory.py
│   │   ├── embedding.py         # BGE Embedding
│   │   ├── vector_store.py      # ChromaDB 客户端
│   │   ├── reranker.py          # Cross-Encoder 重排
│   │   └── document_parser.py   # PDF/DOCX/TXT 解析
│   │
│   ├── tasks/                   # Celery 异步任务
│   │   ├── celery_app.py
│   │   └── document_tasks.py    # 文档处理流水线
│   │
│   ├── routers/                 # API 路由
│   │   ├── health.py
│   │   ├── chat.py
│   │   ├── documents.py
│   │   ├── knowledge.py
│   │   └── resume.py
│   │
│   └── tests/                   # 测试
│       ├── test_models.py
│       ├── test_schemas.py
│       ├── test_repositories.py
│       ├── test_llm.py
│       ├── test_integrations.py
│       ├── test_chunking.py
│       ├── test_rag.py
│       ├── test_document_service.py
│       └── conftest.py
│
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   │
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── style.css             # 全局样式 + CSS 变量
│       │
│       ├── router/index.ts       # 路由配置
│       ├── types/index.ts        # TypeScript 类型
│       │
│       ├── api/                  # API 层
│       │   ├── client.ts         # Axios 实例
│       │   ├── chat.ts
│       │   ├── documents.ts
│       │   ├── knowledge.ts
│       │   └── resume.ts
│       │
│       ├── stores/               # Pinia 状态管理
│       │   ├── chat.ts
│       │   ├── document.ts
│       │   └── knowledge.ts
│       │
│       ├── composables/          # 组合式函数
│       │   └── useStreaming.ts   # SSE 流式连接
│       │
│       ├── views/
│       │   ├── ChatView.vue
│       │   ├── DocumentsView.vue
│       │   ├── KnowledgeView.vue
│       │   └── ResumeView.vue
│       │
│       └── components/
│           ├── layout/
│           │   ├── AppLayout.vue
│           │   └── SideNav.vue
│           ├── chat/
│           │   ├── ChatPanel.vue
│           │   ├── MessageList.vue
│           │   └── SourceCard.vue
│           ├── documents/
│           │   ├── UploadZone.vue
│           │   └── DocumentList.vue
│           ├── knowledge/
│           │   ├── KnowledgeForm.vue
│           │   └── KnowledgeList.vue
│           └── resume/
│               ├── ResumeUpload.vue
│               └── AnalysisView.vue
```

## 数据库设计

### PostgreSQL 表结构

```sql
-- 知识库
CREATE TABLE knowledge_bases (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- 文档
CREATE TABLE documents (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE SET NULL,
    filename         VARCHAR(500) NOT NULL,          -- 存储文件名
    original_name    VARCHAR(500) NOT NULL,           -- 原始文件名
    file_type        VARCHAR(20) NOT NULL,            -- pdf/docx/txt/md
    file_size        BIGINT NOT NULL,
    status           VARCHAR(20) DEFAULT 'pending',   -- pending/processing/completed/failed
    chunk_count      INTEGER DEFAULT 0,
    error_message    TEXT,
    file_path        VARCHAR(1000),                   -- 文件绝对路径
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

-- 对话
CREATE TABLE conversations (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title      VARCHAR(500),
    kb_id      UUID REFERENCES knowledge_bases(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 消息
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,             -- user / assistant
    content         TEXT NOT NULL,
    sources         JSONB,                            -- 引用来源
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 简历分析
CREATE TABLE resume_analyses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename        VARCHAR(500) NOT NULL,
    file_path       VARCHAR(1000),
    analysis_result JSONB,                            -- LLM 结构化分析结果
    status          VARCHAR(20) DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT NOW()
);
```text

### ChromaDB 向量存储

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | `{document_id}_{chunk_index}` |
| document | string | 文本块内容 |
| embedding | float[] | BGE-small-zh-v1.5 512 维向量 |
| metadata.filename | string | 原始文件名 |
| metadata.document_id | string | 文档 UUID |
| metadata.knowledge_base_id | string | 所属知识库（可选） |
| metadata.chunk_index | int | 分块序号 |
| metadata.token_count | int | token 数量 |

## API 接口

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledge-bases/` | 创建知识库 |
| GET | `/api/knowledge-bases/` | 知识库列表（含文档数量） |
| GET | `/api/knowledge-bases/{id}` | 知识库详情 |
| PUT | `/api/knowledge-bases/{id}` | 更新知识库 |
| DELETE | `/api/knowledge-bases/{id}` | 删除知识库（同时删除关联文档） |

### 文档

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/documents/upload` | 上传文档（可指定 kb_id） |
| GET | `/api/documents/` | 文档列表（可按 kb_id 筛选） |
| GET | `/api/documents/{id}` | 文档详情 |
| GET | `/api/documents/{id}/content` | 文档文本内容（TXT/MD/DOCX） |
| GET | `/api/documents/{id}/file` | 下载原始文件（PDF 浏览器预览） |
| GET | `/api/documents/{id}/status` | 处理状态 |
| DELETE | `/api/documents/{id}` | 删除文档（同时清理 ChromaDB） |

### 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/completions` | SSE 流式问答 |
| GET | `/api/chat/conversations` | 对话列表 |
| GET | `/api/chat/conversations/{id}/messages` | 历史消息 |
| DELETE | `/api/chat/conversations/{id}` | 删除对话 |

### 简历

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/resume/upload` | 上传并分析简历 |
| GET | `/api/resume/{id}` | 分析结果 |
| POST | `/api/resume/{id}/interview` | 生成面试题 |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 服务状态 |

## RAG 核心流水线

### 文档处理

```
用户上传文件
  → API 保存文件到磁盘
  → 写入 documents 表 (status=pending)
  → Celery 异步任务:
    1. 文档解析 (pypdf/python-docx) → 纯文本
    2. 文本分块 (滑动窗口, chunk_size=512, overlap=64)
    3. Embedding (BGE-small-zh-v1.5) → 512 维向量
    4. 写入 ChromaDB
    5. 更新 documents 表 (status=completed, chunk_count=N)
```text

### 问答流水线

```
用户提问
  → 混合检索：
     ├── 向量检索 (top_k=20)
     └── BM25 关键词检索 (top_k=20)
  → RRF 融合 (Reciprocal Rank Fusion)
  → 按文本去重
  → Cross-Encoder 重排序 → top 5
  → 构建 Prompt (System + 上下文 + 历史消息 + 问题)
  → LLM 流式生成 → SSE 推送
```text

### LLM 适配器

```python
class LLMProvider(ABC):
    async def chat(self, messages, **kwargs) -> str
    async def chat_stream(self, messages, **kwargs) -> AsyncIterator[str]

# 工厂模式: create_llm_provider(settings)
# 支持: DeepSeek、OpenAI
```

### 性能优化

| 优化项 | 说明 |
|--------|------|
| 模型预加载 | Embedding 和 Reranker 模型在启动时预加载 |
| 混合检索 | 向量 + BM25 并行执行 |
| 低 Temperature | Temperature=0.1，输出更稳定 |
| 混合检索并行 | 向量与 BM25 并行执行 |

## 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+（或 Bun）
- Docker（PostgreSQL、Redis、ChromaDB）

### 1. 启动基础服务

```bash
docker-compose up -d postgres redis chromadb
```bash

### 2. 后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
cp ../.env.example ../.env
# 编辑 .env 填入 API Key

alembic upgrade head     # 数据库迁移
uvicorn main:app --reload --port 8080
```

### 3. Celery Worker

```bash
# 新终端
cd backend
venv\Scripts\activate
python run_worker.py
```text

### 4. 前端

```bash
cd frontend
bun install    # 或 npm install
bun run dev    # 或 npm run dev
```

访问 http://localhost:3000

### Docker 一键部署

```bash
docker-compose up --build
```bash

## 环境变量

```ini
# LLM
LLM_PROVIDER=deepseek              # deepseek / openai
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
# OPENAI_API_KEY=sk-xxx
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=rag_system

# Redis
REDIS_URL=redis://localhost:6379/0

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Embedding
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# App
UPLOAD_DIR=./uploads
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K_VECTOR=20
TOP_K_RERANK=5
```

## 前端设计

- **配色**: 深色侧边栏 (`#0F172A`) + 白色内容区，Indigo (`#4F46E5`) 主色调
- **字体**: Inter (正文) + Plus Jakarta Sans (标题)
- **布局**: 固定侧边栏 64px + 自适应主内容区
- **动画**: 页面切换渐变动画、hover 效果、加载旋转动画
- **响应式**: 基于 Tailwind CSS 的响应式设计

## License

MIT

---

## FAQ / 常见问题

### 启动后 API 返回 404？

确认后端端口（默认 8080）未被占用。如有残留进程：

```bash
netstat -ano | findstr ":8080"
taskkill /F /PID <进程ID>
```bash

### 为什么第一次请求很慢？

首次启动需加载 Embedding 模型（BGE-small-zh-v1.5）和重排序模型（Cross-Encoder），约 5-20 秒。模型加载完成后所有请求均为秒级响应。

### ChromaDB 连不上？

```bash
docker ps | grep chromadb
docker logs rag-system-chromadb-1
```

### 文档上传后状态一直是 `pending`？

Celery Worker 未启动。另开终端运行：

```bash
cd backend
venv\Scripts\activate
python run_worker.py
```text

### 如何切换 LLM 提供商？

编辑 `.env` 文件：

```ini
# DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxx

# 或 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
```

---

## 测试指南

```bash
cd backend
venv\Scripts\activate
pytest tests/ -v
```bash

| 测试文件 | 测试内容 |
|---------|---------|
| `test_rag.py` | RAG 搜索与提示构建 |
| `test_llm.py` | LLM 适配器 |
| `test_chunking.py` | 文本分块 |
| `test_models.py` | ORM 模型 |
| `test_schemas.py` | Pydantic 验证 |
| `test_repositories.py` | 数据访问层 |

---

## 更新日志

### v1.0.0 (2026-06-01)

- RAG 问答、文档管理、知识库管理、简历分析
- 混合检索（向量 + BM25）+ Cross-Encoder 重排
- Vue 3 + Tailwind CSS 4 前端
- Docker Compose 部署
- DeepSeek / OpenAI 多适配器
