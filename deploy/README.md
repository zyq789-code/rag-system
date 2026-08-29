# ECS 部署指南（大陆节点 · Docker Compose）

把 RAG 知识库系统部署到大陆阿里云 ECS，IP 直连访问。**全程约 30~60 分钟**（含模型下载与镜像构建）。

---

## ⚠️ 先看：安全提醒

**本项目当前没有登录/鉴权**。部署到公网后，任何知道你 IP 的人都能：
- 免费使用你的对话（**消耗你的 DeepSeek API Key 额度**）
- 上传 / 删除文档和知识库

**建议二选一**：
1. **演示完就删**：短期展示，用 `docker compose down -v` 清理，不常驻公网
2. **加一层 Nginx Basic Auth**：见文末「附录：加访问口令」——几分钟配好，强烈推荐

---

## 一、前置准备（在你自己电脑 / 云控制台操作）

1. **一台大陆 ECS**（2核4G 起，4核8G 更稳；Ubuntu 22.04 / Debian 12）
2. **安全组放行端口**（阿里云控制台 → 安全组 → 入方向规则）：
   | 端口 | 用途 |
   |------|------|
   | `22` | SSH（通常已开） |
   | `80` | 前端访问 |
   | `8000` | 后端 API（可选，方便直接调试） |
3. **DeepSeek API Key**：准备好 `sk-xxx`
4. **代码已在 GitHub**（本项目已公开）：`https://github.com/zyq789-code/rag-system`

---

## 二、步骤

### Step 1 登录服务器，把脚本拉上去并初始化

```bash
# 在本机终端（或云控制台"远程连接"）SSH 登录
ssh root@你的服务器IP

# 安装 Docker + Compose 插件 + 镜像加速（大陆源）
curl -fsSL https://raw.githubusercontent.com/zyq789-code/rag-system/master/deploy/setup_server.sh -o setup_server.sh
sudo bash setup_server.sh
docker --version && docker compose version   # 确认安装成功
```

### Step 2 拉取代码 + 配置环境变量

```bash
git clone https://github.com/zyq789-code/rag-system.git
cd rag-system

# 用部署专用模板生成 .env，填入真实 Key
cp deploy/.env.example .env
vim .env    # 把 DEEPSEEK_API_KEY 改成你的 key
```

> `.env` 里数据库/缓存/向量库用的是**容器服务名**（postgres/redis/chromadb），
> ChromaDB 是容器内端口 `8000`——这与本地开发不同，**不要**直接复制本机 `.env`。

### Step 3 预下载模型（大陆关键步骤）

```bash
# 从 hf-mirror.com 用 curl 下载 Embedding + 重排模型（约 1.2GB，几分钟）
bash deploy/prepare_models.sh

# 验证缓存结构（refs/main 无换行 + snapshots 目录）
ls ~/.cache/huggingface/hub/
```

> 为什么必须这步：容器内无法从 huggingface.co 下载（被墙），
> hf-mirror 又拦截 python 客户端。用 curl 提前下好、挂载进容器、离线加载。

### Step 4 构建并启动

```bash
# 后台构建+启动全部服务（首次构建较慢，5~15 分钟）
docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml up -d --build

# 查看容器状态（全 Up 即可）
docker compose ps

# 看启动日志，确认模型加载成功
docker compose logs backend | tail -20
```

**关键日志**：应看到 `Models loaded in Xs, application ready`。
若报 `We couldn't connect to huggingface.co`，说明模型缓存没挂载对，回 Step 3。

### Step 5 首次使用（建库 + 迁移 + 导入示例知识库）

```bash
# 数据库迁移
docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml exec backend alembic upgrade head

# 导入 22 篇评测知识库（3 个知识库），体验完整功能
docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml exec backend python scripts/import_kb.py --base http://localhost:8000
```

### Step 6 验证

浏览器打开 **http://你的服务器IP** 应看到前端。测试：
- 问「什么是缓存雪崩？」→ 流式回答 + 来源引用
- 上传一个 PDF/TXT → 状态变 completed
- 提问「Linux 内核中断机制」→ 应回复"没有找到相关文档"（正确拒答）

---

## 三、常用运维命令

```bash
# 查看状态 / 日志
docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml ps
docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml logs -f backend

# 更新代码后重新部署
git pull && docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml up -d --build

# 停止（保留数据）
docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml stop

# 完全清理（含数据库/向量数据）
docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml down -v
```

---

## 四、常见问题

| 现象 | 原因 / 解决 |
|------|------------|
| `Models loaded` 前崩溃，报连不上 huggingface.co | 模型缓存没挂载进容器 → 重跑 `prepare_models.sh`，确认 `docker-compose.deploy.yml` 用了 `-f` |
| 上传文档一直 pending | Celery 容器没起或挂了 → `docker compose ps` 看 celery |
| 提问报 500 / 数据库错误 | 没跑迁移 → Step 5 的 `alembic upgrade head` |
| 构建很慢 | 大陆镜像源：确认 `setup_server.sh` 的 daemon.json 生效（`docker info` 看 registry-mirrors）|
| 镜像构建 pip 失败 | 确认用的是 `--build-arg PIP_INDEX_URL` 默认阿里云源，或换 `https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple` |
| 想换端口 | 前端端口改 compose 里 `frontend` 的 `"3000:80"` 左侧；需同时改安全组 |

---

## 附录：加访问口令（推荐）

给 nginx 加一层 Basic Auth，防陌生人白嫖 API Key。**最直接的做法是改前端 `nginx.conf` 加认证，然后重新构建前端容器**（本地 `npm run dev` 不受影响）：

**① 服务器上生成口令文件**（提示输两次密码）：

```bash
sudo apt-get install -y apache2-utils
sudo htpasswd -c /etc/nginx/rag.htpasswd demo    # 账号 demo，密码自定
```

**② 修改 `frontend/nginx.conf`**，加两行：

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        auth_basic "RAG Demo";                    # ← 新增
        auth_basic_user_file /etc/nginx/rag.htpasswd;   # ← 新增
    }
    ...
}
```

**③ 挂载口令文件并重新构建**（改 `deploy/docker-compose.deploy.yml` 追加）：

```yaml
  frontend:
    volumes:
      - /etc/nginx/rag.htpasswd:/etc/nginx/rag.htpasswd:ro
```

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml up -d --build frontend
```

之后访问 http://你的IP 会先要求输入 `demo` 和密码。这是最简单可靠的一层防护。
