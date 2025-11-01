# 📖 项目介绍

![HearSight logo](https://oss-liuchengtu.hudunsoft.com/userimg/33/3374fce0ebc0d82f093c6c7361b84fcc.png)

HearSight 是一个智能视频内容分析与理解平台，能够自动识别视频中的语音内容，将其转换为文本，并提供智能分句、内容总结和智能问答功能，帮助用户快速理解和分析视频内容。🎯

项目地址：<https://github.com/li-xiu-qi/HearSight>

## ✨ 主要特性

![主要特性](https://oss-liuchengtu.hudunsoft.com/userimg/eb/eb8ce69e51ffee1798ab4419f391adab.png)

- 📹 从哔哩哔哩导入视频并自动下载与管理媒体文件
- 📢 支持本地上传视频和音频文件，支持格式包括 MP4、AVI、MOV、MKV、MP3、WAV、M4A、AAC 等
- 🚀 自动将音频转文字并按时间戳生成可跳转的段落，支持精确定位与播放同步
- 📝 基于大语言模型生成段落级与视频级的摘要总结，便于快速获取要点
- 💬 与视频内容进行智能对话交互，支持基于上下文的问答
- 🖼️ 图文展示模式：支持添加重要的图片内容到回答里面，进行图文展示
<!-- 效果展示 -->
## 🔧 效果展示

视频播放页展示：
![视频播放页展示](https://oss-liuchengtu.hudunsoft.com/userimg/27/27e3d807bc8e6a3abf5739eeb5effb27.png)

打开一个视频：

![打开一个视频](https://oss-liuchengtu.hudunsoft.com/userimg/8d/8daf5b438a9de50fd4425ee1518536a9.png)

打开视频后的文稿效果展示：

![打开视频后的文稿效果展示](https://oss-liuchengtu.hudunsoft.com/userimg/f5/f548ca996e1b001e371df9bca74fc60a.png)

视频总结的展示：

![视频总结的展示](https://oss-liuchengtu.hudunsoft.com/userimg/de/defdd1d7dd03e7b34f34232895455dd9.png)
![视频总结的放大图片展示](https://oss-liuchengtu.hudunsoft.com/userimg/0f/0f4df03f82e2250bc3c6f77d87514f8c.png)

与视频之间的智能对话：

![与视频之间的智能对话](https://oss-liuchengtu.hudunsoft.com/userimg/73/73c98a266a46f1b4524772227c89f23a.png)

![与视频之间的智能对话](https://oss-liuchengtu.hudunsoft.com/userimg/4b/4bd189e43bc033aa1b3e3abc14f9bac6.png)


![图文模式对话图片放大展示](https://oss-liuchengtu.hudunsoft.com/userimg/45/45b084440a50e098229d8c827ab5f01f.png)

## 🛠 技术栈

后端采用 FastAPI 框架结合 PostgreSQL 数据库，前端采用 React 18 + TypeScript + Tailwind CSS，支持 Docker 一键部署。🚀

![架构图](https://oss-liuchengtu.hudunsoft.com/userimg/b5/b54f2ca20885a98aa90ec0557b8354e1.png)

## 🎯 适用场景

学习笔记、教学资料整理、视频内容检索、在线课程理解与快速复习。

## 🚀 快速开始

### 🔥 克隆项目

```bash
git clone https://github.com/li-xiu-qi/HearSight
cd HearSight
```

### ⚙️ 配置环境变量

在项目根目录创建 `.env` 文件，配置以下参数：

```bash
# PostgreSQL 数据库配置（生产环境请修改密码）
POSTGRES_USER=hearsight
POSTGRES_PASSWORD=hearsight_pass
POSTGRES_DB=hearsight
POSTGRES_PORT=5432

# 后端和前端端口（可选）
BACKEND_PORT=9999
FRONTEND_PORT=10000

# OpenAI / 大语言模型 API 配置（必填）
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_CHAT_MODEL=deepseek-ai/DeepSeek-V3

# 会话上下文窗口大小（可选，默认 1000000）
CHAT_MAX_WINDOWS=1000000

# 哔哩哔哩 Cookie（可选，用于下载需要登录的视频）
BILIBILI_SESSDATA=
```

💡 **必填项**：仅需配置 `OPENAI_API_KEY`。我们默认使用硅基流动的 API，获取免费额度：<https://cloud.siliconflow.cn/i/FcjKykMn>，上面提供免费的大语言模型如 `THUDM/GLM-4-9B-0414`。

### 🐳 方案一：Docker 部署（推荐）

```bash
docker compose up -d --build
```

> 你也可以通过仅仅使用docker运行postgres数据库，单独启动后端和前端。

启动完成后，访问 <http://localhost:10000> 打开应用。

### 💻 方案二：本地运行
>
> postgres数据库必须要启动，你可以通过docker启动或者安装postgres数据库。
>
#### 📦 安装后端依赖

```bash
pip install -r requirements.txt
```

安装完依赖后，需要安装 PyTorch，请访问 <https://pytorch.org/get-started/locally/> 查询对应版本。

#### 🚀 启动后端服务

```bash
python main.py
```

后端服务默认运行在 `http://localhost:9999`。

#### 🎨 安装前端依赖

```bash
cd frontend
npm install
```

#### 🌟 启动前端开发服务器

```bash
npm run dev
```

前端默认在 <http://localhost:5173> 启动。

## 📡 API 文档

后端已集成 FastAPI 自动文档，启动后端后访问 <http://localhost:9999/docs> 查看完整 API 文档。

### 核心 API 端点

- `POST /api/download` - 下载视频文件
- `POST /api/jobs` - 创建处理任务
- `GET /api/jobs/{job_id}` - 获取任务状态
- `POST /api/asr/segments` - 语音转文字并生成句子片段
- `GET /api/transcripts` - 获取所有转录记录
- `GET /api/transcripts/{transcript_id}` - 获取转录详情
- `POST /api/summarize` - 生成内容摘要
- `POST /api/chat` - 与内容进行智能对话

## 📂 项目结构

```
HearSight/
├── backend/                    # 后端核心代码
│   ├── routers/               # API 路由
│   │   ├── asr_router.py      # 语音识别相关接口
│   │   ├── chat_router.py     # 对话与总结接口
│   │   ├── download_router.py # 视频下载接口
│   │   ├── job_router.py      # 任务管理接口
│   │   └── transcript_router.py # 转录管理接口
│   ├── services/              # 业务服务层
│   ├── db/                    # 数据库操作
│   ├── audio2text/            # 语音转文字模块
│   ├── text_process/          # 文本处理（总结、对话）
│   ├── cache/                 # 缓存管理
│   └── utils/                 # 工具函数
├── frontend/                  # 前端 React 应用
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── hooks/             # 自定义 React Hook
│   │   ├── services/          # API 调用服务
│   │   ├── types/             # TypeScript 类型定义
│   │   ├── HomePage/          # 首页
│   │   └── App.tsx            # 主应用界面
│   └── vite.config.ts         # Vite 配置
├── main.py                    # FastAPI 应用入口
├── config.py                  # 配置管理
├── docker-compose.yml         # Docker 编排文件
├── Dockerfile.backend         # 后端 Docker 镜像
└── requirements.txt           # Python 依赖
```

## 🔧 功能特性详解

### 1. 视频下载与管理

支持从哔哩哔哩直接下载视频，自动处理媒体文件的存储和管理。

### 2. 语音识别与分句

使用先进的语音识别模型将音频转换为文本，并自动分割为句子片段，每个片段都带有精确的时间戳。

### 3. 内容摘要与总结

基于大语言模型，自动生成视频的段落级摘要和全文总结，帮助用户快速抓住核心要点。

### 4. 智能问答

用户可以与视频内容进行交互式对话，提出问题并获得基于内容的精准答案。

## 🤝 贡献指南

我们欢迎所有贡献！如果您有改进建议或发现问题，请提交 PR 或在 Issues 中告诉我们。

## 📝 许可证

本项目采用  Apache-2.0 license 许可证，详见 LICENSE 文件。
