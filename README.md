# AI Job Copilot

AI 求职助手 — 基于多 Agent 架构的智能求职全流程管理平台。

## 功能

- **👤 求职画像** — 上传简历 MinerU 解析，构建结构化画像和竞争力评分
- **💬 智能对话** — 多会话管理，SSE 流式响应，会话历史持久化
- **🎯 职位匹配** — 语义向量搜索，多维度匹配度评估
- **📄 简历优化** — 多版本管理，针对目标 JD 智能优化
- **📬 投递追踪** — 看板视图管理投递状态和统计数据
- **🎤 面试备战** — AI 生成面试问题，模拟评估回答质量
- **💬 情感支持** — RAG 检索相似经历，贯穿全流程鼓励

## 技术栈

| 层 | 选型 |
|---|------|
| 前端 | Vue.js 3 + Vite + Element Plus + Pinia |
| 后端 | FastAPI (Python 3.10) |
| Agent 编排 | LangGraph StateGraph (Plan-and-Execute) |
| Sub-Agent | LangChain `create_agent()` (ReAct) |
| Agent 通信 | Google A2A 协议 (JSON-RPC 2.0) |
| 文件解析 | MinerU (langchain-mineru) |
| 业务数据库 | PostgreSQL + pgvector |
| 向量存储 | Chroma + LangChain Chroma |
| 部署 | Docker Compose / 本地开发 |

## 架构

```
用户 → Vue.js SPA → SSE → FastAPI
                            │
                    ┌───────▼────────┐
                    │ Supervisor Agent│  Plan-and-Execute
                    └──┬───┬────┬────┘
                       │   │    │  A2A
              ┌────────┘   │    └──────────┐
              ▼            ▼              ▼
         Profile Agent  Matching Agent  Interview Agent
         (ReAct)        (ReAct)         (ReAct)
              │            │              │
              └────────────┼──────────────┘
                           │ call_support_agent
                           ▼
                      Support Agent (ReAct)
```

- **Supervisor**：Plan-and-Execute 模式，分析意图 → 分发 A2A 任务 → 汇总结果 → SSE 流式输出。不直接调用 Support。
- **Sub-Agent**：每个 Agent 独立 ReAct 循环，按需加载 SKILL (.md)，调用 TOOL。Agent 间仅传递结构化结果。
- **软连接**：系统在回复末尾给出下一步建议，最终由用户决定节奏。

## 快速开始

### 环境要求

- Python 3.10 + Anaconda (`conda activate langchain`)
- Docker Desktop
- Node.js 18+

### 方式一：本地开发（推荐）

```bash
# 一键启动（自动打开 6 个终端窗口）
./start_local.bat       # Windows
# ./start_local.sh      # macOS / Linux
```

脚本自动完成：启动 PostgreSQL + Chroma (Docker) → 4 个 Sub-Agent (8001-8004) → Supervisor (8080) → 前端 (3000)

### 方式二：Docker Compose

```bash
docker compose up -d

# 初始化数据库迁移
conda activate langchain
cd backend
alembic upgrade head
```

### 验证

```bash
# 健康检查
curl http://localhost:8080/health

# Agent 对话 (SSE 流式)
curl -X POST http://localhost:8080/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我看看我的简历"}'

# Agent Card
curl http://localhost:8001/.well-known/agent-card.json
```

## 配置

系统支持本地/Docker 双模式，通过环境变量 `AGENT_URLS` 切换：

| 模式 | AGENT_URLS | 说明 |
|------|-----------|------|
| 本地 | 不设置（默认 localhost） | 所有 Agent 在本地不同端口 |
| Docker | compose 自动注入 Docker 主机名 | 容器间通过 Docker DNS 通信 |

其他可配置项见 `backend/app/config.py`（数据库连接、LLM API Key 等）。

## API 端点

### 对话与会话

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/sessions` | GET/POST | 会话列表 / 新建会话 |
| `/api/sessions/{id}` | DELETE/PATCH | 删除 / 更新标题 |
| `/api/sessions/{id}/messages` | GET | 会话历史消息 |
| `/api/agent/chat` | POST | Agent 对话 (SSE 流式) |
| `/api/agent/chat/resume` | POST | 回复中断问题 |
| `/api/agent/parse-file` | POST | 上传简历 (MinerU 解析) |
| `/api/agent/parse-file/{id}` | DELETE | 删除已上传文件 |

### 业务 API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/profile` | GET/PUT | 求职画像 |
| `/api/resumes/upload` | POST | 上传简历 |
| `/api/resumes` | GET | 简历版本列表 |
| `/api/jobs` | POST | 录入职位 |
| `/api/jobs/{id}` | GET | 职位详情 |
| `/api/applications` | GET/POST | 投递记录 |
| `/api/applications/{id}` | PUT | 更新投递状态 |
| `/api/applications/stats` | GET | 统计数据 |

### A2A 协议

| 路径 | 方法 | 说明 |
|------|------|------|
| `/.well-known/agent-card.json` | GET | Agent Card 服务发现 |
| `/api/agent/registry` | GET/POST/DELETE | Agent 注册管理 |

## 项目结构

```
copilot/
├── docker-compose.yml
├── start_local.bat              # Windows 一键启动
├── start_local.sh               # macOS/Linux 一键启动
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # PostgreSQL 异步连接
│   │   ├── models/              # SQLAlchemy ORM (8个实体)
│   │   ├── api/                 # REST + SSE 接口
│   │   │   ├── agent.py         # /api/agent/* (对话+解析)
│   │   │   └── session.py       # /api/sessions/* (会话管理)
│   │   ├── agents/              # 5个Agent定义
│   │   │   ├── supervisor/      # Plan-and-Execute StateGraph
│   │   │   ├── profile/         # ReAct + A2A Server
│   │   │   ├── matching/        # ReAct + A2A Server
│   │   │   ├── interview/       # ReAct + A2A Server
│   │   │   └── support/         # ReAct + A2A Server
│   │   ├── a2a/                 # A2A 协议层 (JSON-RPC 2.0)
│   │   ├── skills/              # SKILL .md 文件 (8个)
│   │   ├── tools/               # TOOL 原子操作
│   │   ├── middleware/           # 自定义中间件
│   │   └── rag/                 # Chroma 向量存储
│   ├── alembic/                 # 数据库迁移
│   └── requirements.txt
├── frontend/                    # Vue.js SPA
│   └── src/
│       ├── views/               # 页面 (Chat/Profile/Resumes/...)
│       ├── stores/              # Pinia 状态管理
│       ├── api/                 # API 客户端
│       └── utils/               # 工具函数
└── data/                        # 种子数据
```

## License

MIT
