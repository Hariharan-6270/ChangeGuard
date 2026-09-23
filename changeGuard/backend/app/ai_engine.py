import json
from openai import OpenAI
from app.config import settings

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

class RiskEngine:
    def assess_risk(
        self,
        diff_summary: dict,
        rule_flags: list,
        tests_passed: bool,
        rag_context: list,
        mcp_data: dict
    ) -> dict:
        prompt = f"""
Analyze the deployment risk for this code change. Return JSON ONLY matching this format:
{{
  "risk_score": <int 0-100>,
  "reasons": ["<reason_1>", "<reason_2>"]
}}

Context:
- Modified Files: {diff_summary.get('files_changed')}
- Rule Triggers: {rule_flags}
- Automated Tests Passed: {tests_passed}
- Historical Incidents: {rag_context}
- Live Kubernetes/Rollback Telemetry: {mcp_data}
"""
        try:
            response = openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            # Rule-based fallback calculation
            score = 15
            reasons = []
            if not tests_passed:
                score += 50
                reasons.append("Unit/Integration tests failed.")
            if "CRITICAL_PAYMENT_LOGIC_MODIFIED" in rule_flags:
                score += 30
                reasons.append("Critical payment system code was modified.")
            if "DATABASE_MIGRATION_DETECTED" in rule_flags:
                score += 25
                reasons.append("Database schema migration included.")
            if "DESTRUCTIVE_SQL_KEYWORDS" in rule_flags:
                score += 40
                reasons.append("Destructive SQL commands (DROP/ALTER) detected.")

            return {
                "risk_score": min(score, 100),
                "reasons": reasons if reasons else ["Standard low-risk change"]
            }