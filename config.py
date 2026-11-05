"""Central configuration for the AI agent service."""

import os
from pathlib import Path

from dotenv import load_dotenv


# Load the .env beside this file for local development. Values already supplied
# by the process environment (such as production settings) take precedence.
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8080/api")
AI_AGENT_INTERNAL_API_KEY = os.getenv("AI_AGENT_INTERNAL_API_KEY", "")

MAX_HISTORY_MESSAGES = 20
MAX_TOOL_ROUNDS = 5
MAX_TOOL_CALLS_PER_ROUND = 5
MAX_TOOL_CALLS_PER_REQUEST = 10
AGENT_TIME_BUDGET_SECONDS = 110
FINAL_RESPONSE_RESERVE_SECONDS = 15
MAX_MODEL_CALL_SECONDS = 20
REQUEST_TIMEOUT = (3, 20)
