## 📖 项目介绍

![HearSight logo](https://oss-liuchengtu.hudunsoft.com/userimg/33/3374fce0ebc0d82f093c6c7361b84fcc.png)

HearSight 是一个基于 AI 的视频辅助阅读工具，目标是让视频内容的获取、定位与理解变得更简单。🎯

### ✨ 主要特性

- 📹 从哔哩哔哩导入视频并自动下载与管理媒体文件
- 🔊 自动将音频转文字并按时间戳生成可跳转的段落（支持精确定位与播放同步）
- 🧠 基于大语言模型生成段落级与视频级的摘要/总结，便于快速获取要点

### 🛠 技术栈

FastAPI + PostgreSQL（后端）、React + Ant Design（前端），支持使用 Docker 一键部署。🚀

### 🎯 适用场景

学习笔记、教学资料整理、视频内容检索与快速复习。

## 📸 效果展示

![](https://oss-liuchengtu.hudunsoft.com/userimg/b4/b425ba2061f11b8a16a063c39824151e.png)
![](https://oss-liuchengtu.hudunsoft.com/userimg/21/217272740919c8740e84c970699e50b3.png)

## 🚀 快速开始

### ⚙️ 配置环境变量

```bash
# Local environment variables (do NOT commit this file)
# MinIO - change these in production
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
# Postgres - change this password for production
POSTGRES_USER=hearsight
POSTGRES_PASSWORD=hearsight_pass
POSTGRES_DB=hearsight
POSTGRES_PORT=5432
# Backend / Frontend ports (optional)
BACKEND_PORT=9999
FRONTEND_PORT=10000
# OpenAI / Chat Server
# Set OPENAI_API_KEY in your local .env or export in your shell
OPENAI_API_KEY= # 必须要配置
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_CHAT_MODEL=deepseek-ai/DeepSeek-V3 # THUDM/GLM-4-9B-0414
CHAT_MAX_WINDOWS=1000000
# Bilibili
BILIBILI_SESSDATA= # 可以不配置，也可以配置，可以去哔哩哔哩官网获取。
```

💡 除了必须要配置的部分，其他的可以不配置，所以只有 `OPENAI_API_KEY` 是需要配置的。默认使用硅基流动 API，但你可以换成其他厂商。硅基流动地址：<https://cloud.siliconflow.cn/i/FcjKykMn>，上面有免费的大语言模型，比如 `THUDM/GLM-4-9B-0414` 就是免费的。

### 🐳 方案一：使用 Docker（推荐，免去依赖安装问题）

```bash
docker compose -d --build
```

🌐 使用 Docker 启动项目后，访问 <http://localhost:10000>

### 💻 方案二：本地运行

#### 📦 安装后端依赖

```
pip install -r requirements.txt
```

🔧 安装完依赖后，需要安装 Pytorch，请访问 <https://pytorch.org/get-started/locally/> 查询对应版本并进行安装。

#### 🚀 启动后端

```
python main.py
```

⚠️ 如果遇到问题，欢迎联系我。

#### 🎨 安装前端依赖

```bash
cd frontend
npm install .
```

#### 🌟 启动前端

```
npm run dev
```

🌐 使用手动启动方式，前端默认在 5173 端口启动，访问 <http://localhost:5173>
