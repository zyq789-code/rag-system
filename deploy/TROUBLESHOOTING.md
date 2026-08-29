# 部署排坑实录（大陆 ECS · Docker Compose）

本文件记录将 RAG 知识库系统部署到大陆阿里云 ECS 过程中**真实遇到并解决**的问题。
每条都含：现象 → 根因 → 修复 → 预防。对排查线上问题有直接参考价值。

---

## 1. Docker Hub 连接超时（i/o timeout）

**现象**
```bash
docker compose up -d --build
Error response from daemon: failed to resolve reference "docker.io/library/postgres:16-alpine":
  dial tcp 59.188.250.54:443: i/o timeout
```

**根因**：大陆服务器无法直连 Docker Hub（`registry-1.docker.io` 被墙/超时）。

**修复**：配置大陆可用的 Docker 镜像加速源：
```json
{ "registry-mirrors": ["https://docker.1panel.live", "https://docker.m.daocloud.io", "https://docker.1ms.run"] }
```
（由 `deploy/setup_server.sh` 自动配置）

**预防**：新服务器先跑 `setup_server.sh`；`docker info | grep -A5 "Registry Mirrors"` 确认加速生效。

---

## 2. 阿里云容器镜像加速器返回 404

**现象**
```bash
docker pull redis:7-alpine
docker.io/library/redis:7-alpine: not found
# 直接问加速器：
curl -I https://你的xxx.mirror.aliyuncs.com/v2/library/redis/manifests/7-alpine
HTTP/2 404
```

**根因**：阿里云 ACR 个人版镜像加速器**并不能代理所有 Docker Hub 镜像**，对未缓存镜像返回 404。
而 Docker 把 404 当权威结果，不会回落到其他源 → 拉取失败。

**修复**：弃用阿里云加速器，改用能真正代理 Docker Hub 的源（`docker.1panel.live` 等）。
**关键**：换源前先用 curl 直接验证某个镜像清单是否存在（200 才用），避免白折腾。

**预防**：daemon.json 配多路源；选源前先 `curl -I <镜像源>/v2/library/redis/manifests/7-alpine` 测一下。

---

## 3. 改了 daemon.json 但加速不生效

**现象**
```bash
# daemon.json 已写好，但 docker info 显示 Registry Mirrors 为空
docker info | grep -A5 "Registry Mirrors"
（无输出）
```

**根因**：`/etc/docker/daemon.json` 在 docker 守护进程**已运行之后**修改，不重启不会加载。
（`systemctl enable --now docker` 对已运行的 docker 不会触发重载。）

**修复**：改完 daemon.json 必须 `sudo systemctl restart docker`，再用 `docker info` 验证。

**预防**：`setup_server.sh` 已修正为「先写 daemon.json → 再 `systemctl restart docker`」。

---

## 4. 前端生产构建 TypeScript 报错（本地 dev 不报，构建才报）

**现象**
```bash
bun run build  # 即 vue-tsc && vite build
src/composables/useStreaming.ts(12,5): error TS1016: A required parameter cannot follow an optional parameter.
src/main.ts(4,17): error TS2307: Cannot find module './App.vue'
src/components/resume/AnalysisView.vue(31,17): error TS7053: ...
```

**根因**：三个问题叠加：
- **TS1016**：`useStreaming.ts` 的 `sendMessage` 把可选参数（`conversationId?`/`kbId?`）排在必选回调前；
- **TS2307**：项目**缺少 `env.d.ts`**，vue-tsc 无法解析 `.vue` 导入；
- **TS7053**：`AnalysisView.vue` 用 `any` 类型索引对象字面量。

本地 `npm run dev` 走 Vite 不跑类型检查，所以一直没暴露；只有生产构建（Docker 里 `bun run build`）才会触发。

**修复**：可选参数移到末尾并同步调用方；新增 `frontend/src/env.d.ts` 声明 `*.vue` 模块；对象索引加类型断言。

**预防**：任何改动后跑一次 `npm run build` 验证；CI 里加 `vue-tsc` 检查。

---

## 5. backend 容器 Exited(137) —— 内存不足 OOM

**现象**
```bash
docker compose ps
rag-system-backend-1  Exited (137)
# 日志为空（被杀前没来得及打印）
```

**根因**：退出码 137 = SIGKILL，被系统 OOM killer 杀掉。
2核2G 实例上，**重排模型（bce-reranker-base_v1，约 1.1GB）+ Embedding（~90MB）+ Postgres + ChromaDB + Celery + nginx** 总内存需求超过 2GB。

**修复**：升级到 2核4G；临时应急可加 swap：
```bash
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**预防**：评估内存需求再选实例规格；重排/向量模型是内存大头，4G 起步。

---

## 6. chromadb 客户端/服务端版本不匹配 —— KeyError '_type'

**现象**
```bash
# 上传文档返回 500，backend 日志：
File "chromadb/api/configuration.py", line 209, in from_json
    f"Trying to instantiate configuration ... {json_map['_type']}"
KeyError: '_type'
```

**根因**：Python 客户端锁 `chromadb==0.6.3`，但 docker-compose 里服务端用了 `chromadb/chroma:latest`。
新版服务端返回的集合配置格式，旧客户端解析不了（缺 `_type` 键）→ 创建集合报错。

**修复**：服务端固定为与客户端匹配的版本：
```yaml
image: chromadb/chroma:0.6.3
```

**预防**：客户端与服务端版本必须一致；用 `latest` 前先核对兼容矩阵。

---

## 7. git clone 报 RPC failed / HTTP2 framing error

**现象**
```bash
git clone https://github.com/.../rag-system.git
error: RPC failed; curl 16 Error in the HTTP2 framing layer
```

**根因**：大陆连 GitHub 的 HTTP/2 连接被重置（GFW 干扰/网络不稳定）。

**修复**
```bash
git config --global http.version HTTP/1.1
git config --global http.postBuffer 524288000
# 仍失败可走镜像：git clone https://ghfast.top/https://github.com/...
```

---

## 8. 长命令被终端换行截断

**现象**
```bash
docker compose -f docker-compose.yml -f
flag needs an argument: 'f' in -f
```

**根因**：带两个 `-f` 的长命令在复制/换行时被截断，`-f` 后面没了参数。

**修复**：定义简短别名，避免反复敲长命令：
```bash
echo 'alias dc="docker compose -f docker-compose.yml -f deploy/docker-compose.deploy.yml"' >> ~/.bashrc
source ~/.bashrc
dc up -d --build
```

---

## 总结

| 类别 | 问题 | 一句话经验 |
|------|------|-----------|
| 网络 | Docker Hub 超时 / 加速器 404 / git RPC | 大陆部署先验证镜像源与网络，别直接信默认配置 |
| 构建 | 前端 TS 报错（dev 不报构建报） | 类型检查只在生产构建暴露 → 必须跑一次 build 验证 |
| 资源 | backend OOM(137) | 模型是内存大头，先算内存需求再选实例 |
| 版本 | chromadb 客户端/服务端不匹配 | 客户端与服务端版本锁一致，别用 latest |
| 运维 | 改配置不重启 / 长命令截断 | 配置生效要重启；用别名缩短命令 |
