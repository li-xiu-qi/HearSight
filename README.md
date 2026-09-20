# 📖 项目介绍

![HearSight logo](https://oss-liuchengtu.hudunsoft.com/userimg/33/3374fce0ebc0d82f093c6c7361b84fcc.png)

HearSight 是一个音视频内容智能分析工具。通过集成先进的语音识别、自然语言处理和大语言模型技术，HearSight 能够自动将视频和音频转化为结构化的文本内容，并在此基础上进行多维度的智能分析和问答交互。无论您是进行学术研究、内容创作还是知识管理，HearSight 都能帮助您深度挖掘音视频内容的价值。

[B站视频介绍](https://www.bilibili.com/video/BV1D5UgBYEtC/?vd_source=325d9b8b91626b0afd2ef63a99caf970)

<div style="text-align: center; margin: auto;">
    <iframe src="//player.bilibili.com/player.html?isOutside=true&aid=115602047899223&bvid=BV1D5UgBYEtC&cid=34218837346&p=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"></iframe>
</div>

项目地址：<https://github.com/li-xiu-qi/HearSight>

## 🛠 技术架构

HearSight 采用本地优先的单体全栈架构。Web 层是 Next.js 全栈应用（TypeScript 前后端同仓，API 路由即后端），数据落在本地 SQLite，任务进度通过服务端事件推送，不依赖消息队列与外部缓存；AI 能力拆为三个可替换的本地服务：语音识别（本地模型，输出句级毫秒时间戳与说话人分离）、向量检索（本地 Embedding 服务加 SQLite 向量表）、大语言模型（OpenAI 兼容协议，默认指向本机推理服务，改三个环境变量即可切换外部 API）。媒体处理（抽音轨、抽关键帧、链接下载）由服务端直接调用本地 ffmpeg 与 yt-dlp。

一台带 NVIDIA GPU 的 Linux 机器即可跑通全链路；也可以只起 Web 层，把 AI 服务指向别处。

## ✨ 核心能力

![核心能力](https://oss-liuchengtu.hudunsoft.com/userimg/eb/eb8ce69e51ffee1798ab4419f391adab.png)

- 📹 集成式媒体导入：直接从哔哩哔哩获取内容，同时支持本地上传视频和音频文件，支持 MP4、AVI、MOV、MKV、MP3、WAV、M4A、AAC 等多种格式
- 🎯 精准语音转写：采用业界领先的 ASR 技术，支持热词识别和实时精确时间戳，自动分句并生成可交互式的文本档案
- 🧠 智能内容分析：基于大语言模型生成段落级和全文级的结构化摘要，支持持久化保存和迭代优化
- 💬 对话式内容理解：支持基于原文的深度问答交互，准确把握关键信息和核心观点，支持单视频和多视频的综合问答与对比分析
- 🖼️ 多模态信息展示：在问答和总结中融入视频关键帧，实现图文融合的高效表达（仅适用于视频内容）
- 🌐 多语言内容转换：支持自动翻译为多种语言，翻译结果完整保存，便于国际化场景使用

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

## 📂 项目结构

详细的项目结构说明请参考 [项目结构](docs/项目结构.md)。

## 📡 API 文档

API 接口文档请参考 [API 文档导航](docs/api_文档导航.md)。

## 🚀 快速开始

本地模式要求：Node.js 20+、Python 3.10+、ffmpeg、yt-dlp，以及带 NVIDIA GPU 的 Linux 机器（语音识别、向量、推理三个服务都跑在本地）。

```bash
# 1. 安装依赖并构建（--include=dev 不能省，否则跳过类型检查）
cd next-app && npm install --include=dev && npm run build && cd ..

# 2. 按需准备环境变量（缺省全部指向本机回环，零配置可跑）
cp next-app/.env.production.example next-app/.env.production

# 3. 启动 Web 层（默认端口 9187；三个 AI 服务需另行启动）
bash scripts/start-local.sh
```

环境变量逐项说明见 `next-app/.env.production.example`。

## 🎯 适用场景

学术研究：快速整理讲座音频或视频，建立参考文献档案库。教育培训：自动生成教学讲义和习题解析。内容创作：批量处理视频脚本和文案素材。企业培训：构建结构化的内部知识库与学习平台。客户服务：分析客服录音提取关键问题与解决方案。市场研究：监测竞品视频内容并自动生成分析报告。

## 🔧 功能详解

![功能结构说明图](https://oss-liuchengtu.hudunsoft.com/userimg/3b/3b446977cb5b2dd11fe3815966a8e839.png)

### 1. 多源媒体导入

集成哔哩哔哩接口可直接获取视频（含登录内容），同时支持本地上传多种格式的音视频文件。系统自动处理文件管理和元数据存储，用户无需手动处理繁琐的文件操作。

![多源媒体导入系统](https://oss-liuchengtu.hudunsoft.com/userimg/a4/a48dd834a2ec5e8436aa8ce02b697e09.png)

### 2. 精准语音识别与时间戳分句

![实时语音转文字流程](https://oss-liuchengtu.hudunsoft.com/userimg/8c/8c50fbd2590e589172e32f260dfd8aab.png)

采用行业前沿的 ASR 模型，支持热词识别优化垂直领域准确度。系统自动按句义分割，每个分句精确对应音频时间戳，支持点击即跳转到音视频位置，打破传统文案的线性查看方式。

![双模式 ASR 架构，便于边缘化部署](https://oss-liuchengtu.hudunsoft.com/userimg/c3/c3b18238ab2fb36846e80aff302b12b7.png)

### 3. 分层级摘要生成与版本管理

集成大语言模型生成分层级摘要，既能快速获取段落关键信息，也能完整掌握全文内容脉络。摘要自动入库，支持查看历史版本与迭代对比，支持强制重新生成自动覆盖，让内容分析全过程可追溯。

### 4. 多语言翻译与存储

支持一键翻译为多种目标语言，后台异步处理不阻塞主流程，支持实时查看翻译进度。翻译结果完整持久化，多语言内容共存于一个项目中，轻松管理国际化内容。

![上下文感知的多语言翻译服务架构设计](https://oss-liuchengtu.hudunsoft.com/userimg/1f/1f311c4fc7fac0ed15a4f0ca3b9e3a07.png)

### 5. 深度问答交互

![LLM与人类对话](https://oss-liuchengtu.hudunsoft.com/userimg/48/4859d90457fc8cab88295847cc9bfc1c.png)

基于原始转写内容进行上下文感知的问答，支持单视频和多视频的综合分析。支持多轮追问与对话历史完整保留，系统能准确把握内容脉络，给出针对性的分析答案。

![ReAct后端问答设计](https://oss-liuchengtu.hudunsoft.com/userimg/a3/a327b36d0ddb4fcaa99a27a4f4cfff42.png)

### 6. 图文融合呈现

自动关联视频关键帧到摘要和问答结果中（仅适用于视频内容）。用户可点击查看大图，实现图文结合的直观表达，让复杂概念更容易理解。

### 7. 技术策略

HearSight 在实现过程中采用了许多的技术策略，以提升系统的性能和实际效果：

#### Embedding 文件名增强策略

在知识库检索环节，我们实现了 embedding 文件名增强技术。通过在生成文本向量时，将文件名信息与内容文本相结合，形成更丰富的上下文嵌入。具体实现是在 chunk_text 前添加文件名描述，如 "文件名：[filename]\n内容：[text]"，从而提升基于文件名提问的检索准确性。该策略有效解决了传统 embedding 仅基于内容而忽略文件名导致的检索不准问题，显著改善了用户查询体验，因为用户基于文件标题提问，很容易错漏相关文件，而给文件名一起进行embedding，会使得整个的效率，召回率平均能提升30%以上。
![文件名增强embedding](https://oss-liuchengtu.hudunsoft.com/userimg/04/04e4675db680c35a70dd6ead54b5a6ce.png)

#### ReAct 记忆管理策略

![ReAct双层记忆管理机制](https://oss-liuchengtu.hudunsoft.com/userimg/ff/fff9b992a690c7030ddf99bee7f57174.png)

在对话问答系统中，我们采用了先进的 ReAct 记忆管理机制，以应对大语言模型的上下文长度限制。通过智能的记忆压缩和上下文重组，当对话积累的消息超过阈值时，系统自动生成对话摘要，将关键信息压缩存储，同时保留完整的消息历史用于精确重组。这种增量总结策略确保了多轮对话的连贯性，避免了信息丢失，同时控制了上下文长度，提升了问答系统的稳定性和效率。记忆管理分为对话记忆和任务执行记忆两层，前者维持用户与助手的对话连贯性，后者管理单次任务的推理过程，确保了系统的可扩展性和性能优化。
![ReAct后端问答设计](https://oss-liuchengtu.hudunsoft.com/userimg/a3/a327b36d0ddb4fcaa99a27a4f4cfff42.png)

#### 检索内容重组策略

在多视频问答场景中，我们设计了层次化的检索内容重组结构，以确保不同视频和内容块有清晰的分界线。该结构采用嵌套标签系统：[视频开始/结束] 包围整个视频内容，[块开始/结束] 分隔连续的内容片段，每个句子附带精确的时间戳 [filename start-end]。这种设计避免了多视频内容混淆的问题，使大语言模型能够准确识别和引用特定视频段落，提升问答的精确性和可追溯性，同时保持提示词的结构化和可读性。
![检索内容重组策略](https://oss-liuchengtu.hudunsoft.com/userimg/9c/9c5fa9824b2395d8563890d05a7e73ac.png)

## 🤝 参与贡献

HearSight 是一个开源项目，我们欢迎来自社区的改进和贡献。无论是功能增强、bug 修复还是文档改进，都可以通过提交 Pull Request 的方式参与。如果有好的想法或发现问题，也可以直接提交 Issue。

## 📝 开源许可

本项目采用 Apache-2.0 License 开源许可证。详见 LICENSE 文件。
