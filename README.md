# 🛡️ ChangeGuard

ChangeGuard is an automated AI-driven CI/CD deployment risk analysis system. It inspects incoming pull requests, diff patterns, historical incident logs, and live Kubernetes telemetry to determine whether code changes are safe for production deployment.

---

## 🏗️ Architecture Flow

```text
Code Change (GitHub PR)
       │
       ▼
GitHub Actions CI/CD
       │
       ▼
ChangeGuard API (`/analyze-change`)
       ├── 1. Git Diff Parser (Detects DB changes, sensitive modules)
       ├── 2. MCP Gateway (Live K8s health, rollback telemetry)
       ├── 3. pgvector RAG (Historical incident matching)
       └── 4. AI Risk Engine (LLM structured evaluation)
       │
       ▼
Risk Classification & Gate
  ├── Score < 30   ➜  ALLOW_AUTOMATIC_DEPLOYMENT
  ├── Score 30-70  ➜  REQUIRE_ADDITIONAL_TESTING
  └── Score > 70   ➜  REQUIRE_MANUAL_APPROVAL (Fails CI pipeline)
