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

### 设计决策：为什么 ChromaDB 用 Server 模式而不是嵌入式

**结论**：本项目必须用 Server 模式（独立服务），不能用嵌入式。

**原因**：后端（FastAPI）和 Celery worker 是两个**独立进程**，都要读写同一个向量库：
- backend 读（检索）+ 删（删文档时清理向量）
- Celery 写（文档入库时写 embedding）

嵌入式模式下，每个进程有自己独立的 `.chroma` 数据文件 → **数据分裂**：Celery 入库的文档，后端根本搜不到。强行让两个进程共享同一个 `.chroma` 目录，又会因 SQLite/HNSW 多进程并发写导致锁冲突、损坏。

Server 模式下，两边通过 HTTP 连同一个服务端，数据天然一致，代价只是内网一次 1-2ms 的请求，可忽略。

**何时嵌入式更合适**：单进程应用（无 Celery、文档同步处理）、原型、小工具——少一个容器，更简单。

> 面试要点：能讲清"多进程共享向量库 → 必须 Server 模式"这个取舍，体现对向量库原理和架构的理解。

### 我的职责
从 0 到 1 完成前后端、模型选型、检索链路、部署，并持续做检索质量与性能优化。

> 面试重点：能画出架构图、讲清"为什么这么分层"、"文档和简历两条流水线为什么一个异步一个同步"。
