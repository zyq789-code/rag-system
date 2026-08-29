#!/bin/bash
# 大陆 ECS：用 curl 从 hf-mirror.com 预下载 Embedding 与重排模型到 HF 缓存目录。
# 说明：huggingface.co 被墙、hf-mirror 对 python 客户端做 TLS 指纹拦截，但 curl 可用；
#       模型缓存好后，容器内以 HF_HUB_OFFLINE=1 离线加载（见 docker-compose.deploy.yml）。
# 用法：bash deploy/prepare_models.sh   （生成 ~/.cache/huggingface/hub/）
set -e

HF_CACHE_DIR="${HF_CACHE_DIR:-$HOME/.cache/huggingface/hub}"
MIRROR="https://hf-mirror.com"
mkdir -p "$HF_CACHE_DIR"

# 模型清单：(缓存目录名 sha 镜像repo 文件列表...)
# 用 printf 写 refs/main（无换行！echo 会带 \n 导致 huggingface 找不到快照）
download_model() {
  local cache_name="$1" sha="$2" repo="$3"; shift 3
  local dir="$HF_CACHE_DIR/models--$cache_name"
  local snap="$dir/snapshots/$sha"
  mkdir -p "$snap" "$dir/refs"
  printf '%s' "$sha" > "$dir/refs/main"
  echo "==> $repo ($sha)"
  for f in "$@"; do
    # 处理子目录（如 1_Pooling/config.json）
    local target="$snap/$f"
    mkdir -p "$(dirname "$target")"
    if [ -f "$target" ] && [ -s "$target" ]; then
      echo "  已存在，跳过 $f"
    else
      echo "  下载 $f ..."
      curl -fL -o "$target" -m 600 "$MIRROR/$repo/resolve/main/$f" || { echo "  下载失败: $f"; exit 1; }
    fi
  done
  echo "  ✅ 完成 $(du -sh "$snap" | cut -f1)"
}

# Embedding：BAAI/bge-small-zh-v1.5（91MB safetensors）
download_model \
  "BAAI--bge-small-zh-v1.5" \
  "7999e1d3359715c523056ef9478215996d62a620" \
  "BAAI/bge-small-zh-v1.5" \
  config.json config_sentence_transformers.json sentence_bert_config.json \
  modules.json special_tokens_map.json tokenizer.json tokenizer_config.json vocab.txt \
  "1_Pooling/config.json" model.safetensors

# 重排：maidalun1020/bce-reranker-base_v1（约 1.1GB，XLM-R base）
download_model \
  "maidalun1020--bce-reranker-base_v1" \
  "eb7650fca1d81e2856fbd0d522488844aa502735" \
  "maidalun1020/bce-reranker-base_v1" \
  config.json sentencepiece.bpe.model special_tokens_map.json \
  tokenizer.json tokenizer_config.json pytorch_model.bin

echo ""
echo "✅ 模型预下载完成：$HF_CACHE_DIR"
du -sh "$HF_CACHE_DIR"
