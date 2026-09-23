from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, make_asgi_app
from app.config import settings
from app.models import init_db, SessionLocal, DeploymentLog, ChangeAnalysisRequest, RiskAnalysisResponse
from app.analyzer import GitDiffAnalyzer
from app.mcp_tools import MCPRuntime
from app.rag import IncidentRAG
from app.ai_engine import RiskEngine

app = FastAPI(title="ChangeGuard Production Gate")

ANALYSIS_COUNTER = Counter("changeguard_requests_total", "Total change scans", ["status"])
RISK_HISTOGRAM = Histogram("changeguard_risk_score", "Distribution of change risk scores")

init_db()

diff_engine = GitDiffAnalyzer
rag_engine = IncidentRAG()
mcp_runtime = MCPRuntime()
risk_engine = RiskEngine()

@app.post("/analyze-change", response_model=RiskAnalysisResponse)
def analyze_change(payload: ChangeAnalysisRequest):
    try:
        # Step 1: Parse Git Diff
        analyzer = GitDiffAnalyzer(payload.diff_text)
        diff_metrics = analyzer.parse()

        # Step 2: Fetch Controlled Telemetry via MCP Tools
        k8s_status = mcp_runtime.execute("get_k8s_status", service_name=payload.service_name)
        rollback_history = mcp_runtime.execute("get_previous_rollbacks", service_name=payload.service_name)
        mcp_telemetry = {"k8s": k8s_status, "rollbacks": rollback_history}

        # Step 3: Query Historical Incident Memory (RAG)
        rag_query = f"{payload.service_name} " + " ".join(diff_metrics["rule_flags"])
        rag_context = rag_engine.retrieve_similar_incidents(rag_query)

        # Step 4: AI Risk Assessment
        assessment = risk_engine.assess_risk(
            diff_summary=diff_metrics,
            rule_flags=diff_metrics["rule_flags"],
            tests_passed=payload.tests_passed,
            rag_context=rag_context,
            mcp_data=mcp_telemetry
        )

        score = assessment.get("risk_score", 0)
        reasons = assessment.get("reasons", [])

        # Categorize
        if score >= settings.HIGH_RISK_THRESHOLD:
            level = "HIGH"
            decision = "REQUIRE_MANUAL_APPROVAL"
        elif score >= settings.MEDIUM_RISK_THRESHOLD:
            level = "MEDIUM"
            decision = "REQUIRE_ADDITIONAL_TESTING"
        else:
            level = "LOW"
            decision = "ALLOW_AUTOMATIC_DEPLOYMENT"

        # Record to Database
        db = SessionLocal()
        log = DeploymentLog(
            repo_name=payload.repository,
            commit_sha=payload.commit_sha,
            branch=payload.branch,
            risk_score=score,
            risk_level=level,
            reasons=reasons
        )
        db.add(log)
        db.commit()
        db.close()

        # Metrics
        ANALYSIS_COUNTER.labels(status=level).inc()
        RISK_HISTOGRAM.observe(score)

        return RiskAnalysisResponse(
            risk_score=score,
            risk_level=level,
            decision=decision,
            reasons=reasons,
            mcp_telemetry=mcp_telemetry,
            historical_matches=rag_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)