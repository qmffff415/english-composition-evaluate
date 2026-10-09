# 考研英语（一 / 二）写作智能评卷系统

基于 **RAG 检索增强 + 大语言模型** 的考研英语写作自动评卷系统。围绕考研英语大纲的官方评分标准构建知识库，对考生作文做四维度量化打分，输出可解释的结构化评卷报告。

支持 **英语一**（Part A 应用文 10 分 / Part B 图画作文 20 分）与 **英语二**（Part A 应用文 10 分 / Part B 图表作文 15 分）。

## 功能特性

- **大纲对齐的四维度评分** — 内容完整性、组织连贯性、语言质量、格式规范与语域，每个维度给出得分、得分率与扣分理由，而非只给一个总分
- **档位判定** — 按官方评分档次（第一档 ~ 第五档）定位作文水平，附阅卷组长综合评语
- **RAG 知识检索** — 从评分标准、历年真题范文、写作知识、常见错误四大模块中检索上下文，让评分有据可依，而非模型自由发挥
- **多模型支持** — 内置 DeepSeek / 通义千问 / Kimi / 智谱 GLM / 本地 Ollama 预设，任何 OpenAI 兼容接口均可接入
- **多格式作文录入** — 直接粘贴，或上传 `txt` / `pdf` / `doc` / `docx` / `md` / `png` / `jpg` / `jpeg`，图片走 OCR 识别
- **真题范文库** — 按考试类别、年份、题型、关键词检索历年真题与高分标杆范文
- **降级容错** — Milvus 不可用时自动回退到本地分块检索，服务不中断
- **报告留档** — 每次评卷生成 Markdown 报告，按用户隔离保存

## 系统架构

```
                        ┌──────────────────────────────┐
                        │   Vue 3 + Vite 前端 (:5173)   │
                        │  编辑器 / 评分可视化 / 历史   │
                        └───────────────┬──────────────┘
                                        │ /api/*  代理
                        ┌───────────────▼──────────────┐
                        │     Flask 服务端 (:5000)      │
                        └───────────────┬──────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
┌───────────────┐             ┌─────────────────┐             ┌────────────────┐
│  预处理层      │             │    RAG 检索层    │             │   评分与出报    │
│ 词数/段落      │             │  向量召回 + 重排 │             │  结构化打分     │
│ 题型自动识别   │             │                 │             │  Markdown 报告  │
│ 规则初筛       │             │                 │             │                │
└───────────────┘             └────────┬────────┘             └────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
          ┌───────────────────┐                 ┌──────────────────┐
          │  Milvus 向量库     │                 │  Ollama 嵌入模型  │
          │  315 个知识分块    │                 │  bge-m3          │
          └───────────────────┘                 └──────────────────┘
                                       │
                                       ▼ 不可用时降级
                              ┌──────────────────┐
                              │  本地分块检索     │
                              │  knowledge_base/ │
                              └──────────────────┘
```

### 评卷流程

1. **预处理** — 统计词数、切分段落与句子，自动识别题型（小作文 / 大作文），执行规则初筛（词数不足、格式缺失等硬性扣分项）
2. **检索** — 以作文文本与题型为查询，按四类知识模块分别召回相关评分标准、范文片段与常见错误条目
3. **评分** — 组装系统提示词与检索上下文，调用大模型输出结构化 JSON 评分结果；解析失败时走正则兜底抽取
4. **出报** — 渲染为带档位、维度雷达、逐句批注的 Markdown 报告并落盘

## 知识库构成

知识库共 **315 个检索分块**，构建自大纲评分标准与历年真题语料：

| 模块 | 分块数 | 内容 |
| :--- | ---: | :--- |
| `sample_essays` | 92 | 历年真题与高分标杆范文，含结构分析与亮点句式 |
| `question_templates` | 85 | 历年真题题目与题型模板 |
| `writing_knowledge` | 67 | 主题语料、高级词汇替换、句式结构、格式规范 |
| `scoring_criteria` | 51 | 分段评分标准、档次描述、扣分规则 |
| `common_errors` | 20 | 中式英语、语法、篇章逻辑、格式四类典型错误 |

按考试类别划分：英语一 138 块 / 英语二 127 块 / 通用 50 块。

## 技术栈

| 层 | 技术 |
| :--- | :--- |
| 后端服务 | Python · Flask · Flask-CORS |
| 模型调用 | OpenAI SDK（兼容 DeepSeek / Qwen / Kimi / GLM / Ollama） |
| 向量检索 | Milvus · Ollama `bge-m3` 嵌入 |
| 文档解析 | PyMuPDF · python-docx · RapidOCR(ONNX) · Pillow |
| 前端 | Vue 3 · Vite · lucide-vue-next · marked |
| 存储 | SQLite（用户体系）· Markdown（评卷报告） |

## 快速开始

### 前置依赖

- Python 3.12+
- Node.js 18+
- [Ollama](https://ollama.com/)（提供嵌入模型）
- [Milvus](https://milvus.io/)（可选，缺失时自动降级为本地检索）

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 拉取嵌入模型

```bash
ollama pull bge-m3
```

### 3. 启动 Milvus（可选）

```bash
docker run -d --name milvus-standalone -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest
```

### 4. 构建知识库索引并向量化

```bash
# 从原始知识库构建分块索引 → knowledge_base/index.json
python knowledge_base/kb_loader.py

# 生成嵌入向量并写入 Milvus
python rag/vectorizer.py
```

### 5. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少填入：

```ini
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

> 该 Key 仅供**命令行模式**使用。Web 界面出于安全设计，**强制要求每位用户在「评卷模型」设置中填入自己的 API Key**，不会借用服务端 `.env` 中的密钥。

### 6. 启动

**Web 模式**

```bash
python server.py                      # 后端 → http://127.0.0.1:5000

cd frontend
npm install
npm run dev                           # 前端 → http://127.0.0.1:5173
```

生产部署时改为 `npm run build`，产物输出到 `frontend/dist/`，由 Flask 直接托管，访问 `http://127.0.0.1:5000` 即可。

**命令行模式**

```bash
python main.py                                        # 交互式评卷
python main.py --file essay.txt --category 英语二      # 从文件评卷
python main.py --demo                                 # 运行真题案例对比演示
```

## API 接口

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| `GET` | `/api/status` | 系统状态与 Milvus 连接探活（60 秒缓存） |
| `GET` | `/api/llm/presets` | 可用大模型服务商预设列表 |
| `POST` | `/api/llm/test` | 测试指定模型的连通性 |
| `GET` | `/api/topics` | 历年真题题目列表 |
| `POST` | `/api/upload` | 上传作文文档并提取文本 |
| `POST` | `/api/evaluate` | 执行评卷，返回结构化评分 + Markdown 报告 |
| `GET` | `/api/essay-library` | 真题范文库，支持类别 / 年份 / 题型 / 关键词过滤 |
| `GET` | `/api/reports` | 历史评卷报告列表 |
| `GET` | `/api/report/<filename>` | 读取单篇报告内容 |

## 项目结构

```
EnglishTwoEvaluate/
├── main.py                 # 命令行入口（交互式 / 文件 / 演示）
├── server.py               # Flask Web 服务入口
├── agent/                  # 评卷核心链路
│   ├── evaluator.py        # 评分主流程、JSON 解析与容错修复
│   ├── preprocessor.py     # 词数统计、题型识别、规则初筛
│   ├── prompts.py          # 系统提示词与评分 Prompt 构建
│   ├── retriever 对接      # （见 rag/）
│   ├── llm_provider.py     # 多模型预设与连通性测试
│   ├── document_loader.py  # 多格式文档解析与 OCR
│   ├── report_generator.py # Markdown 报告生成与落盘
│   ├── config.py           # 模型配置读取
│   └── auth/               # 用户体系（JWT + 邮箱验证码 + SQLite）
├── rag/                    # 检索增强
│   ├── embedder.py         # Ollama 嵌入调用
│   ├── milvus_manager.py   # 集合管理、写入与检索
│   ├── vectorizer.py       # 知识库向量化入库
│   ├── retriever.py        # 四类知识检索 + 本地降级
│   └── test_rag.py         # 检索链路自测
├── knowledge_base/         # 知识库原始数据与分块索引
├── frontend/               # Vue 3 前端
│   └── src/components/     # 编辑器、维度评分、亮点扣分、历史抽屉等
├── scripts/                # 知识库样例构建脚本
└── evaluation_reports/     # 评卷报告输出目录（运行时生成）
```

## 部署注意事项

- **务必设置 `JWT_SECRET_KEY`** — [agent/auth/service.py](agent/auth/service.py) 中带有开发用的默认密钥。生产环境若沿用默认值，任何人都可伪造 token。
- **用户数据目录** — `data/*.db` 与 `evaluation_reports/` 含用户邮箱、密码哈希与作文原文，同样已排除在版本控制之外。
- **用户体系尚未接入 Web 路由** — `agent/auth/` 已实现注册、密码登录、验证码登录、重置密码与资料修改，但目前仅作为后端能力存在，`server.py` 尚未暴露 `/api/auth/*` 接口，前端也未接入。

## 许可

本项目仅供学习与研究使用。`knowledge_base/` 中的历年真题与范文材料版权归原权利人所有，请勿用于商业用途。
