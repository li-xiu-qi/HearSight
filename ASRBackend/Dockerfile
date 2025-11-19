# 使用 Python 官方镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 配置 apt 使用清华源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 使用清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制 requirements.txt
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 如果 .env 不存在，复制 .env.example 为 .env
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# 创建数据目录
RUN mkdir -p datas/audios datas/results

# 暴露端口
EXPOSE 8003

# 启动应用
CMD ["python", "main.py"]
