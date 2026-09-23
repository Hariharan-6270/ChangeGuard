from typing import List
from sqlalchemy import text
from app.models import SessionLocal
from openai import OpenAI
from app.config import settings

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

class IncidentRAG:
    def get_embedding(self, content: str) -> List[float]:
        try:
            res = openai_client.embeddings.create(
                input=[content],
                model="text-embedding-3-small"
            )
            return res.data[0].embedding
        except Exception:
            # Fallback zero-vector for local development without active API keys
            return [0.0] * 1536

    def retrieve_similar_incidents(self, query: str, limit: int = 3) -> List[str]:
        query_vector = self.get_embedding(query)
        db = SessionLocal()
        try:
            raw_sql = text("""
                SELECT incident_summary, root_cause
                FROM incident_knowledge
                ORDER BY embedding <-> CAST(:vec AS vector)
                LIMIT :lim
            """)
            result = db.execute(raw_sql, {"vec": str(query_vector), "lim": limit}).fetchall()
            return [f"Incident: {r[0]} | Root Cause: {r[1]}" for r in result]
        except Exception:
            return ["No previous incidents recorded for this domain."]
        finally:
            db.close()