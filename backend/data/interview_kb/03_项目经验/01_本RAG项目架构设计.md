## 项目：RAG 智能知识库问答系统 —— 架构设计

### 技术栈
FastAPI（async）+ SQLAlchemy 2 + Alembic ｜ Vue3 + TS + Pinia + Vite ｜ PostgreSQL 16 + ChromaDB + Celery/Redis ｜ DeepSeek/OpenAI 适配 ｜ sentence-transformers

### 整体架构
- **后端分层**：routers → services → repositories，数据形态用 Pydantic Schema / ORM Model 解耦，外部依赖收敛在 integrations（LLM / Embedding / VectorStore / Reranker / Parser）
- **双数据库引擎**：API 走 async engine，Celery 任务走 sync engine，避免连接池冲突
- **两条流水线**：文档处理走 Celery 异步（解析→分块→向量化→入库），简历分析走请求内同步 LLM 调用

### 关键设计
- 单例依赖：core/dependencies 模块级懒加载全局对象
- 模型预热：启动时加载 Embedding + Reranker，首次响应免冷启动
- SSE 流式协议：sources → token → done 三帧，前端 useStreaming 消费
- Docker Compose 一键编排：Postgres + Redis + ChromaDB + 后端 + Celery + 前端

### 我的职责
从 0 到 1 完成前后端、模型选型、检索链路、部署，并持续做检索质量与性能优化。

> 面试重点：能画出架构图、讲清"为什么这么分层"、"文档和简历两条流水线为什么一个异步一个同步"。
