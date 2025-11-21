FROM ubuntu:22.04

# 环境变量与镜像运行行为
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # 默认使用阿里云 PyPI 镜像加速大部分包安装
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple \
    PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /app

# 安装系统依赖（包含音频处理所需的 ffmpeg/libsndfile）
# 使用清华镜像源加速 apt 下载（替换常见 Ubuntu/Debian 源），并在网络错误时重试
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|https://mirrors.tuna.tsinghua.edu.cn/ubuntu/|g' /etc/apt/sources.list \
     || true \
     && sed -i 's|http://security.ubuntu.com/ubuntu/|https://mirrors.tuna.tsinghua.edu.cn/ubuntu/|g' /etc/apt/sources.list \
     || true \
     && sed -i 's|http://deb.debian.org/debian/|https://mirrors.tuna.tsinghua.edu.cn/debian/|g' /etc/apt/sources.list \
     || true \
     && apt-get -o Acquire::Retries=3 update || apt-get -o Acquire::Retries=3 update --fix-missing \
     && apt-get -o Acquire::Retries=3 install -y --no-install-recommends ca-certificates apt-transport-https \
         python3 python3-pip python3-venv build-essential git curl ffmpeg libsndfile1 \
     || apt-get install -y --no-install-recommends --fix-missing ca-certificates apt-transport-https \
         python3 python3-pip python3-venv build-essential git curl ffmpeg libsndfile1 \
     && ln -s /usr/bin/python3 /usr/bin/python || true \
     && rm -rf /var/lib/apt/lists/*

# 复制 requirements 并安装依赖
COPY backend/requirements.txt /app/requirements.txt

RUN python3 -m pip install --upgrade pip \
     && python3 -m pip install -r /app/requirements.txt

# 复制源码
COPY . /app

# 确保持久化目录存在
RUN mkdir -p /app/app_datas/download_videos \
    /app/app_datas/model_cache \
    /app/app_datas/torch_cache \
    /app/app_datas/transformers_cache \
    /app/app_datas/xdg_cache

EXPOSE 8000

# 启动时使用运行时的 PORT 环境变量（默认 8000）
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
