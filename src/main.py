from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.infrastructure.database import init_db, get_db
from src.dependencies import verify_admin
from src.app.services import IngestionService
from src.infrastructure.ai_agent import FinancialAgent
from src.domain.schemas import QueryRequest, QueryResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Kudwa AI System", lifespan=lifespan)

@app.exception_handler(Exception)
async def global_handler(req: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Server Error", "detail": str(exc)})

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/ingest/{source}", dependencies=[Depends(verify_admin)])
async def ingest_route(source: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    service = IngestionService(db)
    count = await service.ingest(source, await file.read())
    return {"message": "Ingestion successful", "count": count}

@app.post("/api/v1/analyze", response_model=QueryResponse, dependencies=[Depends(verify_admin)])
async def analyze_route(req: QueryRequest, db: AsyncSession = Depends(get_db)):
    agent = FinancialAgent(db)
    # Convert Pydantic history to dict for internal usage
    hist_dicts = [{"role": m.role, "content": m.content} for m in req.history]
    return await agent.run(req.question, hist_dicts)