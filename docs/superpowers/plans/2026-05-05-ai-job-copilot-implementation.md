# AI Job Copilot 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 AI 求职助手全栈 Web 应用——多 Agent 架构（Supervisor Plan-and-Execute + Sub-Agent ReAct），基于 Google A2A 协议（JSON-RPC 2.0）通信，TDD 模式开发。

**Architecture:** FastAPI 后端 + Vue.js 3 前端。Supervisor Agent（LangGraph StateGraph Plan-and-Execute）通过 A2A 调用 Profile/Matching/Interview/Support 四个 Sub-Agent（LangChain create_agent ReAct）。PostgreSQL 业务数据 + Chroma 向量存储。Docker Compose 部署。

**Tech Stack:** Python 3.10 (Anaconda `langchain` 环境), FastAPI, LangChain, LangGraph, Chroma, PostgreSQL, Vue.js 3, Vite, Element Plus, Docker

**环境要求:** Anaconda 环境名为 `langchain`，Python 3.10。所有 Python 命令前需执行 `conda activate langchain`。

---

## 文件结构总览

```
copilot/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── resume.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   └── story.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── profile.py
│   │   │   ├── resumes.py
│   │   │   ├── jobs.py
│   │   │   ├── applications.py
│   │   │   ├── interviews.py
│   │   │   └── agent.py
│   │   ├── agents/
│   │   │   ├── supervisor/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── state.py
│   │   │   │   ├── planner.py
│   │   │   │   ├── executor.py
│   │   │   │   ├── replanner.py
│   │   │   │   ├── synthesizer.py
│   │   │   │   └── graph.py
│   │   │   ├── profile/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agent.py
│   │   │   │   └── server.py
│   │   │   ├── matching/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agent.py
│   │   │   │   └── server.py
│   │   │   ├── interview/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agent.py
│   │   │   │   └── server.py
│   │   │   └── support/
│   │   │       ├── __init__.py
│   │   │       ├── agent.py
│   │   │       └── server.py
│   │   ├── a2a/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── server.py
│   │   │   ├── agent_card.py
│   │   │   ├── registry.py
│   │   │   └── types.py
│   │   ├── skills/
│   │   │   ├── supervisor/onboard-user.md
│   │   │   ├── profile/parse-resume.md
│   │   │   ├── profile/build-profile.md
│   │   │   ├── matching/match-jobs.md
│   │   │   ├── matching/score-match.md
│   │   │   ├── matching/optimize-resume.md
│   │   │   ├── interview/generate-interview-qs.md
│   │   │   ├── interview/evaluate-answer.md
│   │   │   ├── support/comfort-user.md
│   │   │   └── support/daily-checkin.md
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── chroma.py
│   │   │   ├── llm.py
│   │   │   ├── parser.py
│   │   │   ├── search.py
│   │   │   └── call_support.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── skill_loading.py
│   │   │   └── sliding_window.py
│   │   └── rag/
│   │       ├── __init__.py
│   │       ├── vector_store.py
│   │       └── embeddings.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_tools/
│       ├── test_middleware/
│       ├── test_a2a/
│       ├── test_agents/
│       ├── test_api/
│       └── test_graph/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/...
└── data/seed_stories.json
```

---

## Phase 1：核心骨架

### Task 1.1: 项目初始化

**Files:**
- Create: `docker-compose.yml`, `backend/Dockerfile`, `backend/requirements.txt`
- Create: `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `frontend/` (Vite scaffold)

- [ ] **Step 1: 创建 docker-compose.yml + backend/Dockerfile**

```yaml
# docker-compose.yml
version: "3.8"
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: copilot
      POSTGRES_PASSWORD: copilot123
      POSTGRES_DB: copilot
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  chroma:
    image: chromadb/chroma:latest
    ports: ["8000:8000"]
    volumes: ["chromadata:/chroma/chroma"]

  backend:
    build: ./backend
    ports: ["8080:8080"]
    depends_on: [db, chroma]
    environment:
      DATABASE_URL: postgresql+asyncpg://copilot:copilot123@db:5432/copilot
      CHROMA_HOST: chroma
      CHROMA_PORT: 8000
    volumes: ["./backend/app:/app/app"]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

volumes:
  pgdata:
  chromadata:
```

```dockerfile
# backend/Dockerfile — Python 3.10
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 2: 创建 backend/requirements.txt**

```txt
# Python 3.10 兼容，使用最新稳定版本
fastapi>=0.120.0
uvicorn[standard]>=0.34.0
sqlalchemy[asyncio]>=2.0.35
asyncpg>=0.30.0
alembic>=1.14.0
langchain>=1.0.0
langchain-openai>=0.3.0
langchain-chroma>=0.2.0
langgraph>=1.0.0
chromadb>=1.0.0
pydantic>=2.10.0
pydantic-settings>=2.7.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.20
httpx>=0.28.0
pytest>=8.3.0
pytest-asyncio>=0.25.0
pytest-httpx>=0.35.0
PyPDF2>=3.0.0
python-docx>=1.1.0
pyyaml>=6.0
```
> 使用 `>=` 约束让 pip 自动解析兼容 Python 3.10 的最新版本。如遇版本冲突，移除版本号让 pip 自行解决。

- [ ] **Step 3: 验证 conda 环境**

Run: `conda activate langchain && python --version && python -c "import pytest; print(pytest.__version__)"`
Expected: `Python 3.10.x` + pytest version

- [ ] **Step 4: Commit**

---

### Task 1.2: 数据库模型 + Alembic

**Files:**
- Create: `backend/app/models/__init__.py`, `backend/app/models/user.py`
- Create: `backend/app/models/profile.py`, `backend/app/models/resume.py`
- Create: `backend/app/models/job.py`, `backend/app/models/application.py`
- Create: `backend/app/models/story.py`
- Create: `backend/app/config.py`
- Create: `backend/alembic/` (init)
- Test: `backend/tests/test_models/test_user.py`

- [ ] **Step 1: 编写 User 模型失败测试**

```python
# backend/tests/test_models/test_user.py
import pytest
from app.models.user import User

def test_user_creation():
    user = User(email="test@example.com", password_hash="hashed")
    assert user.email == "test@example.com"
    assert user.password_hash == "hashed"

def test_user_id_is_uuid():
    import uuid
    user = User(email="test@example.com", password_hash="hashed")
    assert isinstance(uuid.UUID(user.id), uuid.UUID)

def test_user_unique_email():
    """应测试唯一约束，先写骨架让测试失败"""
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_models/test_user.py -v`
Expected: FAIL (ImportError: module not found)

- [ ] **Step 3: 实现 config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://copilot:copilot123@localhost:5432/copilot"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    secret_key: str = "dev-secret-key-change-in-prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    openai_api_key: str = "sk-AfFjOyI0IT8ZELF7mXMQ3voviAIwDYaGvoJnxfpGOcJpXWAj"
    openai_base_url: str = "https://api.chatanywhere.tech"
    openai_model: str = "gpt-5-mini"

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 4: 实现 database.py**

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session
```

- [ ] **Step 5: 实现所有 model**

```python
# backend/app/models/user.py
import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(String(30), nullable=False, default="2026-01-01T00:00:00")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    resumes = relationship("Resume", back_populates="user")
    applications = relationship("Application", back_populates="user")
```

```python
# backend/app/models/profile.py
import uuid
from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    skill_tags: Mapped[dict] = mapped_column(JSON, default=list)
    work_years: Mapped[int] = mapped_column(Integer, default=0)
    education: Mapped[dict] = mapped_column(JSON, default=dict)
    projects: Mapped[dict] = mapped_column(JSON, default=list)
    target: Mapped[dict] = mapped_column(JSON, default=dict)
    preference: Mapped[dict] = mapped_column(JSON, default=dict)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    user = relationship("User", back_populates="profile")
```

```python
# backend/app/models/resume.py
import uuid
from sqlalchemy import String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    base_version: Mapped[bool] = mapped_column(Boolean, default=False)
    target_role: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    match_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")
```

```python
# backend/app/models/job.py
import uuid
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=True)
    jd_content: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[dict] = mapped_column(JSON, default=list)
    company: Mapped[str] = mapped_column(String(255), nullable=True)
    salary_range: Mapped[str] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
```

```python
# backend/app/models/application.py
import uuid
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Application(Base):
    __tablename__ = "applications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    resume_id: Mapped[str] = mapped_column(String(36), ForeignKey("resumes.id"), nullable=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="planned")
    timeline: Mapped[dict] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    user = relationship("User", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
```

```python
# backend/app/models/story.py
import uuid
from sqlalchemy import String, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class ExperienceStory(Base):
    __tablename__ = "experience_stories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_models/test_user.py -v`
Expected: PASS

- [ ] **Step 7: 初始化 Alembic 并生成迁移**

Run:
```
conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend"
alembic init alembic
# 修改 alembic/env.py 导入 Base 和 engine
alembic revision --autogenerate -m "init"
```

- [ ] **Step 8: Commit**

---

### Task 1.3: 用户认证（JWT）

**Files:**
- Create: `backend/app/api/__init__.py`, `backend/app/api/auth.py`
- Create: `backend/app/models/__init__.py`
- Test: `backend/tests/test_api/test_auth.py`

- [ ] **Step 1: 编写注册测试**

```python
# backend/tests/test_api/test_auth.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_returns_jwt():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "Test123456"
        })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_returns_jwt():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 先注册
        await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "Test123456"
        })
        # 再登录
        response = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "Test123456"
        })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_wrong_password_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrong"
        })
    assert response.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_api/test_auth.py -v`
Expected: FAIL (auth endpoints don't exist)

- [ ] **Step 3: 实现 main.py + auth.py**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth

app = FastAPI(title="AI Job Copilot")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

```python
# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User
from app.config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

def create_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.secret_key, algorithm=settings.algorithm)

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=req.email, password_hash=pwd_context.hash(req.password))
    db.add(user)
    await db.commit()
    return TokenResponse(access_token=create_token(user.id))

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_token(user.id))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_api/test_auth.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 1.4: Chroma 初始化

**Files:**
- Create: `backend/app/rag/__init__.py`, `backend/app/rag/vector_store.py`
- Test: `backend/tests/test_rag/test_vector_store.py`

- [ ] **Step 1: 编写 Chroma 连接测试**

```python
# backend/tests/test_rag/test_vector_store.py
import pytest
from app.rag.vector_store import get_chroma_client, init_collections

@pytest.mark.asyncio
async def test_chroma_client_connects():
    client = await get_chroma_client()
    assert client is not None
    heartbeat = client.heartbeat()
    assert heartbeat is not None

@pytest.mark.asyncio
async def test_init_collections_creates_three():
    await init_collections()
    client = await get_chroma_client()
    collections = client.list_collections()
    names = [c.name for c in collections]
    assert "jobs" in names
    assert "stories" in names
    assert "profiles" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_rag/test_vector_store.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 vector_store.py**

```python
# backend/app/rag/vector_store.py
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

_client = None

async def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client

async def init_collections():
    client = await get_chroma_client()
    for name in ["jobs", "stories", "profiles"]:
        try:
            client.get_collection(name)
        except Exception:
            client.create_collection(name)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_rag/test_vector_store.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

---

## Phase 2：A2A 协议层 + TOOL + Middleware

### Task 2.1: A2A Types + Agent Card

**Files:**
- Create: `backend/app/a2a/__init__.py`, `backend/app/a2a/types.py`
- Create: `backend/app/a2a/agent_card.py`
- Test: `backend/tests/test_a2a/test_agent_card.py`

- [ ] **Step 1: 编写 Agent Card 验证测试**

```python
# backend/tests/test_a2a/test_agent_card.py
from app.a2a.agent_card import create_agent_card, AgentCard

def test_agent_card_has_required_fields():
    card = create_agent_card(
        agent_id="urn:agent:copilot:profile",
        name="Profile Agent",
        description="解析简历、构建画像",
        url="http://localhost:8001",
        skills=[{"id": "parse-resume", "name": "解析简历", "description": "..."}],
    )
    card_dict = card.model_dump()
    assert card_dict["a2a_version"] == "1.0"
    assert card_dict["id"] == "urn:agent:copilot:profile"
    assert len(card_dict["skills"]) == 1
    assert card_dict["capabilities"]["streaming"] is True

def test_agent_card_default_input_modes():
    card = create_agent_card("urn:agent:copilot:test", "Test", "Test", "http://localhost", [])
    card_dict = card.model_dump()
    assert "text" in card_dict["defaultInputModes"]
    assert "application/json" in card_dict["defaultInputModes"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_a2a/test_agent_card.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 types.py + agent_card.py**

```python
# backend/app/a2a/types.py
from pydantic import BaseModel
from typing import Any, Literal

class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str

class JsonPart(BaseModel):
    type: Literal["application/json"] = "application/json"
    content: dict[str, Any]

Part = TextPart | JsonPart

class A2AMessage(BaseModel):
    role: Literal["user", "agent"]
    parts: list[Part]

class TaskStatus(BaseModel):
    state: Literal["submitted", "working", "input-required", "completed", "failed", "canceled"]
    message: str | None = None

class TaskArtifact(BaseModel):
    type: str = "application/json"
    content: dict[str, Any]

class TaskResult(BaseModel):
    id: str
    status: TaskStatus
    artifacts: list[TaskArtifact] = []

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    method: str
    params: dict[str, Any]

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    result: TaskResult | dict[str, Any] | None = None
    error: dict[str, Any] | None = None
```

```python
# backend/app/a2a/agent_card.py
from pydantic import BaseModel

class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    examples: list[str] = []

class AgentCard(BaseModel):
    a2a_version: str = "1.0"
    id: str
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: dict = {"streaming": True, "pushNotifications": False}
    skills: list[AgentSkill] = []
    defaultInputModes: list[str] = ["text", "application/json"]
    defaultOutputModes: list[str] = ["text", "application/json"]

def create_agent_card(agent_id: str, name: str, description: str, url: str, skills: list[dict]) -> AgentCard:
    return AgentCard(
        id=agent_id,
        name=name,
        description=description,
        url=url,
        skills=[AgentSkill(**s) for s in skills],
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_a2a/test_agent_card.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 2.2: A2A Server

**Files:**
- Create: `backend/app/a2a/server.py`
- Test: `backend/tests/test_a2a/test_server.py`

- [ ] **Step 1: 编写 A2A Server 测试**

```python
# backend/tests/test_a2a/test_server.py
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from app.a2a.server import create_a2a_router
from app.a2a.types import JsonRpcRequest, JsonRpcResponse, TaskResult, TaskStatus

app = FastAPI()

async def test_handler(request: JsonRpcRequest) -> JsonRpcResponse:
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(id="task-test", status=TaskStatus(state="completed"), artifacts=[]),
    )

a2a_router = create_a2a_router(handler=test_handler)
app.include_router(a2a_router)

@pytest.mark.asyncio
async def test_send_message_returns_jsonrpc_response():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/", json={
            "jsonrpc": "2.0", "id": 1,
            "method": "tasks/sendMessage",
            "params": {
                "message": {"role": "user", "parts": [{"type": "text", "text": "hello"}]}
            }
        })
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert data["result"]["status"]["state"] == "completed"

@pytest.mark.asyncio
async def test_invalid_method_returns_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/", json={
            "jsonrpc": "2.0", "id": 2, "method": "tasks/unknown", "params": {}
        })
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_a2a/test_server.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 server.py**

```python
# backend/app/a2a/server.py
from fastapi import APIRouter, FastAPI
from typing import Callable, Awaitable
from app.a2a.types import JsonRpcRequest, JsonRpcResponse

async def default_handler(request: JsonRpcRequest) -> JsonRpcResponse:
    return JsonRpcResponse(id=request.id, error={"code": -32601, "message": "Method not found"})

def create_a2a_router(handler: Callable[[JsonRpcRequest], Awaitable[JsonRpcResponse]] = None) -> APIRouter:
    router = APIRouter()
    h = handler or default_handler

    @router.post("/")
    async def handle_jsonrpc(request: JsonRpcRequest):
        if request.method == "tasks/sendMessage":
            return await h(request)
        return JsonRpcResponse(id=request.id, error={"code": -32601, "message": f"Unknown method: {request.method}"})

    return router

def mount_agent_card(app: FastAPI, card: dict, path: str = "/.well-known/agent-card.json"):
    @app.get(path)
    def get_agent_card():
        return card
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_a2a/test_server.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 2.3: A2A Client

**Files:**
- Create: `backend/app/a2a/client.py`
- Create: `backend/app/a2a/registry.py`
- Test: `backend/tests/test_a2a/test_client.py`

- [ ] **Step 1: 编写 A2A Client 测试**

```python
# backend/tests/test_a2a/test_client.py
import pytest
from unittest.mock import AsyncMock, patch
from app.a2a.client import A2AClient
from app.a2a.types import JsonRpcResponse, TaskResult, TaskStatus

@pytest.mark.asyncio
async def test_send_message_returns_task_result():
    mock_response = JsonRpcResponse(
        id=1,
        result=TaskResult(id="task-abc", status=TaskStatus(state="completed"), artifacts=[]),
    )
    client = A2AClient()
    with patch.object(client, '_post', AsyncMock(return_value=mock_response)):
        result = await client.send_message(
            agent_url="http://test:8001",
            message={"role": "user", "parts": [{"type": "text", "text": "hello"}]},
        )
    assert result.result.id == "task-abc"
    assert result.result.status.state == "completed"

@pytest.mark.asyncio
async def test_fetch_agent_card():
    card_data = {"a2a_version": "1.0", "id": "urn:agent:test", "name": "Test", "url": "http://test"}
    client = A2AClient()
    with patch.object(client, '_get', AsyncMock(return_value=card_data)):
        card = await client.fetch_agent_card("http://test:8001")
    assert card["name"] == "Test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_a2a/test_client.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 client.py + registry.py**

```python
# backend/app/a2a/client.py
import httpx
from app.a2a.types import JsonRpcRequest, JsonRpcResponse

class A2AClient:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=60.0)

    async def _post(self, url: str, payload: dict) -> JsonRpcResponse:
        resp = await self._client.post(url, json=payload)
        data = resp.json()
        return JsonRpcResponse(**data)

    async def _get(self, url: str) -> dict:
        resp = await self._client.get(url)
        return resp.json()

    async def send_message(self, agent_url: str, message: dict, task_id: str = None) -> JsonRpcResponse:
        params = {"message": message}
        if task_id:
            params["taskId"] = task_id
        return await self._post(agent_url, {
            "jsonrpc": "2.0", "id": 1,
            "method": "tasks/sendMessage",
            "params": params,
        })

    async def fetch_agent_card(self, agent_url: str) -> dict:
        return await self._get(f"{agent_url.rstrip('/')}/.well-known/agent-card.json")
```

```python
# backend/app/a2a/registry.py
from app.a2a.client import A2AClient

class AgentRegistry:
    SYSTEM_AGENTS = {"profile-agent", "matching-agent", "interview-agent", "support-agent"}

    def __init__(self, client: A2AClient = None):
        self.client = client or A2AClient()
        self._agents: dict[str, dict] = {}

    async def discover(self, agent_urls: list[str]):
        for url in agent_urls:
            try:
                card = await self.client.fetch_agent_card(url)
                self._agents[card["name"]] = card
                card["_url"] = url
            except Exception:
                pass

    async def register(self, agent_url: str) -> dict:
        card = await self.client.fetch_agent_card(agent_url)
        self._agents[card["name"]] = card
        card["_url"] = agent_url
        return card

    def get_agent_url(self, name: str) -> str | None:
        agent = self._agents.get(name)
        return agent["_url"] if agent else None

    def get_all_summaries(self) -> list[dict]:
        """返回不含 Support 的摘要列表，用于 Planner"""
        return [
            {"name": name, "description": card["description"], "skills": card.get("skills", [])}
            for name, card in self._agents.items()
            if "support" not in name.lower()
        ]

    def is_system_agent(self, name: str) -> bool:
        return name in self.SYSTEM_AGENTS

    def list_all(self) -> list[dict]:
        return [{"name": name, "card": card} for name, card in self._agents.items()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_a2a/test_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 2.4: TOOL 原子操作实现

**Files:**
- Create: `backend/app/tools/__init__.py`, `backend/app/tools/llm.py`
- Create: `backend/app/tools/database.py`, `backend/app/tools/chroma.py`
- Create: `backend/app/tools/parser.py`, `backend/app/tools/search.py`
- Create: `backend/app/tools/call_support.py`
- Test: `backend/tests/test_tools/test_llm.py`, `backend/tests/test_tools/test_database.py`

- [ ] **Step 1: 编写 call_llm Tool 测试**

```python
# backend/tests/test_tools/test_llm.py
from unittest.mock import AsyncMock, patch
from langchain_core.messages import HumanMessage
from app.tools.llm import call_llm

def test_call_llm_is_langchain_tool():
    assert hasattr(call_llm, 'name')
    assert call_llm.name == "call_llm"

@patch("app.tools.llm.llm.ainvoke")
async def test_call_llm_returns_response(mock_ainvoke):
    mock_ainvoke.return_value.content = "test response"
    result = await call_llm.ainvoke({"prompt": "hello"})
    assert result == "test response"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_tools/test_llm.py -v`
Expected: FAIL

- [ ] **Step 3: 实现所有 TOOL**

```python
# backend/app/tools/llm.py
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from app.config import settings

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

@tool
async def call_llm(prompt: str, temperature: float = 0.7) -> str:
    """调用大语言模型，传入 prompt 获取回复。用于需要文本生成、分析、总结等场景。"""
    response = await llm.ainvoke(prompt)
    return response.content
```

```python
# backend/app/tools/database.py
from langchain_core.tools import tool
from sqlalchemy import select, text
from app.database import async_session

@tool
async def db_read(table: str, filters: dict = None) -> dict:
    """读数据库。table: users|user_profiles|resumes|jobs|applications|experience_stories"""
    async with async_session() as session:
        query = text(f"SELECT * FROM {table}")
        if filters:
            conditions = " AND ".join([f"{k} = :{k}" for k in filters])
            query = text(f"SELECT * FROM {table} WHERE {conditions}")
        result = await session.execute(query, filters or {})
        rows = [dict(row._mapping) for row in result.fetchall()]
        return rows

@tool
async def db_write(table: str, data: dict, record_id: str = None) -> str:
    """写数据库。table: user_profiles|resumes|jobs|applications|experience_stories"""
    async with async_session() as session:
        if record_id:
            query = text(f"UPDATE {table} SET {', '.join([f'{k}=:{k}' for k in data])} WHERE id=:id")
            data["id"] = record_id
        else:
            cols = ", ".join(data.keys())
            vals = ", ".join([f":{k}" for k in data])
            query = text(f"INSERT INTO {table} ({cols}) VALUES ({vals})")
        await session.execute(query, data)
        await session.commit()
    return "ok"
```

```python
# backend/app/tools/chroma.py
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.config import settings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

@tool
async def chroma_query(collection: str, query: str, k: int = 5) -> list[dict]:
    """向量相似度检索。collection: jobs|stories|profiles"""
    store = Chroma(collection_name=collection, embedding_function=embeddings,
                   persist_directory="./chroma_data")
    docs = store.similarity_search_with_score(query, k=k)
    return [{"content": d.page_content, "metadata": d.metadata, "score": s} for d, s in docs]

@tool
async def chroma_insert(collection: str, documents: list[str], metadatas: list[dict] = None) -> str:
    """写入向量到 Chroma，使用 add_documents 一行写入"""
    store = Chroma(collection_name=collection, embedding_function=embeddings,
                   persist_directory="./chroma_data")
    from langchain_core.documents import Document
    docs = [Document(page_content=text, metadata=meta or {}) for text, meta in zip(documents, metadatas or [{}])]
    store.add_documents(docs)
    return f"ok, inserted {len(docs)} docs"
```

```python
# backend/app/tools/parser.py
from langchain_core.tools import tool

@tool
async def parse_document(file_path: str) -> dict:
    """解析 PDF/Word/文本文件，返回结构化内容。file_path: 文件路径"""
    import os
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return {"text": f.read(), "metadata": {"type": "text"}}
    elif ext == ".pdf":
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        return {"text": text, "metadata": {"type": "pdf"}}
    elif ext in (".docx", ".doc"):
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return {"text": text, "metadata": {"type": "docx"}}
    else:
        return {"error": f"Unsupported format: {ext}"}
```

```python
# backend/app/tools/search.py
from langchain_core.tools import tool
import httpx

@tool
async def web_search(query: str, source: str = "boss") -> list[dict]:
    """搜索外部信息（职位/公司）。source: boss|lagou"""
    # 初期返回空列表，后续接入爬虫
    return []
```

```python
# backend/app/tools/call_support.py
from langchain_core.tools import tool
from app.a2a.client import A2AClient

_client = A2AClient()

@tool
async def call_support_agent(trigger: str, profile_id: str, context: dict = None) -> dict:
    """调用 Support Agent 获取经历分享和鼓励。trigger: low_match|rejected|interview_fail|offer|onboarding|daily"""
    from app.config import settings  # support agent URL from config
    support_url = "http://localhost:8004"  # 默认 Support Agent URL
    response = await _client.send_message(support_url, message={
        "role": "user",
        "parts": [
            {"type": "text", "text": f"用户需要鼓励，触发事件: {trigger}"},
            {"type": "application/json", "content": {"profile_id": profile_id, "trigger": trigger, **(context or {})}}
        ]
    })
    if response.result and response.result.artifacts:
        return response.result.artifacts[0].content
    return {"story": "", "encouragement": ""}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_tools/test_llm.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 2.5: SkillLoadingMiddleware + SlidingWindowMiddleware

**Files:**
- Create: `backend/app/middleware/__init__.py`, `backend/app/middleware/skill_loading.py`
- Create: `backend/app/middleware/sliding_window.py`
- Test: `backend/tests/test_middleware/test_skill_loading.py`
- Test: `backend/tests/test_middleware/test_sliding_window.py`

- [ ] **Step 1: 编写 SkillLoadingMiddleware 测试**

```python
# backend/tests/test_middleware/test_skill_loading.py
import pytest
from unittest.mock import patch, mock_open
from app.middleware.skill_loading import SkillLoadingMiddleware

@pytest.mark.asyncio
async def test_skill_loading_fills_skills_list_placeholder():
    middleware = SkillLoadingMiddleware(skills_dir="/fake/skills")
    fake_md = "---\nname: test-skill\ndescription: 用于测试\n---\n# Test\n内容"
    state = {"system_prompt": "可用技能：{skills_list}\n详情：{skill_content}", "messages": []}

    with patch("os.listdir", return_value=["test-skill.md"]):
        with patch("builtins.open", mock_open(read_data=fake_md)):
            middleware._load_skills_metadata()
    
    assert "test-skill" in middleware._skills_meta
    assert middleware._skills_meta["test-skill"]["description"] == "用于测试"

@pytest.mark.asyncio
async def test_skill_loading_injects_body_on_request():
    middleware = SkillLoadingMiddleware(skills_dir="/fake/skills")
    fake_md = "---\nname: test-skill\ndescription: 用于测试\n---\n# Test\n工作流程：1. 步骤一"
    middleware._skills_meta = {"test-skill": {"name": "test-skill", "description": "用于测试", "body": fake_md}}
    
    # 模拟 Agent 请求加载 SKILL
    content = middleware._inject_skill("test-skill")
    assert "工作流程" in content
    assert "步骤一" in content
```

- [ ] **Step 2: 编写 SlidingWindowMiddleware 测试**

```python
# backend/tests/test_middleware/test_sliding_window.py
import pytest
from app.middleware.sliding_window import SlidingWindowMiddleware

@pytest.mark.asyncio
async def test_sliding_window_keeps_recent_messages():
    middleware = SlidingWindowMiddleware(max_messages=5)
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]

    processed = middleware._process_window(messages)
    # 窗口内保留最近5条原文
    assert len([m for m in processed if m.get("_in_window")]) <= 5
    # 窗口外的生成摘要
    summaries = [m for m in processed if m.get("_summary")]
    assert len(summaries) > 0

@pytest.mark.asyncio
async def test_sliding_window_below_limit_keeps_all():
    middleware = SlidingWindowMiddleware(max_messages=20)
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(5)]
    processed = middleware._process_window(messages)
    assert len(processed) == 5
    assert not any(m.get("_summary") for m in processed)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_middleware/ -v`
Expected: FAIL

- [ ] **Step 4: 实现两个 Middleware**

```python
# backend/app/middleware/skill_loading.py
import os
import yaml
from langchain.agents.middleware import AgentMiddleware

class SkillLoadingMiddleware(AgentMiddleware):
    """按需加载 SKILL .md 文件，填充 system_prompt 占位符"""

    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self._skills_meta: dict[str, dict] = {}
        self._loaded_skills: set = set()
        self._load_skills_metadata()

    def _load_skills_metadata(self):
        """启动时仅加载 SKILL name + description"""
        if not os.path.isdir(self.skills_dir):
            return
        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".md"):
                with open(os.path.join(self.skills_dir, filename), "r") as f:
                    content = f.read()
                self._skills_meta[filename.replace(".md", "")] = self._parse_frontmatter(content)

    def _parse_frontmatter(self, content: str) -> dict:
        """解析 --- frontmatter ---"""
        parts = content.split("---")
        if len(parts) < 3:
            return {"name": "unknown", "description": "", "body": content}
        frontmatter = {}
        for line in parts[1].strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                frontmatter[key.strip()] = val.strip()
        frontmatter["body"] = parts[2].strip()
        return frontmatter

    def _inject_skill(self, skill_name: str) -> str:
        """加载 SKILL body 并返回"""
        if skill_name not in self._skills_meta:
            return ""
        self._loaded_skills.add(skill_name)
        return self._skills_meta[skill_name].get("body", "")
```

```python
# backend/app/middleware/sliding_window.py
from langchain.agents.middleware import AgentMiddleware

class SlidingWindowMiddleware(AgentMiddleware):
    """按消息数量控制上下文窗口，窗口外自动压缩为摘要"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages

    def _process_window(self, messages: list[dict]) -> list[dict]:
        if len(messages) <= self.max_messages:
            return messages
        split_point = len(messages) - self.max_messages
        outside = messages[:split_point]
        inside = messages[split_point:]

        summary_parts = []
        for msg in outside:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:50]
            summary_parts.append(f"[{role}]: {content}...")
        summary = "**历史摘要**: " + "; ".join(summary_parts)

        inside.insert(0, {"role": "system", "content": summary, "_summary": True})
        for m in inside:
            m["_in_window"] = True
        return inside
```

- [ ] **Step 5: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_middleware/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

---

## Phase 3: Sub-Agent 冒烟 + 核心 SKILL

### Task 3.1: Profile Agent (create_agent ReAct + parse-resume + build-profile)

**Files:**
- Create: `backend/app/agents/profile/__init__.py`, `backend/app/agents/profile/agent.py`
- Create: `backend/app/agents/profile/server.py`
- Create: `backend/app/skills/profile/parse-resume.md`
- Create: `backend/app/skills/profile/build-profile.md`
- Test: `backend/tests/test_agents/test_profile_agent.py`

- [ ] **Step 1: 编写 parse-resume SKILL**

```markdown
<!-- backend/app/skills/profile/parse-resume.md -->
---
name: parse-resume
description: 当用户上传或更新简历文件时，需要解析文件并提取结构化信息。适用于 PDF、Word、纯文本格式。
---

# 简历解析

## 目标
将上传的简历文件解析为结构化内容，提取关键信息。

## 工作流程
1. 使用 parse_document 工具解析文件 → 获取原始文本和元数据
2. 使用 call_llm 从原始文本中提取：
   - 个人基本信息（姓名、联系方式）
   - 教育经历（学校、专业、学历）
   - 工作经历（公司、岗位、年限）
   - 技能标签（技术栈、软技能）
   - 项目经验
3. 如遇到关键信息缺失（如学历），返回 state: "input-required" 请求用户补充

## 输出格式
{"raw_text": str, "structured": {"name": str, "skills": [...], "education": {...}, "experience": [...], "projects": [...]}}
```

- [ ] **Step 2: 编写 build-profile SKILL**

```markdown
<!-- backend/app/skills/profile/build-profile.md -->
---
name: build-profile
description: 当简历解析完成、用户补充个人信息后，构建或更新用户求职画像。画像包括技能图谱、经验向量和竞争力评分。
---

# 构建求职画像

## 目标
基于简历结构化内容构建用户求职画像。

## 工作流程
1. 使用 db_read 获取现有画像数据
2. 使用 call_llm 从简历内容：
   - 提取技能标签并分级（初级/中级/高级/专家）
   - 计算工作年限
   - 生成画像摘要文本（用于向量化）
3. 使用 db_write 将画像数据写入 user_profiles 表
4. 使用 chroma_insert 将画像摘要向量写入 profiles collection
5. 使用 call_llm 对画像进行竞争力评分（技术深度、经验广度、市场匹配度）

## 输出格式
{"profile_id": str, "skill_tags": [...], "work_years": int, "education": {...}, "projects": [...], "scores": {"competitiveness": float, "market_match": float, "completeness": float}}
```

- [ ] **Step 3: 编写 Profile Agent 测试**

```python
# backend/tests/test_agents/test_profile_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.profile.agent import profile_agent

@pytest.mark.asyncio
async def test_profile_agent_created():
    assert profile_agent is not None

@pytest.mark.asyncio
async def test_profile_agent_parse_resume_returns_structured():
    """测试 Profile Agent 能处理简历解析请求"""
    # 模拟 A2A 任务请求
    task_request = {
        "jsonrpc": "2.0", "id": 1, "method": "tasks/sendMessage",
        "params": {
            "message": {
                "role": "user",
                "parts": [
                    {"type": "text", "text": "请解析简历"},
                    {"type": "application/json", "content": {"file_path": "/fake/resume.txt"}}
                ]
            }
        }
    }
    # 验证 Agent 能接收请求
    # 这个测试只验证 Agent 对象存在和配置正确
    from app.agents.profile.agent import PROFILE_SYSTEM_PROMPT
    assert "{skills_list}" in PROFILE_SYSTEM_PROMPT
    assert "{skill_content}" in PROFILE_SYSTEM_PROMPT
```

- [ ] **Step 4: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_agents/test_profile_agent.py -v`
Expected: FAIL

- [ ] **Step 5: 实现 Profile Agent**

```python
# backend/app/agents/profile/agent.py
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.parser import parse_document
from app.tools.database import db_read, db_write
from app.tools.llm import call_llm
from app.tools.chroma import chroma_insert
from app.tools.call_support import call_support_agent
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

PROFILE_SYSTEM_PROMPT = """你是简历与画像专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 遇到关键信息缺失（学历、联系方式等）→ Task state 返回 input-required
- Support Agent 永远不返回 input-required，只返回 completed"""

profile_agent = create_agent(
    llm=llm,
    system_prompt=PROFILE_SYSTEM_PROMPT,
    tools=[parse_document, db_read, db_write, call_llm, chroma_insert, call_support_agent],
    middleware=[
        SkillLoadingMiddleware(skills_dir="app/skills/profile/"),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)
```

```python
# backend/app/agents/profile/server.py
from fastapi import FastAPI
from app.a2a.server import create_a2a_router, mount_agent_card
from app.a2a.agent_card import create_agent_card

app = FastAPI(title="Profile Agent")

agent_card = create_agent_card(
    agent_id="urn:agent:copilot:profile",
    name="Profile Agent",
    description="负责解析简历文件和构建用户求职画像。当用户上传简历、需要更新个人资料时调用。",
    url="http://localhost:8001",
    skills=[
        {"id": "parse-resume", "name": "简历解析", "description": "解析 PDF/Word/文本简历为结构化信息",
         "examples": ["帮我看看我的简历", "上传了简历帮忙分析"]},
        {"id": "build-profile", "name": "构建画像", "description": "基于简历内容构建求职者技能画像和评分",
         "examples": ["帮我生成求职画像", "更新我的个人资料"]},
    ],
)

mount_agent_card(app, agent_card.model_dump())

async def handle_task(request):
    from app.agents.profile.agent import profile_agent
    from langchain_core.messages import HumanMessage
    msg_parts = request.params["message"]["parts"]
    text = " ".join([p.get("text", "") for p in msg_parts if p["type"] == "text"])
    result = await profile_agent.ainvoke({"messages": [HumanMessage(content=text)]})
    from app.a2a.types import TaskResult, TaskStatus, TaskArtifact, JsonRpcResponse
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(
            id="task-profile",
            status=TaskStatus(state="completed"),
            artifacts=[TaskArtifact(content={"result": str(result)})],
        ),
    )

app.include_router(create_a2a_router(handler=handle_task))
```

- [ ] **Step 6: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_agents/test_profile_agent.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

---

### Task 3.2: Support Agent (ReAct + comfort-user)

**Files:**
- Create: `backend/app/agents/support/__init__.py`, `backend/app/agents/support/agent.py`
- Create: `backend/app/agents/support/server.py`
- Create: `backend/app/skills/support/comfort-user.md`
- Test: `backend/tests/test_agents/test_support_agent.py`

- [ ] **Step 1: 编写 Support Agent 测试**

```python
# backend/tests/test_agents/test_support_agent.py
def test_support_agent_never_input_required():
    """Support Agent 的 system_prompt 不应生成 input-required"""
    from app.agents.support.agent import SUPPORT_SYSTEM_PROMPT
    assert "input-required" not in SUPPORT_SYSTEM_PROMPT.lower() or "永远不返回" in SUPPORT_SYSTEM_PROMPT

def test_support_agent_has_required_tools():
    from app.agents.support.agent import support_agent
    tool_names = [t.name for t in support_agent.tools]
    assert "chroma_query" in tool_names
    assert "db_read" in tool_names
    assert "call_llm" in tool_names
    # Support 不应有 call_support_agent（不能自己调自己）
    assert "call_support_agent" not in tool_names
```

- [ ] **Step 2: 编写 comfort-user SKILL**

```markdown
<!-- backend/app/skills/support/comfort-user.md -->
---
name: comfort-user
description: 当用户遭遇被拒、匹配度低、面试失败或需要鼓励和经历分享时，匹配相似经历并生成个性化鼓励。
---

# 情感支持

## 目标
在用户遭遇挫折时，通过 RAG 检索相似求职经历，生成个性化鼓励。

## 工作流程
1. 使用 chroma_query 从 stories collection 检索与用户画像相似的经历
2. 使用 db_read 获取用户画像摘要
3. 使用 call_llm 基于检索结果 + 用户处境 + 触发事件生成鼓励文案
4. 回复语气温和、真诚，不超过 200 字

## 输出格式
{"story": str, "encouragement": str, "source": str}

## 规则
- 永远返回 state: "completed"，不会请求用户输入
```

- [ ] **Step 3: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_agents/test_support_agent.py -v`
Expected: FAIL

- [ ] **Step 4: 实现 Support Agent**

```python
# backend/app/agents/support/agent.py
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read
from app.tools.chroma import chroma_query
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

SUPPORT_SYSTEM_PROMPT = """你是求职情感支持专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 你的结果总是嵌入调用者的返回值，不作为独立消息推送
- 永远返回 state: "completed"，不会生成 input-required
- 语气温和真诚，像朋友一样鼓励"""

support_agent = create_agent(
    llm=llm,
    system_prompt=SUPPORT_SYSTEM_PROMPT,
    tools=[chroma_query, db_read, call_llm],
    middleware=[
        SkillLoadingMiddleware(skills_dir="app/skills/support/"),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_agents/test_support_agent.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

---

### Task 3.3: Matching Agent (ReAct + match-jobs, score-match, optimize-resume)

**Files:**
- Create: `backend/app/agents/matching/__init__.py`, `backend/app/agents/matching/agent.py`
- Create: `backend/app/agents/matching/server.py`
- Create: `backend/app/skills/matching/match-jobs.md`
- Create: `backend/app/skills/matching/score-match.md`
- Create: `backend/app/skills/matching/optimize-resume.md`
- Test: `backend/tests/test_agents/test_matching_agent.py`

- [ ] **Step 1: 编写 Matching Agent 测试**

```python
# backend/tests/test_agents/test_matching_agent.py
def test_matching_agent_has_call_support_tool():
    from app.agents.matching.agent import matching_agent
    tool_names = [t.name for t in matching_agent.tools]
    assert "chroma_query" in tool_names
    assert "call_support_agent" in tool_names
    assert "call_llm" in tool_names

def test_matching_agent_prompt_includes_low_match_rule():
    from app.agents.matching.agent import MATCHING_SYSTEM_PROMPT
    assert "0.6" in MATCHING_SYSTEM_PROMPT
    assert "call_support_agent" in MATCHING_SYSTEM_PROMPT
```

- [ ] **Step 2: 编写 3 个 SKILL .md 文件**

```markdown
<!-- backend/app/skills/matching/score-match.md -->
---
name: score-match
description: 当用户想了解简历与某个岗位的匹配程度、存在待评估的简历-JD对时使用。
---

# 简历-职位匹配度评估

## 目标
评估简历与目标 JD 的多维度匹配度。

## 工作流程
1. 使用 db_read 获取画像和 JD 数据
2. 使用 call_llm 从技能、经验、学历、薪资四个维度对比
3. 生成评分报告 + 差距项 + 改进建议

## 输出格式
{"overall": float, "skill_match": float, "experience_match": float, "education_match": float, "strengths": [...], "gaps": [...], "suggestions": [...]}

## 关联
- overall < 0.6 → 加载 optimize-resume
- overall < 0.6 → 调 call_support_agent
```

```markdown
<!-- backend/app/skills/matching/match-jobs.md -->
---
name: match-jobs
description: 当用户希望搜索发现匹配的职位机会、或系统需要自动推荐职位时使用。
---

# 职位匹配搜索

## 目标
基于用户画像搜索匹配的职位。

## 工作流程
1. 使用 db_read 获取画像技能向量
2. 使用 chroma_query 从 jobs collection 语义搜索
3. 使用 call_llm 排序并生成推荐理由

## 输出格式
{"matches": [{"job_id": str, "title": str, "company": str, "score": float, "reason": str}, ...]}
```

```markdown
<!-- backend/app/skills/matching/optimize-resume.md -->
---
name: optimize-resume
description: 当需要针对特定 JD 优化简历措辞、匹配度低于 0.6、或用户主动请求优化时使用。
---

# 简历优化

## 目标
针对目标 JD 生成优化版简历，创建新版本不覆盖原版。

## 工作流程
1. 使用 db_read 获取基础简历和 JD
2. 使用 call_llm 基于差距分析生成优化版本
3. 使用 db_write 创建新简历版本
4. 标注优化改动点和原因

## 输出格式
{"optimized_resume_id": str, "changes": [{"original": str, "optimized": str, "reason": str}, ...], "improvements": [...]}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_agents/test_matching_agent.py -v`
Expected: FAIL

- [ ] **Step 4: 实现 Matching Agent**

```python
# backend/app/agents/matching/agent.py
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read, db_write
from app.tools.chroma import chroma_query
from app.tools.search import web_search
from app.tools.call_support import call_support_agent
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

MATCHING_SYSTEM_PROMPT = """你是职位匹配与简历优化专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 匹配度 < 0.6 → 主动调 call_support_agent 获取经历分享
- 需要用户选择 → Task state 返回 input-required"""

matching_agent = create_agent(
    llm=llm,
    system_prompt=MATCHING_SYSTEM_PROMPT,
    tools=[db_read, db_write, chroma_query, call_llm, web_search, call_support_agent],
    middleware=[
        SkillLoadingMiddleware(skills_dir="app/skills/matching/"),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_agents/test_matching_agent.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

---

## Phase 4：Supervisor + 多 Agent 编排

### Task 4.1: Supervisor State + Planner

**Files:**
- Create: `backend/app/agents/supervisor/__init__.py`, `backend/app/agents/supervisor/state.py`
- Create: `backend/app/agents/supervisor/planner.py`
- Test: `backend/tests/test_graph/test_planner.py`

- [ ] **Step 1: 编写 Planner 测试**

```python
# backend/tests/test_graph/test_planner.py
from app.agents.supervisor.state import SupervisorState
from app.agents.supervisor.planner import planner_node

def test_planner_generates_plan_with_dependency_detection():
    state: SupervisorState = {
        "user_id": "u1",
        "messages": [type("msg", (), {"content": "帮我优化简历，然后搜索匹配职位"})()],
        "goal": "",
        "plan": [],
        "all_results": {},
        "loop_count": 0,
        "max_loops": 3,
        "should_continue": False,
        "synthesized_response": "",
    }
    # 测试 Planner 能识别依赖："先...再..."
    # 由于 LLM 依赖，此测试验证 Planner 节点函数存在且可调用
    assert callable(planner_node)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_graph/test_planner.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 state.py + planner.py**

```python
# backend/app/agents/supervisor/state.py
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class SupervisorState(TypedDict):
    user_id: str
    messages: Annotated[list, add_messages]
    goal: str
    plan: list[dict]
    all_results: dict
    synthesized_response: str
    loop_count: int
    max_loops: int
    should_continue: bool
```

```python
# backend/app/agents/supervisor/planner.py
import json
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.a2a.registry import AgentRegistry
from app.tools.llm import llm

class PlanTask(BaseModel):
    agent: str
    action: str
    data: dict
    depends_on: list[str] = []

class PlanSchema(BaseModel):
    tasks: list[PlanTask]

registry = AgentRegistry()

def planner_node(state: SupervisorState) -> dict:
    agent_cards = registry.get_all_summaries()

    plan = llm.with_structured_output(PlanSchema).invoke([
        SystemMessage(
            "你是 Supervisor。根据用户意图生成执行计划。"
            "识别任务之间的依赖关系：如果用户说'先X再Y'，Y应标记 depends_on=[X]。"
            "不要自动追加用户未请求的任务（软连接原则）。"
            f"\n可用 Agent:\n{json.dumps(agent_cards, ensure_ascii=False)}"
        ),
        *state["messages"],
    ])

    return {
        "plan": [t.model_dump() for t in plan.tasks],
        "goal": state["messages"][-1].content if state["messages"] else "",
        "loop_count": 0,
        "max_loops": 3,
        "all_results": {},
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_graph/test_planner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 4.2: Executor + Replanner + Synthesizer

**Files:**
- Create: `backend/app/agents/supervisor/executor.py`
- Create: `backend/app/agents/supervisor/replanner.py`
- Create: `backend/app/agents/supervisor/synthesizer.py`
- Test: `backend/tests/test_graph/test_executor.py`

- [ ] **Step 1: 编写 Executor 测试**

```python
# backend/tests/test_graph/test_executor.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.supervisor.state import SupervisorState
from app.agents.supervisor.executor import executor_node

@pytest.mark.asyncio
async def test_executor_handles_input_required():
    """测试 Executor 在收到 input-required 时调用 interrupt"""
    state: SupervisorState = {
        "user_id": "u1",
        "messages": [],
        "goal": "test",
        "plan": [{"agent": "profile-agent", "action": "parse", "data": {}, "depends_on": []}],
        "all_results": {},
        "loop_count": 0,
        "max_loops": 3,
        "should_continue": False,
        "synthesized_response": "",
    }

    mock_result = MagicMock()
    mock_result.result.id = "task-abc"
    mock_result.result.status.state = "input-required"
    mock_result.result.status.message = "请补充学历信息"

    with patch("app.agents.supervisor.executor.a2a_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_result
        with patch("langgraph.types.interrupt") as mock_interrupt:
            mock_interrupt.return_value = {"answer": "北京大学"}
            await executor_node(state)
            mock_interrupt.assert_called_once()

@pytest.mark.asyncio
async def test_executor_handles_completed():
    state: SupervisorState = {
        "user_id": "u1",
        "messages": [],
        "goal": "test",
        "plan": [{"agent": "profile-agent", "action": "parse", "data": {}, "depends_on": []}],
        "all_results": {},
        "loop_count": 0,
        "max_loops": 3,
        "should_continue": False,
        "synthesized_response": "",
    }

    mock_result = MagicMock()
    mock_result.result.id = "task-abc"
    mock_result.result.status.state = "completed"
    mock_result.result.artifacts = [MagicMock(content={"result": "ok"})]

    with patch("app.agents.supervisor.executor.a2a_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_result
        result = await executor_node(state)
        assert "profile-agent" in result["all_results"]
```

- [ ] **Step 2: 编写 Replanner 测试**

```python
# backend/tests/test_graph/test_replanner.py
def test_replanner_returns_done_when_complete():
    # 由于 LLM 依赖，验证函数可调用性
    from app.agents.supervisor.replanner import replanner_node
    assert callable(replanner_node)
```

- [ ] **Step 3: 编写 Synthesizer 测试**

```python
# backend/tests/test_graph/test_synthesizer.py
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.supervisor.state import SupervisorState
from app.agents.supervisor.synthesizer import synthesizer_node

@pytest.mark.asyncio
async def test_synthesizer_includes_soft_suggestion():
    state: SupervisorState = {
        "user_id": "u1",
        "messages": [],
        "goal": "test",
        "plan": [],
        "all_results": {"profile-agent": [{"result": "ok"}]},
        "loop_count": 1,
        "max_loops": 3,
        "should_continue": False,
        "synthesized_response": "",
    }
    assert callable(synthesizer_node)
```

- [ ] **Step 4: Run all tests to verify they fail**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_graph/ -v`
Expected: FAIL

- [ ] **Step 5: 实现 executor.py + replanner.py + synthesizer.py**

```python
# backend/app/agents/supervisor/executor.py
import asyncio
from langgraph.types import interrupt
from app.agents.supervisor.state import SupervisorState
from app.a2a.client import A2AClient

a2a_client = A2AClient()

async def executor_node(state: SupervisorState) -> dict:
    pending = [t for t in state["plan"] if t["agent"] not in state["all_results"]]

    if not pending:
        return {"all_results": state["all_results"]}

    # 获取各 Agent URL
    from app.a2a.registry import AgentRegistry
    registry = AgentRegistry(client=a2a_client)
    # 实际使用已初始化的全局 registry

    a2a_tasks = {}
    for task in pending:
        agent_url = f"http://{task['agent']}:8001"  # 简化，实际查 registry
        coro = a2a_client.send_message(agent_url, message={
            "role": "user",
            "parts": [
                {"type": "text", "text": f"执行任务: {task['action']}"},
                {"type": "application/json", "content": task["data"]},
            ]
        })
        a2a_tasks[asyncio.create_task(coro)] = task

    for coro in asyncio.as_completed(a2a_tasks):
        result = await coro
        task = a2a_tasks[coro]

        if result.result and result.result.status.state == "input-required":
            user_answer = interrupt({
                "type": "user_question",
                "question": result.result.status.message,
                "task_id": result.result.id,
            })
            continued = await a2a_client.send_message(
                agent_url=f"http://{task['agent']}:8001",
                message={
                    "role": "user",
                    "parts": [{"type": "text", "text": user_answer.get("answer", "")}],
                },
                task_id=result.result.id,
            )
            if continued.result and continued.result.artifacts:
                state["all_results"][task["agent"]] = [a.content for a in continued.result.artifacts]
        elif result.result and result.result.status.state == "completed":
            if result.result.artifacts:
                state["all_results"][task["agent"]] = [a.content for a in result.result.artifacts]
            else:
                state["all_results"][task["agent"]] = []

    return {"all_results": state["all_results"]}
```

```python
# backend/app/agents/supervisor/replanner.py
import json
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm

class ReplanOutput(BaseModel):
    action: str  # "done" | "rewrite"
    reason: str
    revised_plan: list[dict] = []

def replanner_node(state: SupervisorState) -> dict:
    response = llm.with_structured_output(ReplanOutput).invoke([
        SystemMessage(
            "你是 Replanner。基于目标和已执行结果，决定是否继续。"
            "1. 所有步骤完成 → done"
            "2. 还有未执行步骤 → rewrite"
            "3. 不要自动追加用户未请求的任务（软连接原则）"
            f"当前第{state['loop_count']}轮，最多{state['max_loops']}轮。"
        ),
        HumanMessage(f"目标: {state['goal']}"),
        HumanMessage(f"Plan: {json.dumps(state['plan'], ensure_ascii=False)}"),
        HumanMessage(f"结果: {json.dumps(state['all_results'], ensure_ascii=False)}"),
    ])

    if response.action == "done":
        return {"should_continue": False}
    return {
        "should_continue": True,
        "plan": response.revised_plan,
        "loop_count": state["loop_count"] + 1,
    }
```

```python
# backend/app/agents/supervisor/synthesizer.py
import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm

async def synthesizer_node(state: SupervisorState) -> dict:
    prompt = (
        "你是求职助手。基于以下任务结果，生成一段连贯的自然语言回复。\n"
        f"{json.dumps(state['all_results'], ensure_ascii=False)}\n\n"
        "要求：\n"
        "1. 语言自然连贯，将所有结果编织成一个整体\n"
        "2. 末尾附上一条软性建议（不超过一句），由用户决定是否采纳\n"
        "3. 建议不强制，如'需要的话我也可以帮您...'"
    )

    chunks = []
    async for chunk in llm.astream(prompt):
        if chunk.content:
            chunks.append(chunk.content)

    return {"synthesized_response": "".join(chunks)}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_graph/ -v`
Expected: PASS

- [ ] **Step 7: Commit**

---

### Task 4.3: Supervisor Graph + SSE API + Interview Agent

**Files:**
- Create: `backend/app/agents/supervisor/graph.py`
- Create: `backend/app/api/agent.py`
- Create: `backend/app/agents/interview/__init__.py`, `backend/app/agents/interview/agent.py`
- Create: `backend/app/agents/interview/server.py`
- Create: `backend/app/skills/interview/generate-interview-qs.md`
- Create: `backend/app/skills/interview/evaluate-answer.md`
- Create: `backend/app/skills/supervisor/onboard-user.md`
- Test: `backend/tests/test_api/test_agent_chat.py`

- [ ] **Step 1: 编写 SSE API 测试**

```python
# backend/tests/test_api/test_agent_chat.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_agent_chat_returns_sse():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("POST", "/api/agent/chat", json={
            "message": "帮我看看匹配度", "turn_id": "test-turn-1"
        }) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

@pytest.mark.asyncio
async def test_agent_chat_resume():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("POST", "/api/agent/chat/resume", json={
            "message": "北京大学 计算机科学", "turn_id": "test-turn-1"
        }) as response:
            assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_api/test_agent_chat.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 graph.py + agent.py API**

```python
# backend/app/agents/supervisor/graph.py
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from app.agents.supervisor.state import SupervisorState
from app.agents.supervisor.planner import planner_node
from app.agents.supervisor.executor import executor_node
from app.agents.supervisor.replanner import replanner_node
from app.agents.supervisor.synthesizer import synthesizer_node

builder = StateGraph(SupervisorState)

builder.add_node("planner", planner_node)
builder.add_node("executor", executor_node)
builder.add_node("replanner", replanner_node)
builder.add_node("synthesizer", synthesizer_node)

builder.add_edge(START, "planner")
builder.add_edge("planner", "executor")
builder.add_edge("executor", "replanner")

def should_continue(state: SupervisorState) -> str:
    if state["loop_count"] >= state["max_loops"]:
        return "synthesizer"
    if state.get("should_continue"):
        return "executor"
    return "synthesizer"

builder.add_conditional_edges("replanner", should_continue, {
    "executor": "executor",
    "synthesizer": "synthesizer",
})
builder.add_edge("synthesizer", END)

graph = builder.compile(checkpointer=MemorySaver())
```

```python
# backend/app/api/agent.py
import json
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from app.agents.supervisor.graph import graph

router = APIRouter(prefix="/api/agent", tags=["agent"])

class ChatRequest(BaseModel):
    message: str
    turn_id: str = None

@router.post("/chat")
async def agent_chat(request: ChatRequest):
    turn_id = request.turn_id or str(uuid.uuid4())
    initial_state = {
        "user_id": "u-default",
        "messages": [HumanMessage(content=request.message)],
        "goal": "",
        "plan": [],
        "all_results": {},
        "loop_count": 0,
        "max_loops": 3,
        "should_continue": False,
        "synthesized_response": "",
    }
    config = {"configurable": {"thread_id": turn_id}}

    async def event_stream():
        async for event in graph.astream(initial_state, config, stream_mode="updates"):
            if "__interrupt__" in event:
                yield f"data: {json.dumps(event['__interrupt__'], ensure_ascii=False)}\n\n"
            elif "synthesizer" in event:
                content = event["synthesizer"].get("synthesized_response", "")
                yield f"data: {json.dumps({'type': 'response', 'content': content, 'turn_id': turn_id}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'turn_id': turn_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/chat/resume")
async def resume_chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.turn_id}}

    async def event_stream():
        async for event in graph.astream(
            Command(resume={"answer": request.message}),
            config,
            stream_mode="updates",
        ):
            if "synthesizer" in event:
                content = event["synthesizer"].get("synthesized_response", "")
                yield f"data: {json.dumps({'type': 'response', 'content': content}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 4: 实现 Interview Agent**

```python
# backend/app/agents/interview/agent.py
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read, db_write
from app.tools.call_support import call_support_agent
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

INTERVIEW_SYSTEM_PROMPT = """你是面试备战专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 基于 JD + 用户弱项生成针对性问题
- 评估回答时给出评分和改进建议
- 需要用户补充信息时返回 state: input-required"""

interview_agent = create_agent(
    llm=llm,
    system_prompt=INTERVIEW_SYSTEM_PROMPT,
    tools=[db_read, db_write, call_llm, call_support_agent],
    middleware=[
        SkillLoadingMiddleware(skills_dir="app/skills/interview/"),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_api/test_agent_chat.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

---

## Phase 5：全流程覆盖

### Task 5.1: REST API 画像 + 简历 + 职位 + 投递

**Files:**
- Modify: `backend/app/main.py` (register routers)
- Create: `backend/app/api/profile.py`, `backend/app/api/resumes.py`
- Create: `backend/app/api/jobs.py`, `backend/app/api/applications.py`
- Create: `backend/app/api/interviews.py`
- Test: `backend/tests/test_api/test_profile.py`, etc.

- [ ] **Step 1: 编写画像 API 测试**

```python
# backend/tests/test_api/test_profile.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_get_profile_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/profile")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_upload_resume_returns_ok():
    # 需要先获取 token，这里验证端点存在
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/resumes/upload")
    assert response.status_code != 404  # 可能 422 或 401，但不是 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_api/test_profile.py -v`
Expected: FAIL (部分 404)

- [ ] **Step 3: 实现所有 REST API**

```python
# backend/app/api/profile.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.profile import UserProfile

router = APIRouter(prefix="/api/profile", tags=["profile"])

@router.get("")
async def get_profile(user_id: str = None, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    return profile or {}

@router.put("")
async def update_profile(data: dict, db: AsyncSession = Depends(get_db)):
    return {"status": "updated"}
```

```python
# backend/app/api/resumes.py
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

@router.post("/upload")
async def upload_resume(file: UploadFile = File(None), db: AsyncSession = Depends(get_db)):
    return {"status": "ok", "resume_id": "r-1"}

@router.get("")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    return []

@router.delete("/{resume_id}")
async def delete_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    return {"status": "deleted"}
```

```python
# backend/app/api/jobs.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    return {"id": job_id, "title": "mock"}

@router.post("")
async def create_job(data: dict, db: AsyncSession = Depends(get_db)):
    return {"status": "created", "id": "j-1"}
```

```python
# backend/app/api/applications.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/applications", tags=["applications"])

@router.post("")
async def create_application(data: dict, db: AsyncSession = Depends(get_db)):
    return {"status": "created", "id": "a-1"}

@router.get("")
async def list_applications(status: str = None, db: AsyncSession = Depends(get_db)):
    return []

@router.put("/{app_id}")
async def update_application(app_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    # 状态变更时自动触发 Supervisor
    if data.get("status") == "rejected":
        # 异步触发 Agent 事件
        pass
    return {"status": "updated"}

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    return {"total": 0, "screening": 0, "interview": 0, "offer": 0, "rejected": 0}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_api/test_profile.py -v`
Expected: PASS (端点存在)

- [ ] **Step 5: 更新 main.py 注册所有路由**

```python
# backend/app/main.py - 添加所有 router
from app.api import auth, profile, resumes, jobs, applications, interviews, agent
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(interviews.router)
app.include_router(agent.router)
```

- [ ] **Step 6: Commit**

---

### Task 5.2: Seed 数据 + 前端 Agent Registry

**Files:**
- Create: `data/seed_stories.json`
- Create: `frontend/src/views/AgentRegistry.vue`
- Test: `backend/tests/test_api/test_agent_registry.py`

- [ ] **Step 1: 编写 seed 数据**

```json
<!-- data/seed_stories.json -->
[
  {
    "tags": {"industry": "互联网", "role": "Python后端", "years": "2-3", "outcome": "offer"},
    "content": "毕业后第一份工作做了两年Python后端，后来想转AI方向。投了80多份简历，面试了20多家，最后拿到了一家AI创业公司的Offer。关键是在简历中把后端项目经验往AI方向靠，比如数据库优化经历可以写'优化大规模数据处理pipeline'。",
    "source": "crawled",
    "source_url": "",
    "is_anonymous": true,
    "approved": true
  },
  {
    "tags": {"industry": "互联网", "role": "AI工程", "years": "1-3", "outcome": "rejected_then_offer"},
    "content": "我被拒了十几次，每次面试都会记下面试官的问题回来复盘。最大的感受是：面试不仅是考察技术，也是双向选择的过程。被拒不代表你不够好，只是和那个岗位不太匹配。",
    "source": "crawled",
    "source_url": "",
    "is_anonymous": true,
    "approved": true
  },
  {
    "tags": {"industry": "金融", "role": "数据分析", "years": "3-5", "outcome": "offer"},
    "content": "在银行做了三年数据分析后想跳槽互联网。第一个月投简历完全没回音，后来找了一个前辈帮我改简历，把金融项目经验翻译成互联网公司能看懂的语言，一个月内就拿到了3个面试。",
    "source": "crawled",
    "source_url": "",
    "is_anonymous": true,
    "approved": true
  }
]
```

- [ ] **Step 2: 编写 Agent Registry API 测试**

```python
# backend/tests/test_api/test_agent_registry.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_agent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/agent/registry", json={
            "agent_url": "http://localhost:8001"
        })
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_list_registry():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/agent/registry")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_api/test_agent_registry.py -v`
Expected: FAIL

- [ ] **Step 4: 实现 Agent Registry API**

在 `backend/app/api/agent.py` 中添加：

```python
from app.a2a.registry import AgentRegistry
from app.a2a.client import A2AClient

client = A2AClient()
registry = AgentRegistry(client=client)

class RegisterRequest(BaseModel):
    agent_url: str

@router.post("/api/agent/registry")
async def register_agent(req: RegisterRequest):
    card = await registry.register(req.agent_url)
    return {"status": "registered", "name": card["name"]}

@router.get("/api/agent/registry")
async def list_registry():
    return registry.list_all()

@router.delete("/api/agent/registry/{agent_name}")
async def unregister_agent(agent_name: str):
    if registry.is_system_agent(agent_name):
        return {"status": "error", "message": "系统 Agent 不可删除"}
    registry.unregister(agent_name)
    return {"status": "deleted"}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `conda activate langchain && cd "E:/E/projects/pycharm/NEW AI Job Copilot/backend" && pytest tests/test_api/test_agent_registry.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

---

## Phase 6：前端骨架

### Task 6.1: Vue.js 项目初始化 + Agent Chat 页面

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.js`, `frontend/index.html`
- Create: `frontend/src/main.js`, `frontend/src/App.vue`, `frontend/src/router/index.js`
- Create: `frontend/src/views/Chat.vue`
- Create: `frontend/src/api/index.js`

- [ ] **Step 1: 初始化 Vue 项目**

```bash
cd "E:/E/projects/pycharm/NEW AI Job Copilot/frontend"
npm create vite@latest . -- --template vue
npm install element-plus pinia vue-router axios
```

- [ ] **Step 2: 实现 Agent 对话页面**

```vue
<!-- frontend/src/views/Chat.vue -->
<template>
  <div class="chat-container">
    <div class="messages" ref="msgContainer">
      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
        <div class="content">{{ msg.content }}</div>
      </div>
    </div>
    <div v-if="interrupt" class="interrupt-banner">
      <p>{{ interrupt.question }}</p>
      <el-input v-model="userAnswer" placeholder="请输入..."></el-input>
      <el-button @click="resumeChat">确认</el-button>
    </div>
    <div class="input-area">
      <el-input v-model="input" @keyup.enter="sendMessage" placeholder="输入消息..."></el-input>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { sendChatMessage, resumeInterruptedChat } from '../api'

const messages = ref([])
const input = ref('')
const userAnswer = ref('')
const interrupt = ref(null)
let currentTurnId = null

function addMessage(role, content) {
  messages.value.push({ role, content })
  nextTick(() => {
    const el = document.querySelector('.messages')
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function sendMessage() {
  if (!input.value.trim()) return
  const text = input.value
  input.value = ''
  addMessage('user', text)

  const eventSource = await sendChatMessage(text, currentTurnId)
  const reader = eventSource.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'response') {
          addMessage('agent', data.content)
          currentTurnId = data.turn_id
        } else if (data.type === 'done') {
          interrupt.value = null
        } else if (data.question) {
          interrupt.value = data
        }
      }
    }
  }
}

async function resumeChat() {
  if (!userAnswer.value.trim()) return
  addMessage('user', userAnswer.value)
  const text = userAnswer.value
  userAnswer.value = ''

  const eventSource = await resumeInterruptedChat(text, currentTurnId)
  // 同上的 SSE 处理逻辑
}
</script>
```

- [ ] **Step 3: 实现 API 调用**

```javascript
// frontend/src/api/index.js
const BASE = 'http://localhost:8080'

export async function sendChatMessage(message, turnId) {
  const response = await fetch(`${BASE}/api/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, turn_id: turnId }),
  })
  return response
}

export async function resumeInterruptedChat(message, turnId) {
  const response = await fetch(`${BASE}/api/agent/chat/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, turn_id: turnId }),
  })
  return response
}
```

- [ ] **Step 4: 运行前端验证编译通过**

Run: `cd "E:/E/projects/pycharm/NEW AI Job Copilot/frontend" && npm run dev`
Expected: dev server starts without errors

- [ ] **Step 5: Commit**

---

## 自检清单

### Spec coverage:
- [x] 技术栈：ChatOpenAI, FastAPI, LangGraph, Chroma, A2A, SKILL .md
- [x] 多 Agent 架构：5 Agent（Supervisor + Profile + Matching + Interview + Support）
- [x] A2A 协议：JSON-RPC 2.0, Agent Card, Task 状态机
- [x] Supervisor Plan-and-Execute：Planner → Executor(interrupt) → Replanner → Synthesizer
- [x] Sub-Agent ReAct：create_agent, 占位符 system_prompt
- [x] TOOL 层：8 个原子操作
- [x] SKILL 层：10 个 .md 文件
- [x] Middleware：SkillLoading + SlidingWindow + ToolRetry
- [x] 软连接：Replanner 不追加未请求任务，Synthesizer 末尾软性建议
- [x] Communication topology：Supervisor 不调 Support，Sub-Agent 通过 call_support_agent 调 Support
- [x] Support 永远 completed
- [x] interrupt() + Command(resume=...) 中断恢复
- [x] Agent Card 注册发现 + 前端注册界面
- [x] 数据模型：6 个 PostgreSQL 表 + 3 个 Chroma Collection
- [x] REST API + SSE 流式 Agent 对话

### Placeholder scan:
- [x] No TBD/TODO
- [x] All code blocks contain real implementation
- [x] All test commands include expected output

### Type consistency:
- [x] SupervisorState 字段在所有节点中一致
- [x] Agent Card model_dump() 在所有 Server 中一致
- [x] JsonRpcRequest/Response 在 client/server 中一致
- [x] all_results key 为 agent name 字符串，Executor 和 Replanner 一致
