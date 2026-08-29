# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概览

RAG 知识库问答系统：上传 PDF/DOCX/TXT/MD → 解析分块 + Embedding 入 ChromaDB → 混合检索 + 重排 + LLM 流式回答；另有简历 AI 分析与面试题生成。代码注释、提示词均为中文。

技术栈：FastAPI(async) + SQLAlchemy 2 + Alembic ｜ Vue3 + TS + Pinia + Vite6 + Tailwind4 ｜ PostgreSQL16 + ChromaDB + Celery/Redis ｜ DeepSeek/OpenAI 适配器。完整功能与 API 表见 `README.md`，本文件只记命令、架构与坑。

## 命令

```bash
# 首次搭建
docker-compose up -d postgres redis chromadb
cd backend && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt    # 测试依赖（pytest 三件套，不在主 requirements）
cp ../.env.example ../.env                      # 再填入 DEEPSEEK_API_KEY

# 日常开发（前端 /api 会代理到后端，见「坑」）
cd backend && venv\Scripts\activate
alembic upgrade head                            # 迁移文件在 backend/alembic/versions/
uvicorn main:app --reload --port 8080
python Celery.py                                # 新终端；Windows 必须用它，不要 celery -A

cd frontend && npm install && npm run dev       # 端口 3000
npm run build                                   # vue-tsc && vite build（无 lint/test 脚本）

# 测试（纯离线，内存 SQLite）
cd backend && venv\Scripts\activate && pytest tests/ -v

# 评测与基准（详见 backend/scripts/README.md）
venv\Scripts\python.exe -X utf8 scripts\benchmark_retrieval.py   # 离线：jieba vs 旧 BM25
venv\Scripts\python.exe -X utf8 scripts\evaluate_rag.py eval_questions.json  # 在线：真实库 hit@k/MRR
```

Docker 一键部署：`docker-compose up --build`（宿主机 backend=8000，nginx 内网转发）。

## 架构

**分层**：`routers` → `services` → `repositories`，数据形态 `schemas/`(Pydantic) 与 `models/`(ORM)，外部依赖收敛在 `integrations/`。单例靠 `core/dependencies.py` 模块级全局变量懒加载。

**两条处理流水线（核心区别）**：

| | 文档 | 简历 |
|---|---|---|
| 执行 | Celery 异步（`tasks/document_tasks.py`） | 请求内同步 LLM 调用 |
| 流程 | 存盘 → pending → 解析 → 分块(512/64 token) → Embedding → ChromaDB → completed | 解析 → LLM 分析 → 返回 JSON(自动剥 ``` 围栏) |
| 失败 | retry 3×/60s 后置 failed | 直接置 failed |

**双数据库**：API 用 async engine（`Depends(get_db)`），Celery 用 sync `SyncSession`。Repository 里 async/sync 方法并存，别混用。

**RAG 链路**（`services/rag_service.py`）：向量 + BM25 并行 → 过滤 score≥0.3 → RRF(k=60) → 前 100 字符去重 → 中文重排 top5（`maidalun1020/bce-reranker-base_v1`，原英文 cross-encoder 对中文打分失效已被替换）→ 拼 prompt(系统提示 + 带文件名标注的上下文 + 最近 6 条历史) → LLM 流式。BM25 在 `services/bm25.py`：jieba 中文分词，索引按 `VectorStore.texts_revision` 缓存、文档变更自动重建。评测脚本见 `scripts/`（真实库 hit@1=100%/MRR=100%，22 问）。

**SSE 契约**（`routers/chat.py` ↔ `composables/useStreaming.ts`）：逐行发 `data: {json}\n\n`，固定顺序 `sources` → 多个 `token` → `done`。改流格式必须两端同步。

**LLM 适配器**：`integrations/llm/factory.py` 按 `llm_provider` 工厂创建。新服务商 = 新建 Provider 类（实现 `chat`/`chat_stream`）+ factory 注册 + config 字段。embedding/reranker 模型在 lifespan 启动时预加载（首次 5-20s），改相关代码要重启后端才生效。

**前端**：`api/` 走 Axios(baseURL `/api`)；`stores/` 按领域分（chat/document/knowledge），**简历页无 store** 直连 API；`useStreaming.ts` 是唯一 SSE 消费入口；类型集中在 `types/index.ts`。

## 常见任务入口

| 任务 | 看这里 |
|---|---|
| 调检索/重排策略 | `services/rag_service.py`、`integrations/reranker.py` |
| 改分块/解析 | `services/chunking.py`、`integrations/document_parser.py` |
| 加 LLM 服务商 | `integrations/llm/` + `core/config.py` |
| 加/改 API | `routers/` + `schemas/` + `services/` + `repositories/` |
| 改数据库字段 | `models/` + `alembic revision` |
| 改流式交互 | `useStreaming.ts` + `routers/chat.py` |

## 坑

- **HuggingFace 模型必须离线加载（本机特性）**：本机 `HF_ENDPOINT=https://hf-mirror.com`，但镜像对 python 客户端（huggingface_hub 0.36.x）做 TLS 指纹拦截——库下载一律被重定向到被墙的 huggingface.co 失败，curl 却能下。已用 curl 手动下载 embedding（BGE-small-zh）与重排（bce-reranker-base_v1）模型到 `~/.cache/huggingface/hub/`，靠 `HF_HUB_OFFLINE=1` + `TRANSFORMERS_OFFLINE=1` 离线加载（加载约 2s）。`run.bat`/`runCelery.bat` 已内置这两个 env；**手动跑 uvicorn 必须带上**。这些变量**不要写进 `.env`**——会触发 pydantic `extra_forbidden`，且 `.env` 会被 Docker 当 env_file 透传导致容器离线失败。缓存结构注意：`refs/main` 必须**无换行符**（`printf` 写，`echo` 会带 `\n` 导致找不到快照），快照目录用 `snapshots/<commit_sha>/`。
- **本地端口已对齐 8080**：`run.bat`/README 与 `frontend/vite.config.ts` 代理都是 8080。Docker 部署走 8000 内网（nginx 转发）。CORS 白名单仅 3000/5173。
- **`.env` 在仓库根目录**：`core/config.py` 用 `load_dotenv(override=True)` 强制加载并覆盖系统环境变量；改 `Settings` 字段须同步 `.env` 键名。`.env` 含 API Key，勿提交。
- **ChromaDB 端口**：docker-compose 把容器 8000 映射到宿主 **8001**，`.env` 的 `CHROMA_PORT=8001` 匹配。
- **测试依赖**：`requirements-dev.txt` 含 pytest 三件套（主 `requirements.txt` 没有，Docker 镜像也不装）；测试用内存 SQLite（`test_models.py` 有 PG UUID/JSONB 编译 shim），全离线。
- **Windows Celery**：必须 `python Celery.py`（solo pool，绕终端编码）；新增 Windows `.bat` 记得 `chcp 65001`。
- **PDF 预览**：`GET /documents/{id}/content` 返回 `content: null`，只支持浏览器直开原始文件。
- **上传/日志**：文件存 `backend/uploads/`，Loguru 写 `backend/logs/app.log`（10MB 轮转）；`.env`、`uploads/*`、`logs/*.log` 均在 .gitignore。
