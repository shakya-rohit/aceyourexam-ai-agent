from contextlib import asynccontextmanager
import hmac
import logging
import os
import time
import uuid
from typing import List, Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from agent import run_agent

# Uvicorn configures this logger and reliably displays application INFO logs.
logger = logging.getLogger("uvicorn.error")
MAX_HISTORY_MESSAGES = 20


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if os.getenv("AI_AGENT_INTERNAL_API_KEY", "").strip():
        logger.info("AI_AGENT_INTERNAL_API_KEY is configured")
    else:
        logger.error("AI_AGENT_INTERNAL_API_KEY is not configured; /ask requests will be unavailable")
    yield


app = FastAPI(title="AceYourExam AI Agent 🚀", lifespan=lifespan)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=4000)

class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    messages: List[ChatMessage] = Field(default_factory=list, max_length=MAX_HISTORY_MESSAGES)
    userId: int = Field(gt=0)


@app.get("/")
def home():
    return {"message": "AI Coach Agent running 🚀"}


@app.post("/ask")
def ask_agent(
    request: QueryRequest,
    agent_key: Optional[str] = Header(None, alias="X-AI-Agent-Key"),
    user_authorization: Optional[str] = Header(None, alias="X-User-Authorization"),
):
    request_id = uuid.uuid4().hex[:12]
    expected_key = os.getenv("AI_AGENT_INTERNAL_API_KEY", "")
    if not expected_key:
        logger.error("AI request %s rejected: AI_AGENT_INTERNAL_API_KEY is not configured", request_id)
        raise HTTPException(status_code=503, detail="AI agent service authentication is not configured")
    if not agent_key or not hmac.compare_digest(agent_key, expected_key):
        logger.warning("AI request %s rejected: invalid internal service key", request_id)
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not user_authorization or not user_authorization.startswith("Bearer "):
        logger.warning("AI request %s rejected: missing forwarded user bearer token", request_id)
        raise HTTPException(status_code=401, detail="Authenticated user context is required")

    started_at = time.monotonic()
    logger.info("AI request %s started (history_messages=%d)", request_id, len(request.messages))
    messages = [message.dict() for message in request.messages]
    try:
        answer = run_agent(request.question, messages, request.userId, user_authorization)
    except Exception:
        logger.exception("AI request %s failed while running the agent", request_id)
        raise HTTPException(status_code=502, detail="The AI assistant is temporarily unavailable") from None

    logger.info("AI request %s completed in %.2fs", request_id, time.monotonic() - started_at)

    return {
        "question": request.question,
        "answer": answer
    }
