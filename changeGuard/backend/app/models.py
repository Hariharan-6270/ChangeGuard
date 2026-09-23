from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
from app.config import settings

Base = declarative_base()

class DeploymentLog(Base):
    __tablename__ = "deployment_logs"

    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String, index=True)
    commit_sha = Column(String, index=True)
    branch = Column(String)
    risk_score = Column(Integer)
    risk_level = Column(String)
    reasons = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class IncidentKnowledge(Base):
    __tablename__ = "incident_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)
    incident_summary = Column(String)
    root_cause = Column(String)
    embedding = Column(Vector(1536))

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    with engine.connect() as conn:
        conn.execute(Base.metadata.bind.text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class ChangeAnalysisRequest(BaseModel):
    repository: str
    commit_sha: str
    branch: str
    diff_text: str
    tests_passed: bool
    service_name: str

class RiskAnalysisResponse(BaseModel):
    risk_score: int
    risk_level: str
    decision: str
    reasons: List[str]
    mcp_telemetry: dict
    historical_matches: List[str]