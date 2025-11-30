# HearSight项目教程——多模态音频内容分析

一、项目背景

在数字化时代，音视频内容已成为信息传播的主流媒介，但与文本相比，音视频的可检索性、可复用性和可分析性较差，给内容工作者和企业带来诸多难题：

- 发现成本高：大量视频/音频沉淀在平台或私有存储中，难以高效检索到关键信息；
- 跨语言理解门槛：多语言音视频内容难以统一检索与分析；
- 信息提取耗时：人工听写与梳理成本高且效率低；
- 多资源融合难度：在多段视频/音频中做知识聚合与跨文档检索存在上下文混淆问题；
- 对话与长期记忆：多轮问答中上下文长度限制降低了对话效果与用户体验。

HearSight 的使命是把音视频“可听”的信息变成“可搜索、可总结、可对话、可复用”的结构化知识库，帮助个人与企业把媒体内容转化为可管理、可复用的知识资产。我们通过模块化微服务架构、可替换的 ASR/LLM 提供商、以及向量化检索与 ReAct 记忆管理等策略，做到在保证性能与扩展性的同时，降低集成成本和运维门槛。

为什么要做？核心动因与价值：

- 提高效率：自动转写与智能摘要把人工耗时的听写与整理工作大幅缩短；
- 快速发现与检索：基于语义向量搜索的知识库支持多视频、跨语言检索和上下文重组；
- 支持多场景：从学术讲座、企业培训到客户通话分析，统一成可检索的知识资产；
- 使 LLM 更可控：通过结构化检索（Chroma/向量数据库）和记忆管理，显著提升问答的准确性与可审计性；
- 降低门槛：支持云端与本地 ASR，支持在 ARM 设备/低成本环境下部署，便于私有化部署和行业落地。

目标用户与适用场景：

- 内容创作者与媒体机构：自动生成文稿、摘要与短视频素材；
- 教育与科研：快速索引讲座与访谈，生成教学资料与研究笔记；
- 企业与运营：构建内部知识库、培训资料和合规审计记录；
- 客服与法务：自动分析录音发现关键信息、证据保全与合规检查；
- 市场与竞品研究：批量化处理视频数据并自动生成要点。

实现方式要点（技术亮点）：

- 模块化微服务架构：FastAPI 后端 + React 前端 + 可选 ASR 服务（本地 FunASR 或云 DashScope），支持 Docker 一键部署；
- 向量化检索：使用 Chroma 作为向量数据库，将句子段以 chunk 为单位 embedding，支持跨文档检索与多视频聚合；
- 文件名增强 Embedding：在向量化时把文件名与文本拼接，显著提升基于标题/文件名的检索召回率；
- ReAct 记忆管理：对话层使用压缩/重组策略保留关键上下文，兼顾多轮对话连贯性与模型上下文窗口限制；
- 多模态输出：在问答与摘要中自动关联视频关键帧，使文本和视觉信息同时支持检索与展示；
- 可替换 LLM/Embedding 提供商：可切换到 SiliconFlow、Baidu AI Studio 或其他 OpenAI 兼容提供商，支持流式 API 与本地模型；
- 异步任务与可扩展队列：使用 Celery + Redis 管理转写、翻译与摘要任务，支持大规模并发处理；
- 数据持久化：PostgreSQL、Supabase 存储文件元数据、摘要与多语言翻译记录，保证可追溯与版本管理。

接下来我们将在文档与代码注释里逐步解释这些产品化与工程实现的细节，并在示例中展示如何在真实场景中应用 HearSight 的能力。

---

## 目录

1. [项目介绍](#intro)
   - [项目概述](#intro)
   - [技术架构](#tech-architecture)
   - [核心能力](#core-capabilities)
   - [核心技术策略](#core-strategy)
   - [效果展示](#showcase)

2. [功能详解](#feature-media-import)
   - [多源媒体导入](#feature-media-import)
   - [精准语音识别与时间戳分句](#feature-precision-asr)
   - [分层级摘要生成与版本管理](#feature-content-analysis)
   - [多语言翻译与存储](#feature-multilingual)
   - [深度问答交互](#feature-qa)
   - [图文融合呈现](#feature-multimodal)

3. [适用场景](#scenarios)

4. [项目结构](#project-structure)
   - [项目结构详细说明](#project-structure)

5. [API 文档](docs/api_文档导航.md)

6. [快速开始](#quick-start)
   - [获取源代码（项目）](#get-source)

7. [ASR Backend](#asr-backend)
   - [云端模式启动（推荐）](#asr-cloud)
   - [本地模式启动](#asr-local)
   - [Docker 启动](#asr-docker)
   - [基本使用](#asr-basic)
   - [配置指南](#asr-config)

8. [主后端服务](#backend)
   - [环境配置](#backend-env)
   - [容器化部署（后端）](#backend-container)
   - [本地部署（后端）](#backend-local)
   - [验证服务（后端）](#backend-verify)

9. [前端应用](#frontend)
   - [环境准备（前端）](#frontend-prepare)
   - [环境配置（前端）](#frontend-config)
   - [安装依赖（前端）](#frontend-install)
   - [容器化部署（前端）](#frontend-container)
   - [本地开发（前端）](#frontend-local)

10. [Radxa设备部署（LLM）](#radxa)

- [Llama.cpp](#radxa-llama)
- [Ollama](#radxa-ollama)

11. [ARM设备Docker构建](#arm-docker)

- [构建流程](#arm-build-flow)
- [直接构建（推荐）](#arm-direct-build)
- [交叉构建（备选）](#arm-cross-build)

12. [总结](#summary)

<a id="intro"></a>

## 项目介绍

<a id="tech-architecture"></a>

### 技术架构

HearSight 采用现代化的微服务架构设计。后端基于 FastAPI 构建高性能 RESTful API，通过 PostgreSQL 实现数据的持久化和查询优化，通过 Celery 构建任务队列处理异步任务；前端采用 React 18 + TypeScript + Tailwind CSS 提供交互流畅的用户界面。整体支持 Docker 容器化部署，开箱即用。

![架构图](https://oss-liuchengtu.hudunsoft.com/userimg/b5/b54f2ca20885a98aa90ec0557b8354e1.png)

![微服务技术架构概览](https://oss-liuchengtu.hudunsoft.com/userimg/c8/c8ae4f200c345d26e5ec0d4fe3bc169b.png)

<a id="core-capabilities"></a>

### 核心能力

- 📹 集成式媒体导入：直接从哔哩哔哩获取内容，同时支持本地上传视频和音频文件，支持 MP4、AVI、MOV、MKV、MP3、WAV、M4A、AAC 等多种格式
- 🎯 精准语音转写：采用业界领先的 ASR 技术，支持热词识别和实时精确时间戳，自动分句并生成可交互式的文本档案
- 🧠 智能内容分析：基于大语言模型生成段落级和全文级的结构化摘要，支持持久化保存和迭代优化
- 💬 对话式内容理解：支持基于原文的深度问答交互，准确把握关键信息和核心观点
- 🖼️ 多模态信息展示：在问答和总结中融入视频关键帧，实现图文融合的高效表达（仅适用于视频内容）
- 🌐 多语言内容转换：支持自动翻译为多种语言，翻译结果完整保存，便于国际化场景使用

<a id="showcase"></a>

### 效果展示

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

![图文模式对话图片放大展示](https://oss-liuchengtu.hudunsoft.com/userimg/45/45b084440a50e098229d8c827ab5f01f.png)

<a id="core-strategy"></a>

### 核心技术策略

#### Embedding 文件名增强策略

在知识库检索环节，我们实现了 embedding 文件名增强技术。通过在生成文本向量时，将文件名信息与内容文本相结合，形成更丰富的上下文嵌入。具体实现是在 chunk_text 前添加文件名描述，如 "文件名：[filename]\n内容：[text]"，从而提升基于文件名提问的检索准确性。该策略有效解决了传统 embedding 仅基于内容而忽略文件名导致的检索不准问题，显著改善了用户查询体验，因为用户基于文件标题提问，很容易错漏相关文件，而给文件名一起进行embedding，会使得整个的效率，召回率平均能提升30%以上。

![文件名增强embedding](https://oss-liuchengtu.hudunsoft.com/userimg/04/04e4675db680c35a70dd6ead54b5a6ce.png)

#### ReAct 记忆管理策略

在对话问答系统中，我们采用了先进的 ReAct 记忆管理机制，以应对大语言模型的上下文长度限制。通过智能的记忆压缩和上下文重组，当对话积累的消息超过阈值时，系统自动生成对话摘要，将关键信息压缩存储，同时保留完整的消息历史用于精确重组。这种增量总结策略确保了多轮对话的连贯性，避免了信息丢失，同时控制了上下文长度，提升了问答系统的稳定性和效率。记忆管理分为对话记忆和任务执行记忆两层，前者维持用户与助手的对话连贯性，后者管理单次任务的推理过程，确保了系统的可扩展性和性能优化。

![ReAct双层记忆管理机制](https://oss-liuchengtu.hudunsoft.com/userimg/ff/fff9b992a690c7030ddf99bee7f57174.png)

![ReAct后端问答设计](https://oss-liuchengtu.hudunsoft.com/userimg/a3/a327b36d0ddb4fcaa99a27a4f4cfff42.png)

#### 检索内容重组策略

在多视频问答场景中，我们设计了层次化的检索内容重组结构，以确保不同视频和内容块有清晰的分界线。该结构采用嵌套标签系统：[视频开始/结束] 包围整个视频内容，[块开始/结束] 分隔连续的内容片段，每个句子附带精确的时间戳 [filename start-end]。这种设计避免了多视频内容混淆的问题，使大语言模型能够准确识别和引用特定视频段落，提升问答的精确性和可追溯性，同时保持提示词的结构化和可读性。

![检索内容重组策略](https://oss-liuchengtu.hudunsoft.com/userimg/9c/9c5fa9824b2395d8563890d05a7e73ac.png)

<a id="quick-start"></a>

## 功能详解

![功能结构说明图](https://oss-liuchengtu.hudunsoft.com/userimg/3b/3b446977cb5b2dd11fe3815966a8e839.png)

<a id="feature-media-import"></a>

### 1. 多源媒体导入

集成哔哩哔哩接口可直接获取视频（含登录内容），同时支持本地上传多种格式的音视频文件。系统自动处理文件管理和元数据存储，用户无需手动处理繁琐的文件操作。

![多源媒体导入系统](https://oss-liuchengtu.hudunsoft.com/userimg/a4/a48dd834a2ec5e8436aa8ce02b697e09.png)

<a id="feature-precision-asr"></a>

### 2. 精准语音识别与时间戳分句

![实时语音转文字流程](https://oss-liuchengtu.hudunsoft.com/userimg/8c/8c50fbd2590e589172e32f260dfd8aab.png)

采用行业前沿的 ASR 模型，支持热词识别优化垂直领域准确度。系统自动按句义分割，每个分句精确对应音频时间戳，支持点击即跳转到音视频位置，打破传统文案的线性查看方式。

![双模式 ASR 架构，便于边缘化部署](https://oss-liuchengtu.hudunsoft.com/userimg/c3/c3b18238ab2fb36846e80aff302b12b7.png)

<a id="feature-content-analysis"></a>

### 3. 分层级摘要生成与版本管理

集成大语言模型生成分层级摘要，既能快速获取段落关键信息，也能完整掌握全文内容脉络。摘要自动入库，支持查看历史版本与迭代对比，支持强制重新生成自动覆盖，让内容分析全过程可追溯。

<a id="feature-multilingual"></a>

### 4. 多语言翻译与存储

支持一键翻译为多种目标语言，后台异步处理不阻塞主流程，支持实时查看翻译进度。翻译结果完整持久化，多语言内容共存于一个项目中，轻松管理国际化内容。

![上下文感知的多语言翻译服务架构设计](https://oss-liuchengtu.hudunsoft.com/userimg/1f/1f311c4fc7fac0ed15a4f0ca3b9e3a07.png)

<a id="feature-qa"></a>

### 5. 深度问答交互

基于原始转写内容进行上下文感知的问答。支持多轮追问与对话历史完整保留，系统能准确把握内容脉络，给出针对性的分析答案。

<a id="feature-multimodal"></a>

### 6. 图文融合呈现

自动关联视频关键帧到摘要和问答结果中（仅适用于视频内容）。用户可点击查看大图，实现图文结合的直观表达，让复杂概念更容易理解。

<a id="scenarios"></a>

## 适用场景

学术研究：快速整理讲座音频或视频，建立参考文献档案库。教育培训：自动生成教学讲义和习题解析。内容创作：批量处理视频脚本和文案素材。企业培训：构建结构化的内部知识库与学习平台。客户服务：分析客服录音提取关键问题与解决方案。市场研究：监测竞品视频内容并自动生成分析报告。

## 项目结构

详细的项目结构说明请参考 [项目结构](docs/项目结构.md)。

## API 文档

API 接口文档请参考 [API 文档导航](docs/api_文档导航.md)。

<a id="project-structure"></a>

## 项目结构详细说明

HearSight 采用现代化的微服务架构设计。后端基于 FastAPI 构建高性能 RESTful API，通过 PostgreSQL 实现数据的持久化和查询优化；前端采用 React 18 + TypeScript + Tailwind CSS 提供交互流畅的用户界面。整体支持 Docker 容器化部署，开箱即用。

![架构图](https://oss-liuchengtu.hudunsoft.com/userimg/b5/b54f2ca20885a98aa90ec0557b8354e1.png)

### 项目目录结构

```text
HearSight/
├── ASRBackend/                # 语音识别后端服务
│   ├── asr_functions/         # ASR功能实现
│   ├── routers/               # API路由层
│   ├── services/              # 业务服务层
│   ├── supabase_utils/        # Supabase工具
│   ├── tests/                 # 测试文件
│   ├── docs/                  # 文档
│   ├── example_tests/         # 示例测试
│   ├── config.py              # 配置管理
│   ├── main.py                # 启动入口
│   ├── Dockerfile.local       # 本地模式Docker配置
│   ├── Dockerfile.cloud       # 云端模式Docker配置
│   ├── docker-compose.local.yml  # 本地模式编排配置
│   ├── docker-compose.cloud.yml  # 云端模式编排配置
│   ├── requirements-local.txt    # 本地模式依赖
│   └── requirements-cloud.txt    # 云端模式依赖
│
├── backend/                   # 主后端服务
│   ├── routers/               # API 路由层
│   │   ├── chat/              # 聊天相关接口
│   │   ├── asr_router.py      # 语音识别相关接口
│   │   ├── download_router.py # 媒体下载接口
│   │   ├── progress_router.py # 进度查询接口
│   │   ├── thumbnail_router.py# 缩略图接口
│   │   ├── transcript_router.py # 媒体管理接口
│   │   ├── translate_router.py # 翻译接口
│   │   ├── upload_router.py   # 文件上传接口
│   │   └── ...                # 其他功能路由
│   ├── services/              # 业务服务层
│   │   ├── chat_service.py        # 聊天服务
│   │   ├── download_service.py    # 下载服务
│   │   ├── translate_service.py   # 翻译服务
│   │   ├── transcript_service.py  # 转写服务
│   │   └── ...                    # 其他服务
│   ├── db/                    # 数据库访问层
│   │   ├── chat_message_crud.py   # 聊天消息数据操作
│   │   ├── chat_session_crud.py   # 聊天会话数据操作
│   │   ├── job_base_store.py      # 任务基础数据操作
│   │   ├── job_result_store.py    # 任务结果数据操作
│   │   ├── job_status_store.py    # 任务状态数据操作
│   │   ├── transcript_base_crud.py# 转写基础数据操作
│   │   ├── transcript_crud.py     # 转写数据操作
│   │   ├── transcript_summary_crud.py  # 转写摘要数据操作
│   │   ├── transcript_translation_crud.py  # 转写翻译数据操作
│   │   └── ...
│   ├── audio2text/            # 语音识别模块
│   │   └── asr_sentence_segments.py # ASR 与分句处理
│   ├── media_processing/      # 媒体处理模块
│   │   ├── audio/             # 音频处理
│   │   ├── video/             # 视频处理
│   │   ├── downloader_factory.py  # 下载器工厂
│   │   └── upload_handler.py      # 上传处理
│   ├── queues/                # 队列任务处理
│   │   ├── tasks/             # 具体任务实现
│   │   └── worker_launcher.py # 工作进程启动器
│   ├── text_process/          # 文本处理模块
│   │   ├── translate/         # 翻译处理
│   │   ├── summarize.py       # 摘要生成
│   │   ├── translate.py       # 翻译实现
│   │   └── ...
│   ├── utils/                 # 工具函数
│   ├── config.py              # 配置管理
│   ├── main.py                # 启动入口
│   ├── app.py                 # FastAPI 应用工厂
│   ├── Dockerfile             # Docker配置
│   ├── requirements.txt       # Python依赖
│   └── ...
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
├── docker-compose.cloud.yml   # 云端部署容器编排配置
├── docker-compose.local.yml   # 本地开发容器编排配置
├── docker-compose.cloud.linux.yml   # Linux云端部署容器编排配置
├── docker-compose.cloud.arm.linux.yml  # ARM Linux云端部署容器编排配置
├── README.md                  # 项目说明
└── docs/                      # 项目文档
    ├── 快速开始.md            # 快速开始指南
    ├── 项目结构.md            # 项目结构说明
    └── ...                    # 其他文档
```

## 快速开始

### 获取源代码

```bash
git clone https://github.com/li-xiu-qi/HearSight
cd HearSight
```

### 配置环境变量

在各个后端目录下配置环境变量：

- `ASRBackend/.env`：配置ASR相关环境变量，如DASHSCOPE_API_KEY等
- `backend/.env`：配置主后端环境变量，如数据库、LLM、Embedding等

具体配置项请参考各组件的`.env.example`文件。

### Docker启动

一行命令启动完整服务栈：

```bash
docker-compose -f docker-compose.cloud.yml up -d --build
```

部署完成后，访问 <http://localhost:10000> 即可进入应用。

### 各组件独立启动

项目由多个后端服务组成，各组件可独立启动：

- **ASR Backend**: 语音识别服务，支持云端/本地模式
- **主后端服务**: FastAPI 核心服务，处理业务逻辑
- **前端应用**: React 界面
- **数据库/缓存**: PostgreSQL + Redis

项目由多个后端服务组成，各组件可独立启动。详细启动方法请参考对应章节或各组件的文档：

- [ASR Backend 快速开始](#asr-backend)
- [主后端服务快速开始](#backend)
- [前端应用快速开始](#frontend)

### ARM设备部署

如果您在ARM架构设备上部署HearSight，推荐直接在ARM设备上构建镜像。详细步骤请参考 [ARM设备Docker构建指南](#arm-docker)。

<a id="asr-backend"></a>

## ASR Backend 快速开始

ASR Backend 是HearSight的语音识别服务组件。

### 前置准备

确保已完成环境配置。详见 [快速配置文档](ASRBackend/docs/快速配置.md) 文档。

复制 `.env.example` 为 `.env` 并填入相关配置。

根据运行模式安装对应依赖。

### 启动流程概览

![ASR Backend 启动流程概览图](https://oss-liuchengtu.hudunsoft.com/userimg/3c/3ca71bc17320b25b4f08778e21f6840e.png)
![](https://oss-liuchengtu.hudunsoft.com/userimg/3c/3ca71bc17320b25b4f08778e21f6840e.png)

<a id="asr-cloud"></a>

### 云端模式启动（推荐）

云端模式轻量级，适合大多数场景。

#### 步骤 1：获取 API Key

访问阿里云 DashScope 控制台 <https://dashscope.console.aliyun.com/> 获取 API Key。

若未有阿里云账户，需先注册。

#### 步骤 2：配置环境

编辑 `.env` 文件，填入 DashScope API Key。

```env
ASR_MODE=cloud
DASHSCOPE_API_KEY=sk-xxx
```

#### 步骤 3：安装依赖

```bash
pip install -r requirements-cloud.txt
```

#### 步骤 4：启动服务

```bash
python main.py
```

服务将在 `http://localhost:8003` 启动。

#### 步骤 5：验证服务

打开浏览器访问 `http://localhost:8003/docs`，进入 Swagger 文档界面测试 API。

或使用命令行测试。

```bash
curl http://localhost:8003/health
```

健康检查返回 `{"status": "healthy", "service": "ASR Backend"}` 表示启动成功。

<a id="asr-local"></a>

### 本地模式启动

本地模式完全离线运行，首次运行需下载模型文件，耗时较长。

#### 步骤 1：配置环境

编辑 `.env` 文件，设置运行模式为本地。

```env
ASR_MODE=local
```

#### 步骤 2：安装依赖

```bash
pip install -r requirements-local.txt
```

安装过程可能较长，取决于网络速度。

#### 步骤 3：启动服务

```bash
python main.py
```

首次启动会下载并初始化模型，可能需要 5-10 分钟，这属于正常现象。

#### 步骤 4：验证服务

等待模型加载完成后，服务启动成功。

```bash
curl http://localhost:8003/health
```

<a id="asr-docker"></a>

### Docker 启动

#### 云端模式（轻量级）

```bash
docker build -f Dockerfile.cloud -t hearsight-asr:cloud .

docker run -p 8003:8003 \
  -e ASR_MODE=cloud \
  -e DASHSCOPE_API_KEY=sk-xxx \
  hearsight-asr:cloud
```

#### 本地模式（完整镜像）

```bash
docker build -f Dockerfile.local -t hearsight-asr:local .

docker run -p 8003:8003 \
  -e ASR_MODE=local \
  hearsight-asr:local
```

#### Docker Compose

直接使用 docker-compose 启动服务。

```bash
docker-compose up asr_backend
```

<a id="asr-basic"></a>

### 基本使用

#### 查看 API 文档

访问 <http://localhost:8003/docs> 进入交互式 API 文档。

#### 获取服务信息

```bash
curl http://localhost:8003/asr/info
```

返回当前运行模式、模型配置等信息。

#### URL 转录

使用公开的音频 URL 进行转录。

```bash
curl -X POST "http://localhost:8003/asr/transcribe/url" \
  -d "url=https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"
```

#### 文件上传转录

上传本地音频文件进行转录。

```bash
curl -X POST "http://localhost:8003/asr/transcribe/upload" \
  -F "file=@audio.mp3"
```

#### Python 调用

```python
import requests

# 文件上传
with open("audio.mp3", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8003/asr/transcribe/upload", files=files)
    print(response.json())

# URL 转录
response = requests.post(
    "http://localhost:8003/asr/transcribe/url",
    data={"url": "https://example.com/audio.wav"}
)
print(response.json())
```

### 常见问题（ASR）

#### 服务无法启动

检查端口 8003 是否被占用。修改 `PORT` 环境变量使用其他端口。

检查依赖是否完整安装，可尝试重新安装。

```bash
pip install --upgrade -r requirements-cloud.txt
```

#### 云端模式无法连接

确认 DashScope API Key 正确有效。

检查网络连接是否正常。

#### 本地模式运行缓慢

本地模式首次运行需加载大型模型文件，属于正常现象。

可将模型下载到固定位置加速后续启动。

若运行速度仍然很慢，考虑使用云端模式。

#### 文件上传失败

确认已配置 Supabase 相关环境变量。

检查 Supabase 配置是否有效。

确认音频文件格式支持且文件大小在限制内。

注意阿里云提供的supabase默认不允许将文件设置成public的url提供给外部使用，除非你联系阿里云客服开通，建议使用supabase官网的supabase服务。

<a id="asr-config"></a>

## ASR Backend 快速配置

### 环境要求

Python 版本 3.8 或以上。

系统依赖根据运行模式不同而异。本地模式需要 CUDA 工具链支持 GPU 加速，云端模式无此要求。

网络连接仅云端模式需要。

### 依赖安装

#### 通用依赖

所有模式都需要的基础依赖。

```bash
pip install -r requirements.txt
```

#### 云端模式依赖

云端模式只需要轻量级依赖。

```bash
pip install -r requirements-cloud.txt
```

#### 本地模式依赖

本地模式需要 PyTorch 和相关计算库，可能较大且耗时较长。

```bash
pip install -r requirements-local.txt
```

或通过国内镜像加速安装。

```bash
pip install -r requirements-local.txt -i https://pypi.tsinghua.edu.cn/simple
```

#### 环境变量配置

复制示例文件作为配置文件。

```bash
cp .env.example .env
```

根据需要修改 `.env` 文件中的配置项。

```bash
# ASR Backend 环境变量示例文件
# 复制此文件为 .env，然后根据需要修改配置

# ========== 基本配置 ==========
# 应用名称
APP_NAME=HearSight ASR Backend

# 调试模式
DEBUG=true

# 服务端口
PORT=8003

# ========== 运行模式选择 ==========
# 可选值：local（本地模式）或 cloud（云端模式）
# local: 使用 FunASR 本地模型，支持文件上传和 URL
# cloud: 使用阿里云 DashScope API，仅支持 URL，轻量级部署
ASR_MODE=cloud

# ========== 本地模式配置 ==========
# 仅在 ASR_MODE=local 时生效

# FunASR 模型配置
LOCAL_MODEL_NAME=paraformer-zh
LOCAL_MODEL_REVISION=v2.0.4

# VAD（语音活动检测）模型
LOCAL_VAD_MODEL=fsmn-vad
LOCAL_VAD_MODEL_REVISION=v2.0.4

# 标点符号模型
LOCAL_PUNC_MODEL=ct-punc-c
LOCAL_PUNC_MODEL_REVISION=v2.0.4

# 说话人识别模型
LOCAL_SPK_MODEL=cam++

# ========== 云端模式配置 ==========
# 仅在 ASR_MODE=cloud 时生效

# 阿里云 DashScope API Key
# 从 https://dashscope.console.aliyun.com/ 获取
DASHSCOPE_API_KEY=your-api-key-here

# DashScope 模型
DASHSCOPE_MODEL=paraformer-v2

# 语言提示（用于多语言识别）
DASHSCOPE_LANGUAGE_HINTS=zh,en

# ========== Supabase 配置 ==========
# 用于云端模式的文件上传存储
# 从 https://supabase.com/ 创建项目后获取

# Supabase 项目 URL
SUPABASE_URL=https://your-project.supabase.co

# Supabase API Key (anon public key)
SUPABASE_KEY=your-anon-key-here

# Supabase 存储桶名称
SUPABASE_BUCKET_NAME=test-public

# 上传文件的文件夹名称
SUPABASE_FOLDER_NAME=asr

# 管理员邮箱（可选，用于登录）
SUPABASE_ADMIN_EMAIL=your-admin-email@example.com

# 管理员密码（可选，用于登录）
SUPABASE_ADMIN_PASSWORD=your-admin-password
```

## 运行模式选择

通过 `ASR_MODE` 环境变量选择运行模式。

`ASR_MODE=cloud` 为云端模式，轻量级部署，使用阿里云 DashScope API。

`ASR_MODE=local` 为本地模式，离线运行，使用 FunASR 本地模型。

![ASR_MODE 选择模式图](https://oss-liuchengtu.hudunsoft.com/userimg/ab/abe5260246d2112c052f120df36aeb5e.png)

```env
ASR_MODE=cloud
```

### 云端模式配置

配置云端模式需要以下环境变量。

#### DashScope API Key

从阿里云控制台获取 API Key。访问 <https://dashscope.console.aliyun.com/> 注册并获取。

```env
DASHSCOPE_API_KEY=sk-xxx
```

#### DashScope 模型

默认使用 `paraformer-v2` 模型，这是推荐配置。

```env
DASHSCOPE_MODEL=paraformer-v2
```

#### 语言提示

指定支持的语言，用逗号分隔。支持中文（zh）和英文（en）。

```env
DASHSCOPE_LANGUAGE_HINTS=zh,en
```

#### Supabase 配置（可选，用于文件上传）

若需要上传文件到云端存储，需要配置 Supabase。

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-api-key
SUPABASE_BUCKET_NAME=audio-storage
SUPABASE_FOLDER_NAME=uploads
SUPABASE_ADMIN_EMAIL=admin@example.com
SUPABASE_ADMIN_PASSWORD=admin-password
```

### 本地模式配置

配置本地模式需要以下环境变量。

#### 模型配置

配置使用的 FunASR 模型及其版本。

```env
LOCAL_MODEL_NAME=paraformer-zh
LOCAL_MODEL_REVISION=v2.0.4
```

#### VAD 模型

语音活动检测模型，用于自动分割音频中的有声段。

```env
LOCAL_VAD_MODEL=fsmn-vad
LOCAL_VAD_MODEL_REVISION=v2.0.4
```

#### 标点模型

自动添加标点符号的模型。

```env
LOCAL_PUNC_MODEL=ct-punc-c
LOCAL_PUNC_MODEL_REVISION=v2.0.4
```

#### 说话人模型

用于说话人识别的模型。

```env
LOCAL_SPK_MODEL=cam++
```

#### 配置验证

启动应用前可以验证配置是否正确。

```python
from ASRBackend.config import settings

# 检查基本配置
print(f"运行模式: {settings.asr_mode}")
print(f"调试模式: {settings.debug}")
print(f"服务端口: {settings.port}")

# 验证云端模式配置
if settings.is_cloud_mode():
    settings.validate_config()
    print("云端模式配置有效")
```

#### 常见配置场景

##### 快速云端部署

仅需配置 DashScope API Key。

```env
ASR_MODE=cloud
DASHSCOPE_API_KEY=sk-xxx
```

##### 本地离线运行

仅需配置运行模式。

```env
ASR_MODE=local
```

##### 云端模式带文件上传

需要配置 DashScope 和 Supabase。

```env
ASR_MODE=cloud
DASHSCOPE_API_KEY=sk-xxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-api-key
```

#### Docker 环境配置

使用 Docker 运行时，可通过环境变量覆盖配置。

```bash
docker run -p 8003:8003 \
  -e ASR_MODE=cloud \
  -e DASHSCOPE_API_KEY=sk-xxx \
  hearsight-asr:latest
```

或在 docker-compose.yml 中配置。

```yaml
services:
  asr_backend:
    image: hearsight-asr:latest
    ports:
      - "8003:8003"
    environment:
      ASR_MODE: cloud
      DASHSCOPE_API_KEY: sk-xxx
```

#### 配置优先级

配置覆盖优先级从高到低为：环境变量 > `.env` 文件 > 代码默认值。

环境变量最高优先级，会覆盖所有其他配置。

`.env` 文件用于本地开发配置，会覆盖代码中的默认值。

代码中的默认值最低优先级。

#### 故障排查

若启动时出现配置错误，检查以下项。

云端模式下，确认 `DASHSCOPE_API_KEY` 已正确设置且有效。

若使用文件上传，确认 Supabase 相关配置完整正确。

确认 `.env` 文件的编码为 UTF-8，否则中文字符可能显示异常。

若环境变量未生效，确认变量名称正确（环境变量名不区分大小写）。

有关启动和使用方面的更多信息，请参考 [ASR 快速开始文档](ASRBackend/docs/快速开始.md)。

<a id="backend"></a>

## HearSight 主后端快速开始

### 后端 - 获取源代码

```bash
git clone https://github.com/li-xiu-qi/HearSight
cd HearSight
```

<a id="backend-env"></a>

### 环境配置（后端）

在 `backend/` 目录下创建 [.env](backend/.env) 文件，按需配置以下参数：

```bash
# Postgres - change this password for production
POSTGRES_USER=hearsight
POSTGRES_PASSWORD=hearsight_pass
POSTGRES_DB=hearsight
POSTGRES_PORT=5432
POSTGRES_HOST=localhost

# Backend / Frontend ports (optional)
BACKEND_PORT=9999
FRONTEND_PORT=10000

# LLM 配置（推荐使用百度AI Studio）
LLM_PROVIDER=openai
LLM_MODEL=ernie-4.5-300B-A47B
LLM_PROVIDER_BASE_URL=https://aistudio.baidu.com/llm/lmapi/v3
LLM_PROVIDER_API_KEY= # 必须要配置
LLM_CONTEXT_LENGTH=100000
LLM_TPM=80000
LLM_RPM=1000

# 或者使用硅基流动平台（备选）
# LLM_MODEL=deepseek-ai/DeepSeek-V3.2-Exp
# LLM_PROVIDER_BASE_URL=https://api.siliconflow.cn/v1

# Embedding 配置
EMBEDDING_PROVIDER=openai
EMBEDDING_PROVIDER_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_CONTEXT_LENGTH=8192
EMBEDDING_DIM=1024
EMBEDDING_TPM=500000
EMBEDDING_RPM=2000

# ASR Backend Service
ASR_BACKEND_URL=http://localhost:8003
ASR_MODE= # 'local' 或 'cloud'，留空表示自动检测

# Downloads directory
DOWNLOADS_DIR= # 默认在 app_datas/download_videos

# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_TIME_LIMIT=3600
CELERY_TASK_SOFT_TIME_LIMIT=3300
CELERY_WORKER_CONCURRENCY=4
CELERY_LOG_LEVEL=info
```

在 `ASRBackend/` 目录下也需要创建 [.env](ASRBackend/.env) 文件：

```bash
# ASR Backend 环境变量配置

# ========== 基本配置 ==========
APP_NAME=HearSight ASR Backend
DEBUG=true
PORT=8003

# CORS 配置
CORS_ORIGINS_STR=http://localhost:5173,http://localhost:8080,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS_STR=*
CORS_ALLOW_HEADERS_STR=*

# ========== 运行模式 ==========
# cloud: 云端模式（默认，轻量级）
# local: 本地模式（完整功能）
ASR_MODE=local

# ========== 云端模式配置 ==========
DASHSCOPE_API_KEY=your_dashscope_api_key
DASHSCOPE_MODEL=paraformer-v2
DASHSCOPE_LANGUAGE_HINTS=zh,en

# ========== Supabase 配置 ==========
# 用于云端模式的文件上传存储
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_BUCKET_NAME=test-public
SUPABASE_FOLDER_NAME=asr
SUPABASE_ADMIN_EMAIL=your-admin-email@example.com
SUPABASE_ADMIN_PASSWORD=your-admin-password

# ========== 本地模式配置 ==========
# 仅在 ASR_MODE=local 时生效
LOCAL_MODEL_NAME=paraformer-zh
LOCAL_MODEL_REVISION=v2.0.4
LOCAL_VAD_MODEL=fsmn-vad
LOCAL_VAD_MODEL_REVISION=v2.0.4
LOCAL_PUNC_MODEL=ct-punc-c
LOCAL_PUNC_MODEL_REVISION=v2.0.4
LOCAL_SPK_MODEL=cam++
```

快速提示：项目推荐使用百度AI Studio的OpenAI兼容API作为LLM服务，可使用ernie-4.5-300B-A47B模型。配置AI_STUDIO_API_KEY（对应OpenAI SDK的api_key字段）和base_url="<https://aistudio.baidu.com/llm/lmapi/v3"（对应OpenAI> SDK的base_url字段）即可。更具体的内容可以参考：<<https://ai.baidu.com/ai-doc/AISTUDIO/rm344erns。Embedding服务默认使用硅基流动的OpenAI兼容API，平台地址：https://siliconflow.cn，免费额度申请：https://cloud.siliconflow.cn/i/FcjKykMn。DASHSCOPE_API_KEY可从阿里云百炼获取。>

### 启动依赖服务

HearSight 后端依赖以下服务：

1. PostgreSQL 数据库
2. Redis 服务器
3. ASRBackend 服务（用于语音识别）

可以通过 Docker 一键启动这些依赖服务：

```bash
# 在项目根目录（HearSight/）下执行
docker-compose -f docker-compose.local.yml up -d postgres redis asr_backend
```

或者分别手动启动这些服务。

更多关于 ASRBackend 的配置和使用信息，请参考 [ASRBackend 相关文档](ASRBackend/docs/)：

- [ASR 服务设计文档](ASRBackend/docs/ASR_服务设计文档.md)
- [ASR 快速开始指南](ASRBackend/docs/快速开始.md)
- [ASR 快速配置](ASRBackend/docs/快速配置.md)
- [ASR API 文档](ASRBackend/docs/api.md)
- [ASR Docker 部署](ASRBackend/docs/docker_deployment.md)
- [ASR 设计说明](ASRBackend/docs/设计说明.md)

<a id="backend-container"></a>

### 容器化部署（后端）

#### 使用项目根目录的 docker-compose 文件（推荐）

一行命令启动后端服务及相关依赖：

```bash
# 在项目根目录（HearSight/）下执行
docker-compose -f docker-compose.cloud.yml up -d --build
```

#### 使用 backend 目录下的 docker-compose 文件

你也可以使用 backend 目录下专门为后端服务创建的统一 docker-compose 文件，但需要注意该文件不包含数据库和Redis服务，需要确保这些依赖服务已经运行：

```bash
# 在 backend/ 目录下执行，确保已启动 PostgreSQL、Redis 和 ASRBackend 服务
docker-compose -f docker-compose.yml up -d --build
```

部署完成后，访问 <http://localhost:9999> 即可进入后端服务。

如果仅需使用容器运行 PostgreSQL 数据库，而将后端在本地启动，请参考下方本地部署方案。

<a id="backend-local"></a>

### 本地开发部署（主后端）

#### 前置要求（主后端）

需要 PostgreSQL 数据库和 Redis 服务器运行。可通过 Docker 启动也可本地安装。

#### 后端服务启动

1. 安装依赖

   ```bash
   # 在项目根目录（HearSight/）下执行
   pip install -r requirements.txt
   ```

2. 启动服务

   ```bash
   # 在项目根目录（HearSight/）下执行
   python main.py
   ```

   后端运行在 `http://localhost:9999`

<a id="backend-verify"></a>

### 验证服务

打开浏览器访问 `http://localhost:9999/docs`，进入 Swagger 文档界面测试 API。

或使用命令行测试：

```bash
curl http://localhost:9999/health
```

健康检查应该返回类似以下的信息表示启动成功：

```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00"
}
```

### 常见问题（后端）

#### 数据库连接失败

检查 [.env](backend/.env) 中的数据库配置是否正确，确保 PostgreSQL 服务正在运行。

#### Redis 连接失败

检查 Redis 配置，默认使用 `redis://localhost:6379/0`，确保 Redis 服务正在运行。

#### 端口被占用（后端）

修改启动命令中的端口号：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

<a id="frontend"></a>

## HearSight 前端快速开始

<a id="frontend-prepare"></a>

### 环境准备

#### 前置要求（前端）

- Node.js 18.x 或更高版本
- npm 或 yarn 包管理器

#### 前端 - 获取源代码

```bash
git clone https://github.com/li-xiu-qi/HearSight
cd HearSight/frontend
```

<a id="frontend-config"></a>

### 环境配置（前端）

在 `frontend/` 目录下创建 `.env` 文件，按需配置以下参数：

```bash
# 后端 API 地址（默认为本地开发环境）
VITE_BACKEND_URL=http://localhost:9999

# 是否在 Docker 环境中运行（默认为false）
VITE_USE_DOCKER=false

# 后端主机地址（用于Docker环境）
BACKEND_HOST=localhost

# 后端端口（用于Docker环境）
BACKEND_PORT=9999

# 是否使用Docker（用于Vite代理配置）
USE_DOCKER=false
```

环境变量说明：

- `VITE_BACKEND_URL`: 前端应用连接的后端API地址
- `VITE_USE_DOCKER`: 标识是否在Docker环境中运行
- `BACKEND_HOST` 和 `BACKEND_PORT`: 用于Vite代理配置，在Docker环境中指向后端服务容器
- `USE_DOCKER`: 控制Vite代理使用容器名还是localhost

<a id="frontend-install"></a>

### 安装依赖

```bash
npm install
```

<a id="frontend-container"></a>

### 容器化部署（前端）

#### 使用项目根目录的 Docker Compose（推荐）

项目根目录提供了完整的 [docker-compose.cloud.yml](docker-compose.cloud.yml) 文件，可以一键启动包括前端在内的所有服务：

```bash
# 在项目根目录执行
docker-compose -f ../docker-compose.cloud.yml up -d --build
```

#### 使用前端独立的 Docker Compose

前端目录下提供了独立的 [docker-compose.yml](frontend/docker-compose.yml) 文件，可用于单独部署前端服务：

```bash
# 在 frontend 目录下执行
docker-compose up -d --build
```

注意：使用独立的 docker-compose 文件时，需要确保后端服务已经在运行并且可以通过网络访问。

#### 单独构建前端镜像

```bash
# 构建 Docker 镜像
docker build -t hearsight-frontend .

# 运行容器
docker run -p 5173:5173 hearsight-frontend
```

<a id="frontend-local"></a>

### 本地开发部署（前端）

#### 启动开发服务器

```bash
npm run dev
```

默认情况下，开发服务器将在 `http://localhost:5173` 上运行。

#### 构建生产版本

```bash
npm run build
```

构建后的文件将位于 `dist` 目录中。

#### 预览生产构建

```bash
npm run preview
```

### 测试

运行测试：

```bash
npm run test
```

### 常见问题（前端）

#### API 连接失败

检查 `.env` 文件中的 `VITE_BACKEND_URL` 配置是否正确，确保后端服务正在运行。

#### 依赖安装失败

尝试清除缓存后重新安装：

```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### 端口被占用（前端）

修改 `vite.config.ts` 中的端口配置：

```javascript
export default defineConfig({
  server: {
    port: 5173 // 修改为其他端口
  }
})
```

#### Docker 环境中无法连接后端

确保在 Docker 环境中正确设置了 `USE_DOCKER=true` 和 `BACKEND_HOST=backend` 环境变量。

<a id="features"></a>

## Radxa设备大语言模型部署指南

### 概述（Radxa）

本文档介绍在Radxa设备上部署大型语言模型（LLM）的工具和方法，主要包括Llama.cpp和Ollama。

<a id="radxa-llama"></a>

### Llama.cpp

Llama.cpp的主要目标是在各种硬件（本地和云端）上实现LLM推理，只需最少的设置，同时提供最先进的性能。

#### 量化格式对比

以下是不同的量化格式及其性能表现（基于Llama-3-8B模型）：

```text
2 或 Q4_0    : 4.34GB, +0.4685 困惑度 @ Llama-3-8B
3 或 Q4_1    : 4.78GB, +0.4511 困惑度 @ Llama-3-8B
8 或 Q5_0    : 5.21GB, +0.1316 困惑度 @ Llama-3-8B
9 或 Q5_1    : 5.65GB, +0.1062 困惑度 @ Llama-3-8B
19 或 IQ2_XXS : 2.06 bpw 量化
20 或 IQ2_XS  : 2.31 bpw 量化
28 或 IQ2_S   : 2.5  bpw 量化
29 或 IQ2_M   : 2.7  bpw 量化
24 或 IQ1_S   : 1.56 bpw 量化
31 或 IQ1_M   : 1.75 bpw 量化
36 或 TQ1_0   : 1.69 bpw 三值化
37 或 TQ2_0   : 2.06 bpw 三值化
10 或 Q2_K    : 2.96GB, +3.5199 困惑度 @ Llama-3-8B
21 或 Q2_K_S  : 2.96GB, +3.1836 困惑度 @ Llama-3-8B
23 或 IQ3_XXS : 3.06 bpw 量化
26 或 IQ3_S   : 3.44 bpw 量化
27 或 IQ3_M   : 3.66 bpw 量化混合
12 或 Q3_K    : Q3_K_M的别名
22 或 IQ3_XS  : 3.3 bpw 量化
11 或 Q3_K_S  : 3.41GB, +1.6321 困惑度 @ Llama-3-8B
12 或 Q3_K_M  : 3.74GB, +0.6569 困惑度 @ Llama-3-8B
13 或 Q3_K_L  : 4.03GB, +0.5562 困惑度 @ Llama-3-8B
25 或 IQ4_NL  : 4.50 bpw 非线性量化
30 或 IQ4_XS  : 4.25 bpw 非线性量化
15 或 Q4_K    : Q4_K_M的别名
14 或 Q4_K_S  : 4.37GB, +0.2689 困惑度 @ Llama-3-8B
15 或 Q4_K_M  : 4.58GB, +0.1754 困惑度 @ Llama-3-8B
17 或 Q5_K    : Q5_K_M的别名
16 或 Q5_K_S  : 5.21GB, +0.1049 困惑度 @ Llama-3-8B
17 或 Q5_K_M  : 5.33GB, +0.0569 困惑度 @ Llama-3-8B
18 或 Q6_K    : 6.14GB, +0.0217 困惑度 @ Llama-3-8B
7 或 Q8_0    : 7.96GB, +0.0026 困惑度 @ Llama-3-8B
1 或 F16     : 14.00GB, +0.0020 困惑度 @ Mistral-7B
32 或 BF16    : 14.00GB, -0.0050 困惑度 @ Mistral-7B
0 或 F32     : 26.00GB @ 7B
        COPY    : 仅复制张量，不量化
```

#### 实际使用示例

##### 对话示例

```text
> 你好，你是谁
<think>

</think>

你好！我是DeepSeek-R1，由DeepSeek创建的人工智能助手。我随时为您服务，很乐意协助您解决任何疑问或任务。
```

##### 性能基准测试

在Radxa Orion O6上进行性能测试：

```bash
radxa@orion-o6:~/llama.cpp/build/bin$ ./llama-bench -m ~/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf -t 8
| 模型                          |       大小 |     参数量 | 后端    | 线程数 |          测试 |                  速度 |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | ------------: | -------------------: |
| qwen2 1.5B Q4_K - Medium       |   1.04 GB |     1.78 B | CPU        |       8 |         pp512 |         64.60 ± 0.27 |
| qwen2 1.5B Q4_K - Medium       |   1.04 GB |     1.78 B | CPU        |       8 |         tg128 |         36.29 ± 0.16 |
```

测试结果显示，在8线程配置下，预填充速度达到64.60 tokens/秒，生成速度达到36.29 tokens/秒。

<a id="radxa-ollama"></a>

### Ollama

Ollama是一个在本地运行和管理大型语言模型（LLM）的工具。它使您能够轻松地在本地设备上拉取、运行和管理各种AI模型（如LLaMA、Mistral和Gemma），而无需复杂的环境配置。

#### 安装Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

关于本地构建方法，请参考[官方文档](https://github.com/ollama/ollama/blob/main/docs/development.md)。

#### 使用方法

##### 拉取模型

此命令从互联网下载模型文件。

```bash
ollama pull deepseek-r1:1.5b
```

##### 运行模型

此命令直接运行模型。如果模型未在本地缓存，它会在运行前自动下载。

```bash
ollama run deepseek-r1:1.5b
```

##### 显示模型信息

```bash
ollama show deepseek-r1:1.5b
```

##### 列出计算机上的模型

```bash
ollama list
```

##### 列出当前已加载的模型

```bash
ollama ps
```

##### 停止当前正在运行的模型

```bash
ollama stop deepseek-r1:1.5b
```

##### 删除模型

```bash
ollama rm deepseek-r1:1.5b
```

### 参考

- Llama.cpp官方文档：<https://github.com/ggml-org/llama.cpp>
- 使用Llama.cpp在Radxa上运行LLM：<https://docs.radxa.com/en/orion/o6/app-development/artificial-intelligence/llama_cpp>
- Ollama官方文档：<https://github.com/ollama/ollama>
- 使用Ollama在Radxa上运行LLM：<https://docs.radxa.com/en/orion/o6/app-development/artificial-intelligence/ollama>

<a id="arm-docker"></a>

## ARM设备Docker构建指南

### 概述（ARM 设备 Docker 构建）

本指南介绍如何将HearSight项目的Docker镜像构建并部署到ARM架构设备上。如ARM设备资源充足，推荐直接在ARM设备上构建；否则，使用交叉构建方式。

<a id="arm-build-flow"></a>

### 构建流程

<a id="arm-direct-build"></a>

#### 直接构建流程（推荐）

[ARM设备直接构建流程图](docs/mermaid图汇集/ARM设备直接构建流程图.md)

<a id="arm-cross-build"></a>

#### 交叉构建流程（备选）

[ARM设备交叉构建流程图](docs/mermaid图汇集/ARM设备交叉构建流程图.md)

### 选择合适的docker-compose文件

HearSight项目提供多个docker-compose文件，根据运行环境选择：

- **docker-compose.cloud.yml**：适用于Windows主机，使用build指令构建镜像，云端ASR模式。
- **docker-compose.cloud.linux.yml**：适用于Linux主机，使用build指令构建镜像，云端ASR模式。
- **docker-compose.cloud.arm.linux.yml**：适用于ARM Linux设备，使用预构建的image指令，云端ASR模式。
- **docker-compose.local.yml**：适用于Linux主机，使用build指令构建镜像，本地ASR模式（需要CUDA支持）。

根据主机操作系统和ASR模式选择相应文件：

- Windows（云端ASR）：使用docker-compose.cloud.yml
- Linux（云端ASR）：使用docker-compose.cloud.linux.yml
- ARM Linux（云端ASR）：使用docker-compose.cloud.arm.linux.yml
- Linux（本地ASR）：使用docker-compose.local.yml

**重要说明**：对于ARM设备，推荐优先使用云端模式的docker-compose文件（如docker-compose.cloud.arm.linux.yml），因为本地的语音识别docker需要依赖CUDA，而ARM设备上CUDA支持有限或配置复杂。云端模式使用阿里云DashScope API，无需本地GPU资源。

### 配置环境变量

运行docker-compose前，创建环境变量文件：

- **backend/.env**：后端服务配置，包含数据库、API密钥等。
- **ASRBackend/.env**：ASR后端配置，包含API密钥等。

参考项目中的.env.example文件。

#### 获取API密钥

- **语音识别模型密钥 (DASHSCOPE_API_KEY)**：前往阿里云百炼控制台获取DashScope API密钥。
- **Supabase配置**：前往 [Supabase官网](https://supabase.com/) 注册并创建项目。选择Public bucket，配置策略为：允许用户上传文件到名为asr的存储桶，文件名以.wav结尾，用户为<lixiuqixiaoke@qq.com>。

示例backend/.env内容：

```
POSTGRES_USER=hearsight
POSTGRES_PASSWORD=hearsight_pass
POSTGRES_DB=hearsight
BACKEND_PORT=9999
FRONTEND_PORT=10000
OPENAI_API_KEY=your_key
# 其他变量...
```

示例ASRBackend/.env内容：

```
ASR_MODE=cloud
DASHSCOPE_API_KEY=your_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_BUCKET_NAME=test-public
SUPABASE_FOLDER_NAME=asr
SUPABASE_ADMIN_EMAIL=your-admin-email@example.com
SUPABASE_ADMIN_PASSWORD=your-admin-password
```

确保.env文件不提交到版本控制。

### 直接在ARM设备上构建

如果ARM设备资源充足，直接在ARM设备上构建镜像。

#### 步骤

1. 在ARM设备上安装Docker。
2. 配置Docker镜像加速。
3. 传输项目代码到ARM设备：

   ```bash
   scp -r C:\Users\ke\Downloads\HearSight root@arm-ip:/home/ke123/
   ```

   或使用U盘传输。

4. 创建环境变量文件。
5. 构建并运行：

   ```bash
   cd /home/ke123/HearSight
   docker-compose -f docker-compose.cloud.linux.yml build
   docker-compose -f docker-compose.cloud.linux.yml up -d
   ```

#### 优势

- 无需x86主机。
- 无需传输大文件。
- 确保兼容性。

#### 注意

- ARM设备需足够资源。
- 构建时间较长。
- 网络慢时配置加速。

<a id="arm-cross-to-device"></a>

### 交叉构建到ARM设备

如果ARM设备资源有限，在x86主机上交叉构建ARM64镜像，然后传输。

#### 详细步骤

1. 启用Docker Buildx：

   ```bash
   docker buildx create --use
   ```

2. 检查Dockerfile兼容性，确保基础镜像支持ARM64。
3. 构建多架构镜像：

   ```bash
   docker buildx build --platform linux/arm64 -t image:arm64 --load ./backend
   ```

4. 保存镜像为文件：

   ```bash
   mkdir -p docker-images
   docker save hearsight-backend:arm64 > docker-images/backend-arm64.tar
   docker save hearsight-frontend:arm64 > docker-images/frontend-arm64.tar
   docker save hearsight-asr-backend:arm64 > docker-images/asr-backend-arm64.tar
   docker save hearsight-celery-worker:arm64 > docker-images/celery-worker-arm64.tar
   ```

5. 传输到ARM设备：

   ```bash
   scp docker-images/*.tar user@arm-ip:/path/
   ```

   或使用U盘。

6. 在ARM设备上加载并运行：

   - 加载镜像：

   ```bash
   docker load < backend-arm64.tar
   docker load < frontend-arm64.tar
   docker load < asr-backend-arm64.tar
   docker load < celery-worker-arm64.tar
   ```

   - 运行服务：

   ```bash
   docker-compose -f docker-compose.cloud.yml up -d
   ```

     或单独运行celery-worker：

   ```bash
   docker run -d --name celery-worker hearsight-celery-worker:arm64 python -m backend.queues.worker_launcher
   ```

#### 构建多个服务

需要构建的服务：

- backend：

  ```
  docker buildx build --platform linux/arm64 -t hearsight-backend:arm64 --load -f backend/Dockerfile .
  ```

- frontend：

  ```
  docker buildx build --platform linux/arm64 -t hearsight-frontend:arm64 --load ./frontend
  ```

- asr-backend：

  ```
  docker buildx build --platform linux/arm64 -t hearsight-asr-backend:arm64 --load -f Dockerfile.cloud .
  ```

- celery-worker：

  ```
  docker buildx build --platform linux/arm64 -t hearsight-celery-worker:arm64 --load -f backend/Dockerfile .
  ```

- redis：使用现成镜像，无需构建。

### 在ARM设备上安装Docker

如果ARM设备未安装Docker，按以下步骤安装：

```
# 更新包索引
sudo apt update

# 安装必要包
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# 添加Docker GPG密钥
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新包索引
sudo apt update

# 安装Docker CE
sudo apt install docker-ce docker-ce-cli containerd.io

# 启动Docker服务
sudo systemctl start docker

# 设置开机自启
sudo systemctl enable docker

# 安装Docker Compose
sudo apt install docker-compose

# 添加用户到docker组
sudo usermod -aG docker $USER
```

安装后，验证版本。

#### 配置Docker镜像加速

配置镜像加速源，如<https://docker.1ms.run：>

- 全局配置：

  编辑 /etc/docker/daemon.json：

  ```
  {
    "registry-mirrors": ["https://docker.1ms.run"]
  }
  ```

  重启Docker：

  ```
  sudo systemctl restart docker
  ```

- 针对特定镜像：在docker-compose中修改image。

### 注意事项

- 确保Docker版本支持Buildx。
- 调整Dockerfile为ARM兼容。
- 构建时间长，建议在x86上进行。
- 测试ARM设备运行效果。
- 如果PyPI下载SSL错误，更换PIP_INDEX_URL为其他源，并添加PIP_TRUSTED_HOST。

<a id="summary"></a>

## 总结

本教程详细介绍了HearSight项目的安装、配置和使用方法。HearSight是一个强大的音视频内容智能分析工具，能够帮助用户快速处理和分析多媒体内容。

通过本教程，你可以学习到：

- 如何获取和配置HearSight项目
- 不同组件（后端、ASR、前端）的启动方法
- 项目的核心功能和适用场景
- 常见问题的解决方法

如果在部署或使用过程中遇到问题，可以参考各个组件的文档或寻求社区帮助。

祝你使用愉快！
