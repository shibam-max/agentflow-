# AgentFlow — System Design Deep Dive

This document provides extended design rationale beyond what fits in the main README. Intended for system design discussions and interviews.

---

## Capacity Estimation

**Assumptions:**
- 1,000 daily active users
- Average 5 tasks/user/day → 5,000 tasks/day → ~3.5 tasks/second peak
- Average run: 4 agents × 8s each = ~32s total wall clock time
- Average LLM response: ~1,500 tokens input + 800 tokens output = 2,300 tokens/run
- Average artifact size: 5KB

**Storage (1 year):**
```
Tasks:           5,000/day × 365 = 1.825M rows × ~500B = ~900MB
Agent steps:     4 steps/task × 1.825M = 7.3M rows × ~2KB = ~14GB
Embeddings:      ~100K chunks × 1536 floats × 4B = ~600MB
S3 artifacts:    5,000/day × 5KB × 365 = ~9GB
```

**Concurrency:**
- At 3.5 tasks/sec and 32s per run → ~112 concurrent runs at steady state
- Peaks to ~200 with 2× headroom
- Each orchestrator pod handles ~25 concurrent async runs
- Need: 200 / 25 = 8 orchestrator pods at peak → HPA max 8 is correct

**LLM costs (rough):**
- 5,000 tasks/day × 2,300 tokens = 11.5M tokens/day
- At $0.15/1M tokens (gpt-4o-mini) = ~$1.73/day = ~$52/month

---

## Failure Modes and Mitigations

| Failure | Impact | Detection | Mitigation |
|---|---|---|---|
| LLM API timeout | Run hangs | 30s timeout per agent call | Retry with exponential backoff (max 3), fallback to degraded output |
| Orchestrator pod OOM | Run lost | K8s liveness probe | Redis checkpoint: resume from last completed node on pod restart |
| Redis connection drop | SSE breaks | Health check | Client auto-reconnects SSE after 3s; gateway buffers last 10 events |
| RDS failover (Multi-AZ) | ~30s downtime | RDS event | Spring Boot HikariCP retries connection on failover |
| Rate limit hit (OpenAI) | 429 error | Response code | Queue with token bucket, back-pressure to user via SSE event |
| Critic infinite loop | Run never completes | `revision_count >= 3` guard | Hard cap enforced in `route_after_critic()` |

---

## Scaling Considerations

**Stateless services (API gateway, orchestrator):** Scale horizontally with no coordination needed. HPA handles this.

**LangGraph state:** Stored in Redis (`run:{run_id}`), not in pod memory. Any orchestrator pod can resume any run — this is the key design decision that enables horizontal scaling.

**Database connection pooling:** HikariCP (Spring Boot) and asyncpg pool (Python) both configured with `max_size=20`. With 4 pods, that's 80 connections to RDS. RDS `db.t3.medium` supports 170 max connections — safe headroom.

**pgvector at scale:** IVFFlat index with 100 lists performs well up to ~1M vectors. Beyond that, migrate to HNSW index or a dedicated vector DB (Pinecone/Weaviate). The interface in `rag_tool.py` is swappable without changing agent code.

---

## API Design Decisions

**Why SSE over WebSockets?**
- SSE is unidirectional (server → client), which matches our use case exactly
- HTTP/1.1 compatible — no upgrade handshake
- Automatic reconnect built into `EventSource` browser API
- Simpler to scale (stateless HTTP, proxied by ALB)
- WebSockets would add complexity for no benefit here

**Why REST over GraphQL?**
- Simple CRUD operations with no complex query graph
- Better caching with HTTP semantics
- Fewer moving parts; Spring Boot REST is battle-tested

**Why async task creation (202 Accepted) over synchronous?**
- LLM workflows take 30–60 seconds
- Synchronous would require long-lived HTTP connections and load balancer timeout tuning
- 202 + SSE stream is the standard pattern for long-running AI jobs

---

## Security Model

**JWT validation (stateless):**
```
Token → JwtAuthFilter
  ├── Check Redis cache (fast path, ~0.5ms)
  └── Parse + verify HMAC-SHA256 (slow path, ~2ms)
       └── Cache result for remaining TTL
```

**Network isolation:**
- Orchestrator has no public IP, only reachable from API gateway pods via K8s DNS
- Database and Redis only reachable from app-tier security group
- All inter-service communication inside VPC; no public internet

**Secrets rotation:**
- DB password stored in Secrets Manager, rotated every 90 days
- K8s External Secrets Operator syncs to K8s Secret on rotation
- Pod restarts automatically pick up new secret values

---

## Observability Strategy (4 Golden Signals)

| Signal | Metric | Source |
|---|---|---|
| Latency | `agentflow_run_duration_seconds` histogram | Orchestrator Prometheus |
| Traffic | `agentflow_task_total` counter | Orchestrator Prometheus |
| Errors | `agentflow_task_total{status="failed"}` rate | Orchestrator Prometheus |
| Saturation | `agentflow_active_runs` gauge | Orchestrator Prometheus |

**Distributed tracing** (future): Add OpenTelemetry SDK to all three services with `run_id` as the trace correlation key. Export to AWS X-Ray or Jaeger.

---

## Trade-off Log

**pgvector vs Pinecone:**
Chose pgvector to keep infrastructure simple — one fewer managed service, one fewer bill, no SDK to learn. Trade-off: pgvector's IVFFlat requires re-indexing as the table grows; Pinecone handles this automatically. Revisit when embeddings table exceeds 1M rows.

**Redis pub/sub vs Kafka:**
Redis pub/sub is fire-and-forget — if the subscriber (API gateway) disconnects, events are lost. Kafka would give durability and replay. However: at our scale, the SSE client reconnects within 3s and requests missed events from the `agent_steps` DB table. This compensates for the lack of durability without Kafka's operational overhead.

**LangGraph vs AutoGen:**
LangGraph exposes the state machine explicitly as a typed Python dict. This means every agent's input/output is inspectable, testable, and loggable. AutoGen's conversational model is more flexible but harder to debug in production. For a product requiring reliability guarantees, explicit state wins.
