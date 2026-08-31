#!/bin/bash
# 一键安装 docker buildx 插件（含 Docker apt 源配置，失败自动降级为下载二进制）
# 用法：
#   已克隆仓库：bash deploy/install_buildx.sh
#   未克隆仓库：bash <(curl -fsSL https://raw.githubusercontent.com/zyq789-code/rag-system/master/deploy/install_buildx.sh)

echo "==> [0/4] 检查环境..."
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ 未检测到 docker，请先运行 deploy/setup_server.sh"
  exit 1
fi
. /etc/os-release 2>/dev/null
echo "    发行版: ${ID:-unknown} (${VERSION_CODENAME:-unknown})"

install_via_apt() {
  echo "==> [1/4] 配置 Docker apt 源（阿里云镜像）..."
  sudo install -m 0755 -d /etc/apt/keyrings || return 1
  sudo curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || return 1
  sudo chmod a+r /etc/apt/keyrings/docker.gpg || return 1
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu ${VERSION_CODENAME:-stable} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null || return 1

  echo "==> [2/4] apt-get update ..."
  sudo apt-get update || return 1

  echo "==> [3/4] 安装 docker-buildx-plugin + docker-compose-plugin ..."
  sudo apt-get install -y docker-buildx-plugin docker-compose-plugin || return 1
  return 0
}

install_binary() {
  echo "==> apt 方式不可用，改用手动下载 buildx 二进制..."
  # Compose 构建要求 buildx >= 0.17，默认取 0.17.1；可通过 BUILDX_VERSION 环境变量覆盖
  local ver="${BUILDX_VERSION:-v0.17.1}"
  local arch="amd64"
  [ "$(uname -m)" = "aarch64" ] && arch="arm64"
  sudo mkdir -p /usr/lib/docker/cli-plugins || return 1
  # 依次尝试镜像源 → 官方源
  local ok=0
  for url in \
    "https://ghfast.top/https://github.com/docker/buildx/releases/download/${ver}/buildx-${ver}.linux-${arch}" \
    "https://github.com/docker/buildx/releases/download/${ver}/buildx-${ver}.linux-${arch}"; do
    if sudo curl -fsSL "$url" -o /usr/lib/docker/cli-plugins/docker-buildx; then
      ok=1; break
    fi
  done
  [ "$ok" = "1" ] || return 1
  sudo chmod +x /usr/lib/docker/cli-plugins/docker-buildx
  return 0
}

echo "==> [4/4] 安装并验证 ..."
if [ "$ID" = "ubuntu" ] || [ "$ID" = "debian" ]; then
  if ! install_via_apt; then
    echo "⚠️ apt 安装失败，降级为二进制下载"
    install_binary || { echo "❌ 两种方式都失败，请手动排查"; exit 1; }
  fi
else
  install_binary || { echo "❌ 二进制下载失败，请手动排查"; exit 1; }
fi

if docker buildx version 2>&1; then
  echo "✅ buildx 安装成功！以后 docker compose --build 不再告警。"
else
  echo "❌ 已安装但 docker buildx 不可用，请检查 PATH"
  exit 1
fi
