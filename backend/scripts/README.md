# 评测与基准脚本

用于量化 RAG 系统检索质量与性能，产出可写进简历/项目介绍的数据。

## 1. 离线检索基准（无需外部服务）

对比中文 BM25「优化前（空格分词）」vs「优化后（jieba 分词）」的检索质量与延迟。

```bash
cd backend
venv\Scripts\activate
venv\Scripts\python.exe -X utf8 scripts\benchmark_retrieval.py
```

输出两类指标：
- **检索质量**：hit@1 / hit@3 / hit@5 / MRR（合成演示语料）
- **检索延迟**：不同语料规模下「逐查询重建索引（旧）」vs「缓存复用（新）」的稳态单次查询耗时、冷启动建索引耗时

> 语料为合成演示数据，用于展示 jieba 分词的收益机制；真实数据请用下面的在线评测。

## 2. 在线 RAG 评测（真实语料，hit@k / MRR）

对已入库的真实知识库评测全流程检索（向量 + BM25 + RRF + 重排）。

前置：`docker-compose up -d postgres redis chromadb`，文档已入库（Celery 处理完成）。

```bash
cd backend
venv\Scripts\activate
venv\Scripts\python.exe -X utf8 scripts\evaluate_rag.py scripts\eval_questions.example.json
```

1. 复制 `eval_questions.example.json` 为 `eval_questions.json`，按真实知识库填写问题与期望来源
2. 运行上述命令，得到 hit@1/3/5 与 MRR 汇总，明细写入 `backend/eval_results.csv`

命中判定：`expected.filename` 精确匹配来源文件名，或 `expected.keyword` 出现在检索文本中。
