#!/bin/bash
# HearSight 本地模式启动脚本（dgx-spark / 任意 Linux + NVIDIA 机器）
# 前置：三个 AI 服务已在跑（ASR 8003 / llama-server 8080 / embedding 8004），
#       ffmpeg 与 yt-dlp 已按 README 装进用户态环境。
#
# 用法：bash scripts/start-local.sh [端口，默认 9187]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-9187}"

cd "$ROOT/next-app"

if [ ! -d node_modules ]; then
  echo "==> 安装依赖"
  npm install --include=dev
fi

if [ ! -d .next ]; then
  echo "==> 构建"
  npm run build
fi

echo "==> 启动 next start :$PORT"
exec npx next start --port "$PORT"
