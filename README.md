# 📖 项目介绍

![HearSight logo](https://oss-liuchengtu.hudunsoft.com/userimg/33/3374fce0ebc0d82f093c6c7361b84fcc.png)

HearSight 是一个企业级的视频内容智能分析工具。通过集成先进的语音识别、自然语言处理和大语言模型技术，HearSight 能够自动将视频音频转化为结构化的文本内容，并在此基础上进行多维度的智能分析和交互。无论您是进行学术研究、内容创作还是知识管理，HearSight 都能帮助您深度挖掘视频内容的价值。

**HearSight介绍视频**：<https://meeting.tencent.com/crm/Nbnzm4a52c>

项目地址：<https://github.com/li-xiu-qi/HearSight>

## ✨ 核心能力

![核心能力](https://oss-liuchengtu.hudunsoft.com/userimg/eb/eb8ce69e51ffee1798ab4419f391adab.png)

- 📹 集成式媒体导入：直接从哔哩哔哩获取内容，同时支持本地上传视频和音频，支持 MP4、AVI、MOV、MKV、MP3、WAV、M4A、AAC 等多种格式
- 🎯 精准语音转写：采用业界领先的 ASR 技术，支持热词识别和实时精确时间戳，自动分句并生成可交互式的文本档案
- � 智能内容分析：基于大语言模型生成段落级和全文级的结构化摘要，支持持久化保存和迭代优化
- 💬 对话式内容理解：支持基于原文的深度问答交互，准确把握关键信息和核心观点
- 🖼️ 多模态信息展示：在问答和总结中融入视频关键帧，实现图文融合的高效表达
- � 多语言内容转换：支持自动翻译为多种语言，翻译结果完整保存，便于国际化应用
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

## 🛠 技术架构

HearSight 采用现代化的微服务架构设计。后端基于 FastAPI 构建高性能 RESTful API，通过 PostgreSQL 实现数据的持久化和查询优化；前端采用 React 18 + TypeScript + Tailwind CSS 提供交互流畅的用户界面。整体支持 Docker 容器化部署，开箱即用。

![架构图](https://oss-liuchengtu.hudunsoft.com/userimg/b5/b54f2ca20885a98aa90ec0557b8354e1.png)

## 🎯 应用场景

HearSight 适用于需要大量处理视频/音频内容的各类场景。学术研究人员可以快速索引和整理讲座视频；教育工作者能够便捷生成教学素材；内容创作者可以自动化处理视频文案和脚本；企业知识管理团队则可以建立结构化的视频知识库。总之，只要涉及从非结构化视频内容中提取和分析信息的场景，HearSight 都能显著提升工作效率。

## 🚀 快速开始

### 🔥 获取源代码

```bash
git clone https://github.com/li-xiu-qi/HearSight
cd HearSight
```

### ⚙️ 环境配置

在项目根目录创建 `.env` 文件，配置必要的参数：

```bash
# PostgreSQL 数据库配置（生产环境建议修改密码）
POSTGRES_USER=hearsight
POSTGRES_PASSWORD=hearsight_pass
POSTGRES_DB=hearsight
POSTGRES_PORT=5432

# 应用服务端口（可选，生产环境建议配置）
BACKEND_PORT=9999
FRONTEND_PORT=10000

# 大语言模型配置（必填）
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_CHAT_MODEL=baidu/ERNIE-4.5-300B-A47B # 文心4.5多模态系列模型

# 会话上下文大小（可选，默认 1000000）
CHAT_MAX_WINDOWS=1000000

# 哔哩哔哩登录凭证（可选，用于访问需要登录的高清视频）
BILIBILI_SESSDATA=
```

💡 **快速提示**：仅需配置 `OPENAI_API_KEY` 即可启动。我们默认使用硅基流动的 OpenAI 兼容 API 服务。免费额度申请：<https://cloud.siliconflow.cn/i/FcjKykMn>，平台提供免费的大语言模型如 `THUDM/GLM-4-9B-0414`，此外硅基流动上也支持文心4.5多模态系列模型中的ERNIE-4.5-300B-A47B调用。你也可以去[千帆大模型平台-企业级一站式大模型开发及应用开发平台](https://cloud.baidu.com/product-s/qianfan_home)调用ERNIE-4.5-300B-A47B。

### 🐳 方案一：容器化部署（推荐）

一行命令启动完整服务栈：

```bash
docker compose up -d --build
```

部署完成后，访问 <http://localhost:10000> 即可进入应用。

> 如果仅需使用容器运行 PostgreSQL 数据库，而将后端和前端分别在本地启动，请参考下方本地部署方案。

### 💻 方案二：本地开发部署

#### 前置要求

PostgreSQL 数据库必须处于运行状态。可以选择通过 Docker 启动，也可以本地安装。

#### 后端服务启动

1. 安装 Python 依赖包

   ```bash
   pip install -r requirements.txt
   ```

2. 安装 PyTorch

   根据你的硬件选择对应版本，访问 <https://pytorch.org/get-started/locally/>

3. 启动后端服务

   ```bash
   python main.py
   ```

   后端服务默认运行在 `http://localhost:9999`。

#### 前端应用启动

1. 进入前端目录并安装依赖

   ```bash
   cd frontend
   npm install
   ```

2. 启动前端开发服务器

   ```bash
   npm run dev
   ```

前端默认在 <http://localhost:5173> 启动。

## 📡 API 参考

后端集成了 FastAPI 自动文档生成功能，启动后端服务后访问 <http://localhost:9999/docs> 可查看完整的交互式 API 文档。

### 核心接口概览

#### 媒体管理

- `POST /api/download` 启动视频下载任务
- `POST /api/upload` 上传本地媒体文件
- `GET /api/transcripts` 查看所有已处理的媒体列表
- `GET /api/transcripts/{transcript_id}` 获取指定媒体的详细信息及转写内容
- `DELETE /api/transcripts/{transcript_id}` 删除媒体记录及相关数据

#### 内容处理

- `POST /api/asr/segments` 执行语音识别并分句处理
- `POST /api/summarize` 生成内容摘要
- `POST /api/transcripts/{transcript_id}/summaries` 保存生成的摘要
- `GET /api/transcripts/{transcript_id}/summaries` 查看已保存的摘要历史
- `POST /api/transcripts/{transcript_id}/translate` 启动多语言翻译任务
- `GET /api/transcripts/{transcript_id}/translate-progress` 查询翻译进度
- `GET /api/transcripts/{transcript_id}/translations` 查看已保存的翻译结果

#### 交互分析

- `POST /api/chat` 基于内容进行问答交互

## 📂 项目架构

```text
HearSight/
├── backend/                    # 后端服务
│   ├── routers/               # API 路由层
│   │   ├── asr_router.py      # 语音识别相关接口
│   │   ├── chat_router.py     # 对话与总结接口
│   │   ├── download_router.py # 媒体下载接口
│   │   ├── transcript_router.py # 媒体管理接口
│   │   ├── upload_router.py   # 文件上传接口
│   │   └── ...                # 其他功能路由
│   ├── services/              # 业务服务层
│   │   ├── download_service.py    # 下载服务
│   │   ├── translate_service.py   # 翻译服务
│   │   └── ...                    # 其他服务
│   ├── db/                    # 数据库访问层
│   │   ├── pg_store.py        # PostgreSQL 数据操作
│   │   ├── transcript_crud.py  # 媒体数据 CRUD
│   │   └── ...
│   ├── audio2text/            # 语音识别模块
│   │   └── asr_sentence_segments.py # ASR 与分句处理
│   ├── text_process/          # 文本处理模块
│   │   ├── summarize.py       # 摘要生成
│   │   ├── chat_with_segment.py # 问答交互
│   │   └── ...
│   ├── cache/                 # 缓存管理
│   ├── utils/                 # 工具函数
│   └── app.py                 # FastAPI 应用工厂
│
├── frontend/                  # 前端应用（React 18 + TypeScript）
│   ├── src/
│   │   ├── components/        # React 组件库
│   │   │   ├── RightPanel/    # 右侧功能面板
│   │   │   ├── VideoPlayer/   # 视频播放器
│   │   │   └── ...
│   │   ├── features/app/      # 应用主体功能
│   │   ├── services/          # API 服务层
│   │   ├── types/             # TypeScript 类型定义
│   │   ├── hooks/             # 自定义 React hooks
│   │   ├── HomePage/          # 首页
│   │   └── App.tsx            # 应用入口
│   ├── vite.config.ts         # Vite 构建配置
│   └── tailwind.config.js     # Tailwind CSS 配置
│
├── main.py                    # 后端启动入口
├── config.py                  # 配置管理
├── docker-compose.yml         # 容器编排配置
├── Dockerfile.backend         # 后端镜像配置
├── requirements.txt           # Python 依赖
└── README.md                  # 项目说明
```

## 🔧 功能详解

### 1. 多源媒体导入

支持从哔哩哔哩直接导入视频（包含登录视频），同时接受本地上传的各种格式媒体。系统自动管理文件存储和元数据，无需手动处理。

### 2. 精准语音识别与智能分句

采用先进的语音识别模型将音频转化为文本，支持热词识别以提高垂直领域准确度。系统自动按语义进行分句处理，每个句子片段都关联精确的时间戳，支持点击跳转到视频对应位置。

### 3. 结构化内容摘要

基于大语言模型为内容生成多层次的摘要。支持段落级摘要快速获取关键信息，以及全文级总结把握内容全貌。摘要结果完整保存到数据库，支持查看历史版本，支持重新生成并自动覆盖。

**核心特性**：

- ✅ 摘要自动存储，便于追踪演变
- ✅ 支持强制重新生成，自动覆盖旧数据
- ✅ 前端展示"已保存"标记
- ✅ 可随时查看以往的摘要版本

### 4. 多语言内容转换

支持自动将内容翻译为多种目标语言。翻译过程在后台异步进行，支持实时进度查看。翻译结果完整持久化，便于多语言内容管理和复用。

**核心特性**：

- ✅ 翻译结果完整保存，支持多语言同时存储
- ✅ 支持强制重新翻译，自动更新数据库
- ✅ 前端展示已保存的语言种类
- ✅ 可随时查阅历史翻译内容

### 5. 交互式问答分析

用户可以针对视频内容提出自由形式的问题，系统基于原始转写内容进行深度分析并给出精准答案。支持追问和多轮对话，完整保留对话历史。

### 6. 图文融合展示

在摘要和问答中自动关联视频关键帧，实现图文结合的高效表达。支持点击查看大图，帮助用户更直观地理解内容。

## 🤝 参与贡献

HearSight 是一个开源项目，我们欢迎来自社区的改进和贡献。无论是功能增强、bug 修复还是文档改进，都可以通过提交 Pull Request 的方式参与。如果有好的想法或发现问题，也可以直接提交 Issue。

## 📝 开源许可

本项目采用 Apache-2.0 License 开源许可证。详见 LICENSE 文件。
