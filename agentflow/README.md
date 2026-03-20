# AgentFlow — Multi-Agent AI Task Automation Platform

> A production-grade multi-agent AI platform where specialized agents collaborate to complete complex tasks. Built to demonstrate full-stack engineering, cloud-native architecture, and AI integration skills.

[![CI/CD](https://github.com/yourusername/agentflow/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/agentflow/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Java](https://img.shields.io/badge/Java-17-orange)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![Terraform](https://img.shields.io/badge/IaC-Terraform-purple)
![Kubernetes](https://img.shields.io/badge/Orchestration-EKS-orange)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [High-Level Design (HLD)](#2-high-level-design-hld)
   - [System Architecture](#21-system-architecture)
   - [Component Responsibilities](#22-component-responsibilities)
   - [Data Flow](#23-data-flow)
   - [Non-Functional Requirements](#24-non-functional-requirements)
3. [Low-Level Design (LLD)](#3-low-level-design-lld)
   - [API Gateway — Spring Boot](#31-api-gateway--spring-boot)
   - [Agent Orchestrator — FastAPI + LangGraph](#32-agent-orchestrator--fastapi--langgraph)
   - [Multi-Agent State Machine](#33-multi-agent-state-machine)
   - [Frontend — Next.js](#34-frontend--nextjs)
   - [Database Schema](#35-database-schema)
   - [Caching Strategy](#36-caching-strategy)
4. [Tech Stack](#4-tech-stack)
5. [Cloud Architecture — AWS](#5-cloud-architecture--aws)
   - [Infrastructure Diagram](#51-infrastructure-diagram)
   - [Networking — VPC Design](#52-networking--vpc-design)
   - [IAM & Security](#53-iam--security)
6. [DevOps Pipeline](#6-devops-pipeline)
   - [CI/CD with GitHub Actions](#61-cicd-with-github-actions)
   - [Docker Strategy](#62-docker-strategy)
   - [Kubernetes on EKS](#63-kubernetes-on-eks)
7. [Monitoring & Observability](#7-monitoring--observability)
8. [Getting Started](#8-getting-started)
9. [API Reference](#9-api-reference)
10. [Design Decisions & Trade-offs](#10-design-decisions--trade-offs)

---

## 1. Project Overview

**AgentFlow** lets users submit a complex goal (e.g., *"Research the top 5 EV companies and write a competitive analysis"*) and watch four specialized AI agents collaborate in real time to complete it:

| Agent | Role |
|---|---|
| **Researcher** | Searches the web, retrieves context via RAG from a vector store |
| **Writer** | Drafts structured documents, reports, and summaries |
| **Coder** | Generates, executes, and tests code snippets and data visualizations |
| **Critic** | Reviews the combined output, scores quality, triggers revision if needed |

The orchestrator runs a **directed acyclic graph** (with conditional cycles for revision) using LangGraph. Results stream in real time to the browser via Server-Sent Events (SSE).

---

## 2. High-Level Design (HLD)

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT                                  │
│                   Next.js (React + TypeScript)                   │
│              Hosted on S3 + CloudFront (CDN)                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │  HTTPS / SSE
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (Public Subnet)                 │
│              Spring Boot — Port 8080                            │
│   JWT Auth · Rate Limiting · Request Validation · Routing       │
└──────────────┬──────────────────────────────┬───────────────────┘
               │ REST (internal)              │ REST (internal)
               ▼                              ▼
┌──────────────────────────┐    ┌─────────────────────────────────┐
│   AGENT ORCHESTRATOR     │    │     AUTH SERVICE (future)        │
│   FastAPI — Port 8000    │    │     Cognito / custom JWT         │
│   LangGraph State Machine│    └─────────────────────────────────┘
│   ┌──────┐ ┌──────────┐  │
│   │ RAG  │ │ Tool Pool │  │
│   └──────┘ └──────────┘  │
└──────┬───────────────────┘
       │  LLM API calls
       ▼
┌──────────────────────────┐
│  OpenAI / Anthropic API  │
│  (external, over HTTPS)  │
└──────────────────────────┘
       │
       ▼ Reads/Writes
┌──────────────────────────────────────────────────────────────┐
│                        DATA LAYER (Private Subnet)            │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │ PostgreSQL RDS│  │ ElastiCache   │  │   S3 Bucket      │ │
│  │ + pgvector    │  │ (Redis)       │  │ (Files/Artifacts)│ │
│  │ Tasks/Runs    │  │ Sessions/Cache│  │                  │ │
│  └───────────────┘  └───────────────┘  └──────────────────┘ │
└──────────────────────────────────────────────────────────────┘

DevOps Layer:
  GitHub Actions → ECR → EKS (Kubernetes)
  Terraform (IaC) · Prometheus + Grafana (Monitoring)
```

### 2.2 Component Responsibilities

**Next.js Frontend**
- Renders task submission form and real-time agent timeline
- Streams agent progress updates via SSE (no polling)
- Authenticated via JWT stored in HttpOnly cookies
- Deployed to S3 + served via CloudFront for global CDN

**Spring Boot API Gateway**
- Single entry point for all client requests
- Validates and parses JWT tokens (stateless auth)
- Rate limits per user (token bucket, 10 req/min via Redis)
- Proxies `/api/tasks` → orchestrator, `/api/auth` → Cognito
- Exposes SSE endpoint that bridges orchestrator's event stream to client

**FastAPI Orchestrator**
- Receives task definition, builds a LangGraph workflow
- Manages agent execution graph: Researcher → Writer + Coder → Critic
- Handles conditional retry loop if Critic score < threshold
- Persists run state to PostgreSQL and caches active runs in Redis
- Publishes events to a Redis pub/sub channel (read by gateway for SSE)

**PostgreSQL + pgvector**
- `tasks` table: user task definitions and status
- `runs` table: individual workflow execution records
- `agent_steps` table: per-agent outputs for each run
- `embeddings` table (pgvector): document chunks for RAG retrieval

**ElastiCache (Redis)**
- Session cache: JWT → user mapping (TTL 1 hour)
- Rate limit counters: `rate:{user_id}` (TTL 60s)
- Active run state: `run:{run_id}` (LangGraph checkpoint)
- Pub/Sub channel: `events:{run_id}` for SSE bridging

### 2.3 Data Flow

```
User submits task
       │
       ▼
[1] POST /api/tasks  →  Spring Boot validates JWT, rate-checks Redis
       │
       ▼
[2] Spring Boot  →  POST /internal/runs  →  FastAPI Orchestrator
       │
       ▼
[3] Orchestrator builds LangGraph DAG, saves run to PostgreSQL
       │
       ├─[4a] Researcher Agent: web search + pgvector RAG query
       │
       ├─[4b] Writer Agent: calls LLM with research context
       │
       ├─[4c] Coder Agent: generates + sandboxes code (optional)
       │
       └─[4d] Critic Agent: scores output → retry loop or finalize
                │
                ▼ on each step
[5] Orchestrator publishes event → Redis pub/sub → Spring Boot SSE → Browser

[6] Final output saved to PostgreSQL + artifact stored in S3
```

### 2.4 Non-Functional Requirements

| Requirement | Target | How |
|---|---|---|
| Task throughput | 100 concurrent runs | Horizontal pod autoscaling on EKS |
| Streaming latency | < 200ms event lag | Redis pub/sub, SSE (no WebSocket overhead) |
| API p99 latency | < 500ms | ElastiCache for session lookup, no DB on hot path |
| Availability | 99.9% | Multi-AZ RDS, EKS node groups across 2 AZs |
| Security | JWT + network isolation | Private subnets, SGs, IAM roles for service accounts |
| Observability | Full trace per run | Prometheus metrics, structured JSON logs, run_id correlation |

---

## 3. Low-Level Design (LLD)

### 3.1 API Gateway — Spring Boot

**Package structure:**
```
com.agentflow/
├── controller/
│   ├── TaskController.java       # POST /api/tasks, GET /api/tasks/{id}
│   ├── StreamController.java     # GET /api/tasks/{id}/stream  (SSE)
│   └── AuthController.java       # POST /api/auth/login, /refresh
├── service/
│   ├── TaskService.java          # Business logic, calls OrchestratorClient
│   ├── StreamService.java        # Subscribes Redis pub/sub → SseEmitter
│   └── RateLimitService.java     # Token bucket via Redis INCR + TTL
├── client/
│   └── OrchestratorClient.java   # Feign HTTP client to FastAPI
├── config/
│   ├── SecurityConfig.java       # Spring Security, JWT filter chain
│   ├── RedisConfig.java          # Lettuce connection pool
│   └── FeignConfig.java          # Feign timeouts, retry
├── filter/
│   └── JwtAuthFilter.java        # Extracts + validates JWT per request
├── model/
│   └── Task.java                 # JPA entity
└── dto/
    ├── TaskRequest.java          # Incoming payload
    └── TaskResponse.java         # Outgoing payload
```

**JWT Auth Flow:**
```
Request → JwtAuthFilter.doFilterInternal()
  │
  ├─ Extract "Authorization: Bearer <token>"
  ├─ Verify signature with RS256 public key
  ├─ Check Redis cache: "session:{jti}" → user_id (fast path)
  │     └─ Cache miss → validate claims, cache for TTL
  └─ Set SecurityContextHolder → proceed to controller
```

**Rate Limiting (Redis token bucket):**
```java
// Pseudo-code
String key = "rate:" + userId;
Long count = redis.incr(key);          // atomic increment
if (count == 1) redis.expire(key, 60); // first request, set window
if (count > 10) throw RateLimitException();
```

**SSE Bridge (Redis pub/sub → client):**
```java
// StreamController
SseEmitter emitter = new SseEmitter(300_000L); // 5 min timeout
redisSubscriber.subscribe("events:" + runId, message -> {
    emitter.send(SseEmitter.event().data(message));
});
return emitter;
```

### 3.2 Agent Orchestrator — FastAPI + LangGraph

**Package structure:**
```
orchestrator/
├── main.py                  # FastAPI app, lifespan, routes
├── graph/
│   └── workflow.py          # LangGraph DAG definition
├── agents/
│   ├── researcher.py        # Web search + RAG retrieval
│   ├── writer.py            # LLM-based drafting
│   ├── coder.py             # Code generation + sandboxed exec
│   └── critic.py            # Output scoring and feedback
├── tools/
│   ├── search_tool.py       # DuckDuckGo / SerpAPI wrapper
│   ├── rag_tool.py          # pgvector similarity search
│   └── sandbox_tool.py      # Subprocess code execution
├── db/
│   ├── postgres.py          # SQLAlchemy async engine
│   └── redis_client.py      # aioredis connection
├── models/
│   └── schemas.py           # Pydantic request/response models
└── utils/
    └── events.py            # Redis pub/sub publisher
```

**API Endpoints:**
```
POST   /internal/runs          → Start a new agent run
GET    /internal/runs/{run_id} → Get run status and result
DELETE /internal/runs/{run_id} → Cancel a running workflow
GET    /health                 → Liveness probe
GET    /metrics                → Prometheus metrics (port 9090)
```

### 3.3 Multi-Agent State Machine

```
AgentState (TypedDict):
  task_description: str
  research_output:  str | None
  draft_output:     str | None
  code_output:      str | None
  critic_score:     float | None
  critic_feedback:  str | None
  revision_count:   int
  final_output:     str | None
  run_id:           str

LangGraph DAG:

  START
    │
    ▼
[researcher_node] ── publishes event ──►  Redis
    │
    ▼
[writer_node]  ──── publishes event ──►  Redis
    │
    ▼
[coder_node]   ──── publishes event ──►  Redis (conditional: only if task needs code)
    │
    ▼
[critic_node]  ──── publishes event ──►  Redis
    │
    ├─── score >= 0.8 ────────────────►  [finalize_node]  →  END
    │
    └─── score < 0.8 AND revision < 3 ► [researcher_node]  (revision loop)
         else                         ►  [finalize_node]  →  END
```

**Conditional edge logic:**
```python
def route_after_critic(state: AgentState) -> str:
    if state["critic_score"] >= 0.8:
        return "finalize"
    if state["revision_count"] >= 3:
        return "finalize"   # prevent infinite loop
    return "researcher"     # trigger revision
```

### 3.4 Frontend — Next.js

**Component tree:**
```
app/
├── layout.tsx                  # Root layout, auth provider
├── page.tsx                    # Landing / task submission
└── tasks/
    └── [id]/
        └── page.tsx            # Run detail with agent timeline

components/
├── TaskInput.tsx               # Textarea + submit, form validation
├── AgentTimeline.tsx           # Renders streaming steps in order
├── AgentCard.tsx               # Single agent step card (status, output)
└── StreamProvider.tsx          # useEventSource hook, SSE state machine

lib/
├── api.ts                      # Typed fetch wrappers → API gateway
├── auth.ts                     # JWT cookie helpers
└── types.ts                    # Shared TypeScript interfaces
```

**Real-time streaming via SSE:**
```typescript
// StreamProvider.tsx
const useAgentStream = (runId: string) => {
  const [steps, setSteps] = useState<AgentStep[]>([]);

  useEffect(() => {
    const es = new EventSource(`/api/tasks/${runId}/stream`);
    es.onmessage = (e) => {
      const event: AgentEvent = JSON.parse(e.data);
      setSteps(prev => [...prev, event]);
      if (event.type === "FINAL") es.close();
    };
    return () => es.close();
  }, [runId]);

  return steps;
};
```

### 3.5 Database Schema

```sql
-- tasks: user-submitted goals
CREATE TABLE tasks (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL,
  description TEXT NOT NULL,
  status      VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, RUNNING, DONE, FAILED
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- runs: workflow executions (1 task can be re-run)
CREATE TABLE runs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id         UUID REFERENCES tasks(id),
  status          VARCHAR(20) DEFAULT 'RUNNING',
  revision_count  INT DEFAULT 0,
  critic_score    FLOAT,
  final_output    TEXT,
  started_at      TIMESTAMPTZ DEFAULT NOW(),
  completed_at    TIMESTAMPTZ
);

-- agent_steps: per-agent outputs for observability
CREATE TABLE agent_steps (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id      UUID REFERENCES runs(id),
  agent_name  VARCHAR(50) NOT NULL,  -- researcher, writer, coder, critic
  input       JSONB,
  output      TEXT,
  duration_ms INT,
  token_count INT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- embeddings: RAG vector store using pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content    TEXT NOT NULL,
  embedding  vector(1536),   -- OpenAI text-embedding-3-small dimensions
  metadata   JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Indexes
CREATE INDEX idx_tasks_user    ON tasks(user_id);
CREATE INDEX idx_runs_task     ON runs(task_id);
CREATE INDEX idx_steps_run     ON agent_steps(run_id);
```

### 3.6 Caching Strategy

| Cache Key | Value | TTL | Purpose |
|---|---|---|---|
| `session:{jti}` | `user_id` | 1 hour | JWT fast-path validation |
| `rate:{user_id}` | request count | 60 seconds | Rate limiting window |
| `run:{run_id}` | LangGraph checkpoint JSON | 1 hour | Resume interrupted runs |
| `task:{task_id}` | TaskResponse JSON | 5 minutes | Read-through cache |
| `events:{run_id}` | pub/sub channel | — | SSE event bridge |

---

## 4. Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **Frontend** | Next.js + TypeScript | 14.x |
| **API Gateway** | Spring Boot | 3.2 (Java 17) |
| **Orchestrator** | FastAPI + LangGraph | 0.1.x |
| **LLM Framework** | LangChain | 0.2.x |
| **LLM Providers** | OpenAI / Anthropic Claude | — |
| **Primary DB** | PostgreSQL + pgvector | 16 |
| **Cache** | Redis (ElastiCache) | 7.x |
| **Object Store** | AWS S3 | — |
| **Containers** | Docker | 24.x |
| **Orchestration** | Kubernetes (AWS EKS) | 1.29 |
| **IaC** | Terraform | 1.7.x |
| **CI/CD** | GitHub Actions | — |
| **Container Registry** | AWS ECR | — |
| **Monitoring** | Prometheus + Grafana | — |
| **Logging** | CloudWatch Logs | — |

---

## 5. Cloud Architecture — AWS

### 5.1 Infrastructure Diagram

```
Region: us-east-1
┌────────────────────────────────────────────────────────────────────┐
│  VPC  10.0.0.0/16                                                  │
│                                                                    │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐   │
│  │  Public Subnet (10.0.1.0/24) │  │ Public Subnet (10.0.2.0) │   │
│  │  AZ: us-east-1a              │  │ AZ: us-east-1b            │   │
│  │  ┌────────────────────────┐  │  │                           │   │
│  │  │  Application Load      │  │  │  ALB (multi-AZ)           │   │
│  │  │  Balancer              │  │  │                           │   │
│  │  └────────────┬───────────┘  │  │                           │   │
│  └───────────────┼──────────────┘  └──────────────┬────────────┘   │
│                  │                                 │                │
│  ┌───────────────▼─────────────────────────────────▼────────────┐  │
│  │  Private Subnet (10.0.3.0/24 + 10.0.4.0/24)  [App Tier]     │  │
│  │                                                               │  │
│  │  EKS Node Group (EC2 t3.medium, min:2, max:6)               │  │
│  │  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐  │  │
│  │  │ api-gateway   │  │  orchestrator  │  │   frontend     │  │  │
│  │  │ pod (x2)      │  │  pod (x2)      │  │  pod (x1)      │  │  │
│  │  └───────────────┘  └────────────────┘  └────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Private Subnet (10.0.5.0/24 + 10.0.6.0/24)  [Data Tier]   │  │
│  │                                                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                 │  │
│  │  │ RDS PostgreSQL   │  │ ElastiCache Redis │                 │  │
│  │  │ (Multi-AZ)       │  │ (cluster mode)    │                 │  │
│  │  │ db.t3.medium     │  │ cache.t3.micro    │                 │  │
│  │  └──────────────────┘  └──────────────────┘                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  NAT Gateway (public subnet) → Internet Gateway                    │
└────────────────────────────────────────────────────────────────────┘

S3 Buckets (global): agentflow-artifacts, agentflow-frontend-static
CloudFront Distribution → S3 (frontend), ALB (API)
ECR: agentflow/api-gateway, agentflow/orchestrator
```

### 5.2 Networking — VPC Design

```
Internet
   │
   ▼
Internet Gateway (igw-agentflow)
   │
   ▼
CloudFront  ──► S3 (static frontend)
   │
   ▼
ALB (public subnets, port 443/80)
   │ Security Group: sg-alb (allow 443 from 0.0.0.0/0)
   ▼
EKS pods (private subnets)
   │ Security Group: sg-app (allow 8080 from sg-alb only)
   ▼
RDS/Redis (private subnets)
   │ Security Group: sg-data (allow 5432/6379 from sg-app only)
   ▼
NAT Gateway → Internet (for LLM API calls, package downloads)
```

### 5.3 IAM & Security

**Principle of least privilege — IRSA (IAM Roles for Service Accounts):**

```
EKS ServiceAccount: api-gateway-sa
  └── IAM Role: agentflow-api-gateway-role
       └── Policy: allow s3:GetObject on agentflow-artifacts/*
                   allow secretsmanager:GetSecretValue on agentflow/*

EKS ServiceAccount: orchestrator-sa
  └── IAM Role: agentflow-orchestrator-role
       └── Policy: allow s3:PutObject, s3:GetObject on agentflow-artifacts/*
                   allow secretsmanager:GetSecretValue on agentflow/*
```

**Secrets management:**
- Database password → AWS Secrets Manager → mounted as K8s secret via External Secrets Operator
- OpenAI/Anthropic API keys → AWS Secrets Manager
- JWT signing key → Secrets Manager
- NO secrets in environment variables or Git

---

## 6. DevOps Pipeline

### 6.1 CI/CD with GitHub Actions

```
Push to feature/* branch:
  ├── lint-and-test.yml
  │     ├── Java: mvn test (unit + integration)
  │     ├── Python: pytest, ruff lint
  │     └── TypeScript: tsc, eslint, jest
  └── (no deploy)

Push to main branch (after PR merge):
  ├── lint-and-test.yml  (same as above)
  ├── build-and-push.yml
  │     ├── Build Docker images (multi-stage)
  │     ├── Push to ECR: api-gateway:sha, orchestrator:sha, frontend:sha
  │     └── Tag as :latest
  └── deploy-staging.yml
        ├── kubectl set image deployment/api-gateway ...
        ├── kubectl set image deployment/orchestrator ...
        ├── kubectl rollout status (wait for rollout)
        └── Run smoke tests (curl /health)

Tag release/v*:
  └── deploy-prod.yml
        ├── Require manual approval (GitHub Environment protection)
        ├── Blue-green deploy via K8s deployment strategy
        └── Post to Slack on success/failure
```

### 6.2 Docker Strategy

**Multi-stage builds** to minimize image size:

```dockerfile
# api-gateway — ~200MB final (vs ~800MB single stage)
FROM eclipse-temurin:17-jdk-alpine AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline        # cache layer
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:17-jre-alpine   # runtime only
COPY --from=builder /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

```dockerfile
# orchestrator — ~450MB final
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt   # cached layer

FROM base
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.3 Kubernetes on EKS

**Deployment strategy** — rolling update with readiness gates:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # bring up 1 new pod before taking down old
    maxUnavailable: 0  # never reduce below desired replica count
```

**Horizontal Pod Autoscaler:**
```yaml
# Scale orchestrator based on CPU (LLM calls are CPU-bound waiting)
minReplicas: 2
maxReplicas: 8
metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
```

---

## 7. Monitoring & Observability

### Metrics (Prometheus + Grafana)

```
Custom metrics exposed at /metrics:

agentflow_task_total{status="success|failed"}      — task completion counter
agentflow_run_duration_seconds{agent="researcher"}  — per-agent latency histogram
agentflow_llm_tokens_total{model="gpt-4o"}          — token usage counter
agentflow_active_runs                               — current in-flight runs gauge
agentflow_revision_count_histogram                  — critic revision distribution
```

**Grafana dashboards:**
- Task throughput and error rate (4 golden signals)
- Per-agent latency P50/P95/P99
- LLM token usage and cost estimate
- EKS node CPU/memory
- RDS connection pool and slow queries

### Logging

Structured JSON logs on every service (correlation via `run_id`):
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "orchestrator",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent": "researcher",
  "message": "Tool call completed",
  "duration_ms": 1240,
  "token_count": 892
}
```

### Alerting (CloudWatch Alarms)

| Alert | Condition | Action |
|---|---|---|
| High error rate | `error_rate > 5%` for 5 min | PagerDuty |
| Slow LLM calls | `p99 > 30s` for 10 min | Slack |
| Pod crash loop | `restartCount > 3` | PagerDuty |
| DB connections | `> 80% of max_connections` | Slack |

---

## 8. Getting Started

### Prerequisites

- Docker Desktop 24+
- Java 17+, Maven 3.9+
- Python 3.11+
- Node.js 20+
- Terraform 1.7+ (for cloud deploy)
- AWS CLI (for cloud deploy)

### Local Development

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/agentflow.git
cd agentflow

# 2. Copy env template
cp .env.example .env
# Fill in OPENAI_API_KEY (or ANTHROPIC_API_KEY), JWT_SECRET

# 3. Start all services with Docker Compose
docker compose up --build

# Services will be available at:
# Frontend:      http://localhost:3000
# API Gateway:   http://localhost:8080
# Orchestrator:  http://localhost:8000
# PostgreSQL:    localhost:5432
# Redis:         localhost:6379

# 4. Run database migrations
docker compose exec orchestrator python -m alembic upgrade head

# 5. (Optional) Seed sample embeddings for RAG
docker compose exec orchestrator python utils/seed_embeddings.py
```

### Cloud Deployment (AWS)

```bash
# 1. Configure AWS credentials
aws configure

# 2. Provision infrastructure with Terraform
cd infra/terraform
terraform init
terraform plan -var-file="staging.tfvars"
terraform apply -var-file="staging.tfvars"

# 3. Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name agentflow-cluster

# 4. Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/

# 5. Verify pods are running
kubectl get pods -n agentflow
```

### Running Tests

```bash
# API Gateway (Java)
cd apps/api-gateway && mvn test

# Orchestrator (Python)
cd apps/orchestrator && pytest tests/ -v

# Frontend (TypeScript)
cd apps/frontend && npm test
```

---

## 9. API Reference

### Create Task
```
POST /api/tasks
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "description": "Research the top 5 EV companies and write a competitive analysis"
}

Response 202:
{
  "task_id": "550e8400-...",
  "run_id": "7f3c8200-...",
  "status": "RUNNING",
  "stream_url": "/api/tasks/550e8400-.../stream"
}
```

### Stream Task Progress (SSE)
```
GET /api/tasks/{task_id}/stream
Authorization: Bearer <jwt>
Accept: text/event-stream

data: {"type":"AGENT_START","agent":"researcher","timestamp":"..."}
data: {"type":"AGENT_DONE","agent":"researcher","output":"...","duration_ms":3200}
data: {"type":"AGENT_START","agent":"writer","timestamp":"..."}
data: {"type":"FINAL","output":"...","critic_score":0.91}
```

### Get Task Result
```
GET /api/tasks/{task_id}
Authorization: Bearer <jwt>

Response 200:
{
  "task_id": "...",
  "status": "DONE",
  "final_output": "...",
  "critic_score": 0.91,
  "revision_count": 1,
  "steps": [
    {"agent": "researcher", "duration_ms": 3200, "token_count": 892},
    {"agent": "writer",     "duration_ms": 5100, "token_count": 2140},
    {"agent": "critic",     "duration_ms": 1200, "token_count": 340}
  ]
}
```

---

## 10. Design Decisions & Trade-offs

| Decision | Chosen | Alternative | Reason |
|---|---|---|---|
| Agent framework | LangGraph | AutoGen, CrewAI | LangGraph gives explicit state machine control; better for production debugging |
| API gateway language | Spring Boot | Node.js / FastAPI | Plays to Java strengths; better enterprise auth/rate-limit libraries |
| Vector DB | pgvector on RDS | Pinecone, Weaviate | Fewer moving parts; no extra managed service; sufficient for <10M embeddings |
| Streaming | SSE | WebSockets | SSE is simpler (HTTP), sufficient for unidirectional agent events |
| Message passing | Redis pub/sub | Kafka, SQS | Low operational overhead; task volumes don't justify Kafka complexity |
| K8s ingress | AWS ALB Ingress | nginx ingress | Native AWS integration; TLS termination handled by ACM |
| IaC | Terraform | CDK, Pulumi | Widest industry adoption; most HCL examples for AWS |

---

## License

MIT — see [LICENSE](LICENSE)
