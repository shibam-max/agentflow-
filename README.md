<div align="center">

```
 █████╗  ██████╗ ███████╗███╗   ██╗████████╗███████╗██╗      ██████╗ ██╗    ██╗
██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔════╝██║     ██╔═══██╗██║    ██║
███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   █████╗  ██║     ██║   ██║██║ █╗ ██║
██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██╔══╝  ██║     ██║   ██║██║███╗██║
██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ██║     ███████╗╚██████╔╝╚███╔███╔╝
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝
```

### Production-Grade Multi-Agent AI Task Automation Platform

*Four specialized AI agents collaborate in real time to complete any complex task you throw at them*

<br/>

[![CI](https://img.shields.io/github/actions/workflow/status/shibam-max/agentflow-/ci.yml?label=CI&logo=githubactions&logoColor=white&style=flat-square)](https://github.com/shibam-max/agentflow-/actions)
[![CD](https://img.shields.io/github/actions/workflow/status/shibam-max/agentflow-/cd.yml?label=CD%20%E2%80%94%20EKS&logo=amazonaws&logoColor=white&style=flat-square)](https://github.com/shibam-max/agentflow-/actions)
[![Java](https://img.shields.io/badge/Java%2017-Spring%20Boot%203.2-orange?style=flat-square&logo=spring&logoColor=white)](apps/api-gateway)
[![Python](https://img.shields.io/badge/Python%203.11-FastAPI%20%2B%20LangGraph-blue?style=flat-square&logo=python&logoColor=white)](apps/orchestrator)
[![Next.js](https://img.shields.io/badge/Next.js%2014-TypeScript-black?style=flat-square&logo=nextdotjs)](apps/frontend)
[![Terraform](https://img.shields.io/badge/IaC-Terraform%201.7-7B42BC?style=flat-square&logo=terraform)](infra/terraform)
[![Kubernetes](https://img.shields.io/badge/EKS-Kubernetes%201.29-326CE5?style=flat-square&logo=kubernetes&logoColor=white)](k8s)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<br/>

[Architecture](#-architecture) · [System Design](#-system-design) · [Tech Stack](#-tech-stack) · [Getting Started](#-getting-started) · [API Reference](#-api-reference) · [DevOps](#-devops-pipeline) · [Monitoring](#-monitoring--observability)

</div>

---

## What is AgentFlow?

AgentFlow is a **production-grade multi-agent AI platform** where four specialized agents collaborate to complete complex tasks. Submit a goal like *"Research the top 5 EV companies and write a competitive analysis"* and watch in real time as:

| Agent | Role | Tools |
|---|---|---|
| **Researcher** | Searches the web and retrieves context via RAG | DuckDuckGo, pgvector similarity search |
| **Writer** | Drafts structured documents and reports | GPT-4o / Claude via LangChain |
| **Coder** | Generates, validates, and explains code | Sandboxed Python execution |
| **Critic** | Scores quality (0–1) and triggers revision loops | LLM-based evaluation rubric |

The orchestrator runs a **directed graph** (LangGraph state machine) with conditional revision cycles. Results stream to the browser in real time via Server-Sent Events — no polling, no refresh.

---

## 🏗 Architecture

### System Overview

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                  CLIENT LAYER                               ║
║                                                                              ║
║   ┌─────────────────────────────────────────────────────────────────────┐   ║
║   │                    Next.js 14  (TypeScript)                         │   ║
║   │            React · SSE streaming · JWT cookie auth                  │   ║
║   │                S3 static hosting + CloudFront CDN                   │   ║
║   └─────────────────────────────┬───────────────────────────────────────┘   ║
╚═════════════════════════════════╪════════════════════════════════════════════╝
                                  │  HTTPS / SSE (text/event-stream)
╔═════════════════════════════════╪════════════════════════════════════════════╗
║                         AWS VPC │  us-east-1                                ║
║                                 │                                            ║
║   ┌─────────────────────────────▼───────────────────────────────────────┐   ║
║   │          APPLICATION LOAD BALANCER  (public subnets, ACM TLS)       │   ║
║   └──────────────┬──────────────────────────────────────────────────────┘   ║
║                  │                                                           ║
║   ╔══════════════▼══════════════════════════════════════════════════════╗   ║
║   ║              EKS NODE GROUP  (private subnets, t3.medium × 2–6)    ║   ║
║   ║                                                                     ║   ║
║   ║  ┌──────────────────────────────┐  ┌──────────────────────────┐   ║   ║
║   ║  │      API GATEWAY (×2 pods)   │  │  ORCHESTRATOR (×2–8 pods)│   ║   ║
║   ║  │      Spring Boot 3.2         │  │  FastAPI + LangGraph      │   ║   ║
║   ║  │      Java 17                 │  │  Python 3.11              │   ║   ║
║   ║  │                              │  │                           │   ║   ║
║   ║  │  · JWT auth (RS256)          │  │  ┌─────────────────────┐ │   ║   ║
║   ║  │  · Rate limiting (Redis)     │  │  │  Agent State Machine│ │   ║   ║
║   ║  │  · SSE bridge (pub/sub)      │  │  │  Researcher         │ │   ║   ║
║   ║  │  · Request validation        │◄─┤  │  Writer             │ │   ║   ║
║   ║  │  · Feign client proxy        │  │  │  Coder              │ │   ║   ║
║   ║  │                              │  │  │  Critic             │ │   ║   ║
║   ║  └──────────────────────────────┘  │  └─────────────────────┘ │   ║   ║
║   ║                                    │                           │   ║   ║
║   ║                                    │  · Prometheus /metrics    │   ║   ║
║   ║                                    └──────────────┬────────────┘   ║   ║
║   ╚══════════════════════════════════════════════════╪═════════════════╝   ║
║                                                      │ LLM API calls        ║
║                                                      ▼                       ║
║                                         ┌────────────────────┐               ║
║                                         │  OpenAI / Anthropic │               ║
║                                         │  (external HTTPS)   │               ║
║                                         └────────────────────┘               ║
║                                                                               ║
║   ╔═══════════════════════════════════════════════════════════════════════╗  ║
║   ║                    DATA LAYER  (private subnets)                      ║  ║
║   ║                                                                        ║  ║
║   ║  ┌─────────────────────┐  ┌──────────────────┐  ┌─────────────────┐  ║  ║
║   ║  │   PostgreSQL 16     │  │  ElastiCache      │  │   Amazon S3     │  ║  ║
║   ║  │   RDS Multi-AZ      │  │  Redis 7          │  │   (artifacts)   │  ║  ║
║   ║  │   + pgvector ext.   │  │  cluster mode     │  │                 │  ║  ║
║   ║  │                     │  │                   │  │                 │  ║  ║
║   ║  │  tasks · runs       │  │  sessions · rate  │  │  agent outputs  │  ║  ║
║   ║  │  agent_steps        │  │  limits · run     │  │  file uploads   │  ║  ║
║   ║  │  embeddings(vector) │  │  checkpoints      │  │                 │  ║  ║
║   ║  └─────────────────────┘  └──────────────────┘  └─────────────────┘  ║  ║
║   ╚═══════════════════════════════════════════════════════════════════════╝  ║
║                                                                               ║
║   ─────────────────────── DevOps Layer ───────────────────────────────────  ║
║   GitHub Actions → ECR  →  EKS   │  Terraform (IaC)  │  Prometheus+Grafana  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### AWS Infrastructure

```
Region: us-east-1
┌─────────────────────────────────────────────────────────────────────────┐
│  VPC  10.0.0.0/16                                                        │
│                                                                          │
│  ┌─────────────────────────┐    ┌─────────────────────────┐             │
│  │  Public Subnet          │    │  Public Subnet          │             │
│  │  10.0.1.0/24  (AZ: 1a) │    │  10.0.2.0/24  (AZ: 1b) │             │
│  │                         │    │                         │             │
│  │  ┌───────────────────┐  │    │  ┌───────────────────┐  │             │
│  │  │  ALB              ├──┼────┼──┤  ALB (Multi-AZ)   │  │             │
│  │  │  port 443 / 80    │  │    │  │  ACM TLS cert     │  │             │
│  │  └────────┬──────────┘  │    │  └────────┬──────────┘  │             │
│  │           │  NAT GW     │    │           │  NAT GW     │             │
│  └───────────┼─────────────┘    └───────────┼─────────────┘             │
│              │                              │                            │
│  ┌───────────▼──────────────────────────────▼──────────────────────┐   │
│  │  Private Subnet — App Tier                                        │   │
│  │  10.0.3.0/24 (AZ: 1a)    +    10.0.4.0/24 (AZ: 1b)             │   │
│  │                                                                   │   │
│  │  EKS Managed Node Group  (t3.medium, min:2 max:6, auto-scaling)  │   │
│  │  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │   │
│  │  │ api-gateway    │  │  orchestrator   │  │  frontend        │  │   │
│  │  │ pod (×2)       │  │  pod (×2–8)     │  │  pod (×1–3)      │  │   │
│  │  │ 250m–1 CPU     │  │  500m–2 CPU     │  │  100m–500m CPU   │  │   │
│  │  │ 512Mi–1Gi RAM  │  │  1Gi–2Gi RAM    │  │  256Mi–512Mi RAM │  │   │
│  │  └────────────────┘  └─────────────────┘  └──────────────────┘  │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Private Subnet — Data Tier                                       │   │
│  │  10.0.5.0/24 (AZ: 1a)    +    10.0.6.0/24 (AZ: 1b)             │   │
│  │                                                                   │   │
│  │  ┌───────────────────┐      ┌────────────────────────────────┐  │   │
│  │  │  RDS PostgreSQL   │      │  ElastiCache Redis              │  │   │
│  │  │  db.t3.medium     │      │  cache.t3.micro                 │  │   │
│  │  │  Multi-AZ standby │      │  2 nodes (prod)                 │  │   │
│  │  │  encrypted at rest│      │  transit encryption enabled     │  │   │
│  │  └───────────────────┘      └────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Security Groups:                                                        │
│  sg-alb  → allow 443/80 from 0.0.0.0/0                                  │
│  sg-app  → allow 8080/8000/3000 from sg-alb only                        │
│  sg-data → allow 5432/6379 from sg-app only                             │
│                                                                          │
│  NAT Gateway → Internet Gateway (for LLM API calls, package pulls)      │
└─────────────────────────────────────────────────────────────────────────┘

S3:         agentflow-artifacts-{account} (private, SSE-AES256)
CloudFront: → S3 (frontend static), → ALB (API)
ECR:        agentflow/api-gateway · agentflow/orchestrator · agentflow/frontend
```

---

## 🧠 System Design

### High-Level Design (HLD)

**Core principles driving every design decision:**

1. **Stateless compute, stateful data** — Pods hold no in-memory state. All workflow state lives in Redis. Any pod can pick up any request.
2. **Async by default** — LLM calls take 5–30s. Everything is async/non-blocking. HTTP 202 + SSE stream, never long-poll.
3. **Fail open, degrade gracefully** — Critic revision capped at 3. LLM timeout at 30s with retry. Final output always returned even if imperfect.

**Component responsibilities at a glance:**

```
Next.js Frontend
  └─ Renders task form, streams agent steps via EventSource API
  └─ JWT stored in HttpOnly cookie (XSS-safe)
  └─ Deployed to S3 + served via CloudFront (global CDN, ~10ms TTFB)

Spring Boot API Gateway          ← your Java strength, fully leveraged
  └─ Single ingress for all client requests
  └─ JWT validation: Redis cache (0.5ms) → HMAC verify (2ms) → cache result
  └─ Rate limit: Redis INCR + TTL token bucket (10 req/min/user)
  └─ SSE bridge: subscribes Redis pub/sub → pushes to browser EventSource
  └─ Feign client proxies /api/tasks → FastAPI orchestrator (internal only)

FastAPI Orchestrator
  └─ Receives task, instantiates LangGraph DAG, runs async
  └─ Each agent node: calls LLM → publishes event to Redis pub/sub
  └─ Checkpoints state to Redis after each node (resumable on pod crash)
  └─ Persists final result to PostgreSQL, artifacts to S3

LangGraph State Machine
  └─ Typed AgentState dict flows through: Researcher → Writer → Coder → Critic
  └─ Conditional edge: critic_score ≥ 0.8 → finalize, else → researcher (max 3)
  └─ Fully deterministic, testable, loggable — no black-box agent conversation

PostgreSQL + pgvector
  └─ Relational data: tasks, runs, agent_steps
  └─ Vector data: document embeddings for RAG (IVFFlat index, cosine similarity)
  └─ pgvector chosen over Pinecone: fewer moving parts, <1M vectors, no extra cost

ElastiCache Redis
  └─ Session cache, rate limit counters, run checkpoints, pub/sub event bus
  └─ Redis pub/sub chosen over Kafka: zero ops overhead, sufficient durability*
  *SSE client reconnects in 3s and replays from agent_steps table on reconnect
```

### Low-Level Design (LLD)

#### LangGraph Agent State Machine

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                         AgentState  (TypedDict)                          │
 │                                                                          │
 │  task_description : str       research_output  : str | None             │
 │  task_id          : str       draft_output     : str | None             │
 │  run_id           : str       code_output      : str | None             │
 │  revision_count   : int       critic_score     : float | None           │
 │                               critic_feedback  : str | None             │
 │                               final_output     : str | None             │
 └─────────────────────────────────────────────────────────────────────────┘

START
  │
  ▼
┌──────────────────────────────────────┐
│  researcher_node                      │
│                                       │
│  1. DuckDuckGo web search             │
│  2. pgvector RAG retrieval (top-5)    │
│  3. LLM synthesizes research brief   │
│  4. Publishes AGENT_DONE event        │
└──────────────────────┬───────────────┘
                       │
                       ▼
┌──────────────────────────────────────┐
│  writer_node                          │
│                                       │
│  1. Receives research brief           │
│  2. LLM drafts structured document   │
│  3. Publishes AGENT_DONE event        │
└──────────────────────┬───────────────┘
                       │
                       ▼
┌──────────────────────────────────────┐
│  coder_node                           │
│                                       │
│  1. Checks if task needs code         │
│     (keyword match on description)   │
│  2. LLM generates + explains code    │
│  3. Publishes AGENT_DONE event        │
└──────────────────────┬───────────────┘
                       │
                       ▼
┌──────────────────────────────────────┐
│  critic_node                          │
│                                       │
│  1. Evaluates: completeness,          │
│     accuracy, clarity, relevance      │
│  2. Outputs: SCORE (0.0–1.0) +        │
│     FEEDBACK (actionable text)        │
│  3. Publishes AGENT_DONE event        │
└──────────────────────┬───────────────┘
                       │
          ┌────────────▼───────────────┐
          │  conditional_edge()         │
          │                            │
          │  score ≥ 0.8?  ────YES───► finalize_node ──► END
          │                            │
          │  revision_count ≥ 3? ─YES─► finalize_node ──► END
          │                            │
          │  else ──────────────────NO─► researcher_node (loop)
          └────────────────────────────┘
```

#### JWT Authentication Flow

```
Client Request
│
├─ Header: "Authorization: Bearer <jwt>"
│
▼
JwtAuthFilter.doFilterInternal()
│
├─ Extract token from header
│
├─ Compute cache key: "session:" + last 20 chars of token
│
├─ Redis GET cache_key  ──── HIT (~0.5ms) ────► userId found
│                                                    │
└─ MISS (~2ms)                                      │
    │                                               │
    ├─ Jwts.parser().verifyWith(hmacKey)            │
    ├─ Parse claims, extract subject (userId)        │
    ├─ Redis SET cache_key userId EX 3600           │
    └──────────────────────────────────────────────►│
                                                    │
                                                    ▼
                                    SecurityContextHolder.setAuth()
                                                    │
                                                    ▼
                                          Controller proceeds
```

#### Rate Limiting (Token Bucket via Redis)

```java
// Per-user, per-minute window — atomic, no race conditions
String key = "rate:" + userId;
Long count = redis.incr(key);          // atomic increment
if (count == 1) redis.expire(key, 60); // first hit → set 60s window
if (count > 10) throw new RateLimitException("10 req/min exceeded");
// proceeds normally
```

#### SSE Bridge (Redis Pub/Sub → Browser)

```
Orchestrator                Redis                   Spring Boot           Browser
    │                         │                          │                   │
    │  PUBLISH events:{runId} │                          │                   │
    ├────────────────────────►│                          │                   │
    │                         │  SUBSCRIBE events:{runId}│                   │
    │                         │◄─────────────────────────┤                   │
    │                         │                          │  GET /stream      │
    │                         │                          │◄──────────────────┤
    │                         │  message received         │                   │
    │                         ├─────────────────────────►│                   │
    │                         │                          │  SSE event push   │
    │                         │                          ├──────────────────►│
    │                         │                          │                   │
    │  PUBLISH {type:"FINAL"} │                          │                   │
    ├────────────────────────►│                          │                   │
    │                         ├─────────────────────────►│                   │
    │                         │                          │  SSE close        │
    │                         │                          ├──────────────────►│
```

#### Database Schema

```sql
-- tasks: user-submitted goals
CREATE TABLE tasks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    description TEXT NOT NULL,
    status      VARCHAR(20) DEFAULT 'PENDING',  -- PENDING|RUNNING|DONE|FAILED
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_tasks_user   ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);

-- runs: workflow executions (1 task → many runs via retry)
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
CREATE INDEX idx_runs_task   ON runs(task_id);
CREATE INDEX idx_runs_status ON runs(status);

-- agent_steps: granular per-agent outputs for debugging + observability
CREATE TABLE agent_steps (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id      UUID REFERENCES runs(id),
    agent_name  VARCHAR(50) NOT NULL,  -- researcher|writer|coder|critic
    input       JSONB,
    output      TEXT,
    duration_ms INT,
    token_count INT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_steps_run ON agent_steps(run_id);

-- embeddings: pgvector RAG store
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content    TEXT NOT NULL,
    embedding  vector(1536),          -- OpenAI text-embedding-3-small
    metadata   JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- IVFFlat index: fast approximate nearest-neighbor, good up to ~1M vectors
CREATE INDEX ON embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

#### Caching Strategy

| Key Pattern | Value | TTL | Purpose |
|---|---|---|---|
| `session:{token_suffix}` | `user_id` | 1 hour | JWT fast-path, avoids crypto on every request |
| `rate:{user_id}` | request count | 60 sec | Sliding window rate limit |
| `run:{run_id}` | LangGraph checkpoint JSON | 1 hour | Resume interrupted runs after pod crash |
| `task:{task_id}` | TaskResponse JSON | 5 min | Read-through cache for GET /tasks/{id} |
| `events:{run_id}` | — | — | Redis pub/sub channel for SSE bridge |

### Non-Functional Requirements

| Requirement | Target | Implementation |
|---|---|---|
| **Task throughput** | 100 concurrent runs | HPA on orchestrator (max 8 pods × 25 async runs each) |
| **API latency (p99)** | < 500ms | Redis session cache eliminates DB on hot path |
| **Streaming lag** | < 200ms | Redis pub/sub, SSE (no WebSocket handshake overhead) |
| **Availability** | 99.9% | Multi-AZ RDS, EKS node groups across 2 AZs, ALB health checks |
| **Fault tolerance** | Run resumes on pod crash | LangGraph checkpoint stored in Redis after every node |
| **Security** | JWT + network isolation | Private subnets, SGs deny-by-default, IRSA least-privilege |
| **Observability** | Full trace per run | `run_id` correlation across all logs, metrics, and DB rows |

### Capacity Estimation

```
Assumptions:
  1,000 DAU × 5 tasks/day = 5,000 tasks/day = ~3.5 tasks/second (peak)
  Average run: 4 agents × 8s = ~32s wall clock time
  Average tokens: 1,500 input + 800 output = 2,300 tokens/run

Concurrency:
  3.5 tasks/sec × 32s per run = ~112 concurrent runs (steady state)
  2× headroom → 224 concurrent runs at peak
  Each orchestrator pod: 25 async runs
  Pods needed at peak: 224 / 25 = ~9  →  HPA max 8 (safe ceiling with queuing)

Storage (1 year):
  Tasks table:      1.8M rows × 500B  ≈ 900MB
  Agent steps:      7.3M rows × 2KB   ≈ 14GB
  Vector embeddings: 100K × 6KB       ≈ 600MB
  S3 artifacts:     5K/day × 5KB × 365 ≈ 9GB

LLM cost (gpt-4o-mini at $0.15/1M tokens):
  5,000 runs/day × 2,300 tokens = 11.5M tokens/day
  Daily cost: ~$1.73  |  Monthly: ~$52
```

### Failure Modes & Mitigations

| Failure Scenario | Impact | Detection | Mitigation |
|---|---|---|---|
| LLM API timeout | Agent hangs | 30s per-call timeout | Exponential backoff retry (max 3×), fallback to partial output |
| Orchestrator pod OOM kill | Run lost mid-flight | K8s liveness probe | Redis checkpoint: new pod resumes from last completed node |
| Redis connection drop | SSE stream breaks | Lettuce health check | EventSource auto-reconnects (3s); gateway replays last 10 events from DB |
| RDS Multi-AZ failover | ~30s DB unavailable | RDS CloudWatch event | HikariCP retries connection on failover; reads served from Redis cache |
| OpenAI rate limit (429) | Agent fails | HTTP response code | Token bucket backpressure; queued with jitter; user notified via SSE |
| Critic infinite loop | Run never terminates | Revision counter | Hard cap: `revision_count >= 3` always routes to finalize |
| Network partition (VPC) | Service-to-service call fails | ALB health checks | K8s pod restarts; circuit breaker via Spring Resilience4j (future) |

---

## ⚙️ Tech Stack

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| **Frontend** | Next.js + TypeScript | 14.x | SSR, App Router, native SSE via `EventSource` |
| **API Gateway** | Spring Boot | 3.2 (Java 17) | Leverages existing Java strengths; mature auth + rate-limit ecosystem |
| **Orchestrator** | FastAPI + LangGraph | 0.111 / 0.1.x | LangGraph = explicit typed state machine; best for production debugging |
| **LLM Framework** | LangChain | 0.2.x | Unified interface for OpenAI/Anthropic/tool calling |
| **LLM Providers** | OpenAI gpt-4o-mini / Anthropic Claude | — | Swappable via env var |
| **Vector Store** | pgvector on PostgreSQL 16 | — | No extra service; sufficient for <1M vectors; SQL joins with relational data |
| **Cache / Pub-Sub** | Redis 7 (ElastiCache) | — | Session cache + rate limiting + SSE event bus + run checkpoints |
| **Object Storage** | Amazon S3 | — | Agent artifacts, file uploads, Terraform state |
| **Containers** | Docker (multi-stage builds) | 24.x | API gateway: ~200MB image; orchestrator: ~450MB |
| **Orchestration** | Kubernetes on AWS EKS | 1.29 | HPA, rolling deploys, IRSA, namespace isolation |
| **IaC** | Terraform | 1.7.x | VPC, EKS, RDS, ElastiCache, S3, ECR, Secrets Manager |
| **CI/CD** | GitHub Actions | — | Lint → test → build → ECR push → EKS deploy → smoke test |
| **Metrics** | Prometheus + Grafana | — | Custom agent metrics + K8s golden signals |
| **Logging** | Structured JSON → CloudWatch | — | `run_id` correlation across all services |
| **Secrets** | AWS Secrets Manager + ESO | — | Zero secrets in env vars or Git |

---

## 📁 Repository Structure

```
agentflow/
│
├── apps/
│   ├── api-gateway/                    # Spring Boot — Java 17
│   │   ├── src/main/java/com/agentflow/
│   │   │   ├── AgentFlowApplication.java
│   │   │   ├── controller/
│   │   │   │   ├── TaskController.java      # POST /api/tasks, GET, SSE stream
│   │   │   │   └── AuthController.java      # login, token refresh
│   │   │   ├── filter/
│   │   │   │   └── JwtAuthFilter.java       # per-request JWT + Redis cache
│   │   │   ├── service/
│   │   │   │   ├── TaskService.java         # business logic, Feign client
│   │   │   │   ├── StreamService.java       # Redis pub/sub → SseEmitter
│   │   │   │   └── RateLimitService.java    # token bucket via Redis INCR
│   │   │   ├── config/
│   │   │   │   ├── SecurityConfig.java      # Spring Security filter chain
│   │   │   │   └── RedisConfig.java         # Lettuce pool config
│   │   │   └── dto/
│   │   │       ├── TaskRequest.java         # @NotBlank @Size validation
│   │   │       └── TaskResponse.java        # @Builder response shape
│   │   ├── src/main/resources/
│   │   │   └── application.yml             # Spring config (env-driven)
│   │   ├── Dockerfile                      # multi-stage, non-root user
│   │   └── pom.xml
│   │
│   ├── orchestrator/                   # FastAPI + LangGraph — Python 3.11
│   │   ├── main.py                         # FastAPI app, lifespan, routes, Prometheus
│   │   ├── graph/
│   │   │   └── workflow.py                 # LangGraph DAG + conditional edges
│   │   ├── agents/
│   │   │   ├── researcher.py               # web search + RAG retrieval
│   │   │   ├── writer.py                   # structured document drafting
│   │   │   ├── coder.py                    # code generation (conditional)
│   │   │   └── critic.py                   # scoring + feedback (0.0–1.0)
│   │   ├── tools/
│   │   │   └── rag_tool.py                 # pgvector similarity search
│   │   ├── db/
│   │   │   ├── postgres.py                 # asyncpg connection pool
│   │   │   └── redis_client.py             # aioredis client
│   │   ├── utils/
│   │   │   └── events.py                   # Redis pub/sub publisher
│   │   ├── models/
│   │   │   └── schemas.py                  # Pydantic request/response
│   │   ├── migrations/
│   │   │   └── versions/001_initial.py     # Alembic migration
│   │   ├── tests/
│   │   │   └── test_workflow.py            # routing logic unit tests
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── frontend/                       # Next.js 14 — TypeScript
│       ├── src/
│       │   ├── app/
│       │   │   ├── page.tsx                # task submission + timeline
│       │   │   ├── layout.tsx              # root layout
│       │   │   └── globals.css             # CSS variables, dark mode
│       │   ├── components/
│       │   │   └── AgentCard.tsx           # agent step card with timing
│       │   └── lib/
│       │       ├── api.ts                  # typed fetch wrappers
│       │       ├── types.ts                # shared TypeScript interfaces
│       │       └── useAgentStream.ts       # EventSource SSE hook
│       ├── Dockerfile                      # multi-stage, standalone output
│       └── package.json
│
├── infra/
│   ├── terraform/
│   │   ├── main.tf                     # VPC, EKS, RDS, ElastiCache, S3, ECR
│   │   ├── variables.tf                # typed vars with validation
│   │   ├── outputs.tf                  # cluster, DB, Redis endpoints
│   │   └── staging.tfvars             # staging environment values
│   ├── prometheus.yml                  # Prometheus scrape config (K8s SD)
│   └── alerts.yml                      # alerting rules (5 golden signal alerts)
│
├── k8s/
│   ├── namespace.yaml                  # agentflow namespace
│   ├── serviceaccounts.yaml            # IRSA service accounts
│   ├── api-gateway.yaml                # Deployment + Service + HPA
│   ├── orchestrator.yaml               # Deployment + Service + HPA
│   └── ingress.yaml                    # ALB Ingress (ACM TLS)
│
├── .github/
│   └── workflows/
│       ├── ci.yml                      # lint + test (all 3 services + Terraform)
│       └── cd.yml                      # build → ECR → EKS staging → prod (gated)
│
├── docs/
│   └── SYSTEM_DESIGN.md               # extended design: capacity, trade-offs, failures
│
├── docker-compose.yml                  # full local dev stack
├── Makefile                            # make up / down / test / migrate / logs
├── .env.example                        # all required env vars documented
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites

```
Docker Desktop 24+     Java 17 + Maven 3.9+     Python 3.11+
Node.js 20+            Terraform 1.7+ (cloud)   AWS CLI (cloud)
```

### Run Locally (5 minutes)

```bash
# 1. Clone and configure
git clone https://github.com/shibam-max/agentflow-.git
cd agentflow-
cp .env.example .env
# Fill in OPENAI_API_KEY or ANTHROPIC_API_KEY, and JWT_SECRET (min 32 chars)

# 2. Start everything
make up
# or: docker compose up --build -d

# 3. Run database migrations
make migrate
# or: docker compose exec orchestrator python -m alembic upgrade head

# Services running at:
#   Frontend:     http://localhost:3000
#   API Gateway:  http://localhost:8080
#   Orchestrator: http://localhost:8000/docs  (Swagger UI)
#   Prometheus:   http://localhost:9090

# 4. Run all tests
make test
```

### Deploy to AWS (30 minutes)

```bash
# 1. Bootstrap Terraform state bucket
aws s3 mb s3://agentflow-tf-state --region us-east-1

# 2. Provision AWS infrastructure
cd infra/terraform
terraform init
terraform plan -var-file="staging.tfvars"
terraform apply -var-file="staging.tfvars"
# Creates: VPC, EKS, RDS, ElastiCache, S3, ECR repos, Secrets Manager entries

# 3. Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name agentflow-staging

# 4. Push your first images (CI/CD will do this on every merge after setup)
make docker-push ENV=staging

# 5. Deploy to Kubernetes
kubectl apply -f k8s/
kubectl get pods -n agentflow  # watch pods come up

# 6. Run migrations against RDS
kubectl exec -it deploy/orchestrator -n agentflow -- python -m alembic upgrade head
```

### GitHub Actions Setup

Add these secrets in **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user key with ECR push + EKS deploy permissions |
| `AWS_SECRET_ACCESS_KEY` | Corresponding secret |
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |
| `SLACK_WEBHOOK_URL` | Slack app incoming webhook (for deploy notifications) |

Add these **Environments** in Settings → Environments:
- `staging` — no approval required
- `production` — requires manual approval (protects prod)

---

## 📡 API Reference

### POST /api/tasks — Create a task

```http
POST /api/tasks
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "description": "Research the top 5 EV companies and write a competitive analysis"
}
```

```json
// 202 Accepted
{
  "task_id":   "550e8400-e29b-41d4-a716-446655440000",
  "run_id":    "7f3c8200-4f1b-11ee-be56-0242ac120002",
  "status":    "RUNNING",
  "stream_url": "/api/tasks/550e8400-.../stream"
}
```

### GET /api/tasks/:id/stream — Real-time SSE

```http
GET /api/tasks/550e8400-.../stream
Authorization: Bearer <jwt>
Accept: text/event-stream
```

```
data: {"type":"AGENT_START","agent":"researcher","timestamp":"2024-01-15T10:30:00Z"}

data: {"type":"AGENT_DONE","agent":"researcher","output":"Research brief...","duration_ms":3241}

data: {"type":"AGENT_START","agent":"writer","timestamp":"2024-01-15T10:30:03Z"}

data: {"type":"AGENT_DONE","agent":"writer","output":"Competitive analysis...","duration_ms":5102}

data: {"type":"AGENT_DONE","agent":"coder","output":null,"duration_ms":12}

data: {"type":"AGENT_DONE","agent":"critic","output":"Score: 0.91...","duration_ms":1203}

data: {"type":"FINAL","output":"## Competitive Analysis...","critic_score":0.91,"revision_count":0}
```

### GET /api/tasks/:id — Get result

```json
// 200 OK
{
  "task_id":        "550e8400-...",
  "status":         "DONE",
  "final_output":   "## Competitive Analysis of Top 5 EV Companies...",
  "critic_score":   0.91,
  "revision_count": 0,
  "steps": [
    { "agent": "researcher", "duration_ms": 3241, "token_count": 892  },
    { "agent": "writer",     "duration_ms": 5102, "token_count": 2140 },
    { "agent": "coder",      "duration_ms": 12,   "token_count": 0    },
    { "agent": "critic",     "duration_ms": 1203, "token_count": 340  }
  ]
}
```

---

## 🔁 DevOps Pipeline

### CI/CD Flow

```
Feature branch push
  └─► ci.yml
        ├── Java: mvn test + checkstyle
        ├── Python: pytest + ruff lint
        ├── TypeScript: tsc + eslint + jest
        └── Terraform: init + validate + fmt check

Merge to main
  └─► ci.yml  (same gates)
  └─► cd.yml
        ├── Build 3 Docker images (multi-stage, layer-cached via ECR)
        ├── Tag: {sha[:8]} + latest
        ├── Push to ECR
        ├── kubectl set image → EKS staging
        ├── kubectl rollout status (wait for healthy rollout)
        └── Smoke test: curl /actuator/health

Tag release/v*
  └─► cd.yml  (continues from staging)
        ├── Manual approval gate (GitHub Environment protection)
        ├── kubectl set image → EKS prod
        ├── kubectl rollout status --timeout=10m
        └── Slack notification (success or failure)
```

### Docker Strategy (Multi-Stage Builds)

```dockerfile
# api-gateway: 800MB → 195MB final image
FROM eclipse-temurin:17-jdk-alpine AS builder
  mvn dependency:go-offline   # cached layer
  mvn package -DskipTests

FROM eclipse-temurin:17-jre-alpine  # runtime only, no JDK
  COPY --from=builder target/*.jar app.jar
  USER appuser  # non-root

# orchestrator: single-stage slim image, ~450MB
FROM python:3.11-slim
  pip install --no-cache-dir -r requirements.txt  # cached layer
  COPY . .
  USER appuser
```

### Kubernetes Deployment Strategy

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # bring up 1 new pod before terminating old
    maxUnavailable: 0  # never drop below desired replica count
```

Zero-downtime deploys guaranteed. Combined with readiness probes — new pods only receive traffic once healthy.

---

## 📊 Monitoring & Observability

### Custom Prometheus Metrics

```
# Orchestrator (Python — prometheus_client)
agentflow_task_total{status="success|failed"}     Counter  — task completion rate
agentflow_run_duration_seconds{agent="..."}        Histogram — per-agent latency
agentflow_llm_tokens_total{model="gpt-4o-mini"}   Counter  — token usage + cost tracking
agentflow_active_runs                              Gauge    — concurrent workflow count
agentflow_revision_count_bucket                   Histogram — critic revision distribution

# API Gateway (Spring Boot — Micrometer)
http_server_requests_seconds{uri="/api/tasks"}    Histogram — API latency
rate_limit_rejections_total{user_id="..."}         Counter  — rate limit hits
```

### Structured Logging (JSON, run_id correlated)

```json
{
  "time":       "2024-01-15T10:30:03Z",
  "level":      "INFO",
  "service":    "orchestrator",
  "run_id":     "7f3c8200-4f1b-11ee-be56-0242ac120002",
  "agent":      "researcher",
  "msg":        "Agent completed",
  "duration_ms": 3241,
  "token_count": 892
}
```

Every log line carries `run_id` — trace a complete task execution across all services with a single CloudWatch Insights query:

```sql
fields @timestamp, service, agent, msg, duration_ms
| filter run_id = "7f3c8200-4f1b-11ee-be56-0242ac120002"
| sort @timestamp asc
```

### Alerting Rules

| Alert | Condition | Severity | Action |
|---|---|---|---|
| High error rate | `failed_tasks / total_tasks > 5%` for 5m | Critical | PagerDuty |
| Slow LLM calls | `p99 run_duration > 30s` for 10m | Warning | Slack |
| Active runs spike | `active_runs > 80` for 2m | Warning | Slack |
| Pod crash loop | `restart_count > 3` in 15m | Critical | PagerDuty |
| Memory pressure | `memory_usage > 85%` for 5m | Warning | Slack |

---

## 🔐 Security

| Concern | Implementation |
|---|---|
| **Auth** | JWT (HMAC-SHA256), stateless, validated per request |
| **Token storage** | HttpOnly cookies — immune to XSS |
| **Secret management** | AWS Secrets Manager → K8s External Secrets Operator — zero secrets in Git or env vars |
| **Network isolation** | Orchestrator + DB in private subnets — no public IPs |
| **Least privilege** | IRSA: each pod's service account maps to a scoped IAM role |
| **Image scanning** | ECR scan-on-push for CVEs |
| **Encryption** | RDS encrypted at rest (AES-256), ElastiCache transit encryption, S3 SSE |
| **Rate limiting** | 10 req/min per user via Redis token bucket |

---

## 🧩 Design Decisions & Trade-offs

| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| Agent framework | **LangGraph** | AutoGen, CrewAI | Explicit typed state machine — every state transition is inspectable, testable, loggable. AutoGen's conversation model is harder to debug in prod. |
| API gateway language | **Spring Boot** | Node.js / FastAPI | Plays to existing Java strength. Better enterprise auth, rate-limit, and observability ecosystem out of the box. |
| Vector DB | **pgvector on RDS** | Pinecone, Weaviate | One fewer managed service. No extra cost. SQL joins with relational data. Sufficient for <1M vectors. Interface is swappable — see `rag_tool.py`. |
| Streaming protocol | **SSE** | WebSockets | SSE is unidirectional — matches agent event model exactly. HTTP-native, load-balancer friendly, `EventSource` auto-reconnects. |
| Message bus | **Redis pub/sub** | Kafka, SQS | Zero ops overhead. On disconnect, SSE client reconnects and replays from `agent_steps` table, compensating for pub/sub's lack of durability. |
| IaC | **Terraform** | AWS CDK, Pulumi | Widest industry adoption. Most HCL examples for AWS. Declarative state makes drift detection easy. |
| Auth storage | **HttpOnly cookies** | localStorage | XSS-safe. Browser sends automatically. No manual `Authorization` header management. |

---

## 🗺 Roadmap

- [ ] **WebSocket fallback** for environments blocking SSE
- [ ] **OpenTelemetry distributed tracing** (trace_id across all services → Jaeger)
- [ ] **Agent memory** — persist past run summaries in vector store, inject as context
- [ ] **Custom agent builder** — UI to define agent roles and tool sets without code
- [ ] **Multi-tenant isolation** — per-org vector namespaces, usage quotas
- [ ] **Cost dashboard** — per-user token spend tracked via Prometheus + Grafana

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

Built by **[Shibam](https://github.com/shibam-max)** · SDE 2 → AI Engineer

*Full-stack · Cloud-native · Production-grade · AI-powered*

⭐ Star this repo if it helped you understand production AI systems

</div>
