#!/bin/bash
# 大陆 ECS 初始化：安装 Docker + Docker Compose 插件，配置镜像加速
# 适用：Ubuntu / Debian（阿里云、腾讯云等常见 ECS）
# 用法：sudo bash deploy/setup_server.sh
set -e

echo "==> [1/4] 安装 Docker（阿里云镜像源）..."
# 官方脚本带 Aliyun 镜像参数；若 get.docker.com 访问慢，可改用阿里云安装脚本：
#   curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

echo "==> [2/4] 安装 Docker Compose 插件..."
apt-get update -y
apt-get install -y docker-compose-plugin || apt-get install -y docker-compose-v2

echo "==> [3/4] 配置 Docker 镜像加速（拉取 postgres/redis/chroma/python 等镜像更快）..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run",
    "https://dockerproxy.net"
  ]
}
EOF

echo "==> [4/4] 启动 Docker 并开机自启..."
systemctl enable --now docker
sleep 2

echo ""
echo "✅ Docker 安装完成，验证："
docker --version
docker compose version
