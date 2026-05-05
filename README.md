# AI Job Copilot

AI 求职助手 — 基于多 Agent 架构的智能求职全流程管理平台。

## 功能

- **👤 求职画像** — 上传简历自动解析，构建技能图谱和竞争力评分
- **📄 简历优化** — 多版本管理，针对目标 JD 智能优化
- **🎯 职位匹配** — 语义向量搜索，匹配度多维度评估
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
| 业务数据库 | PostgreSQL + pgvector |
| 向量存储 | Chroma + LangChain Chroma |
| AI 模型 | ChatOpenAI (gpt-5-mini) |
| 部署 | Docker Compose |

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

### 1. 启动服务

```bash
# 启动 PostgreSQL + Chroma + Backend + Frontend
docker compose up -d

# 初始化数据库迁移
conda activate langchain
cd backend
alembic upgrade head
```

### 2. 验证

```bash
# 健康检查
curl http://localhost:8080/health

# Agent 对话
curl -X POST http://localhost:8080/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我看看我和这个岗位的匹配度"}'
```

### 3. 开发

```bash
# 后端测试
conda activate langchain
cd backend
pytest tests/ -v

# 前端开发服务器
cd frontend
npm run dev
```

## 项目结构

```
copilot/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # PostgreSQL 异步连接
│   │   ├── models/              # SQLAlchemy ORM (6个实体)
│   │   ├── api/                 # REST + SSE 接口
│   │   ├── agents/              # 5个Agent定义
│   │   │   ├── supervisor/      # Plan-and-Execute StateGraph
│   │   │   ├── profile/         # ReAct + A2A Server
│   │   │   ├── matching/        # ReAct + A2A Server
│   │   │   ├── interview/       # ReAct + A2A Server
│   │   │   └── support/         # ReAct + A2A Server
│   │   ├── a2a/                 # A2A 协议层 (JSON-RPC 2.0)
│   │   ├── skills/              # SKILL .md 文件 (10个)
│   │   ├── tools/               # TOOL 原子操作 (8个)
│   │   ├── middleware/          # 自定义中间件
│   │   └── rag/                 # Chroma 向量存储
│   ├── tests/                   # 全部测试
│   └── alembic/                 # 数据库迁移
├── frontend/                    # Vue.js SPA
└── data/                        # 种子数据
```

## API 端点

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
| `/api/agent/chat` | POST | Agent 对话 (SSE) |
| `/api/agent/chat/resume` | POST | 回复中断问题 |
| `/api/agent/registry` | GET/POST | Agent 注册管理 |
| `/.well-known/agent-card.json` | GET | A2A Agent Card |

## License

MIT
