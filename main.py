from fastapi import FastAPI, Header
from pydantic import BaseModel
from agent import run_agent
from fastapi.middleware.cors import CORSMiddleware
import jwt

app = FastAPI(title="AceYourExam AI Agent 🚀")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_user_id(auth_header):
    if not auth_header:
        return None

    token = auth_header.split(" ")[1]

    decoded = jwt.decode(token, options={"verify_signature": False})

    return decoded.get("id")

class QueryRequest(BaseModel):
    question: str
    messages: list = []  # Optional: Previous conversation messagess
    userId: int = None  # Optional: To identify the student making the query


@app.get("/")
def home():
    return {"message": "AI Coach Agent running 🚀"}


@app.post("/ask")
def ask_agent(request: QueryRequest, authorization: str = Header(None)):
    logged_in_user_id = extract_user_id(authorization)
    # print(f"👤 Logged in user ID: {logged_in_user_id}")
    # print(f"📨 Received header: {authorization}")
    answer = run_agent(request.question, request.messages, request.userId, authorization)

    return {
        "question": request.question,
        "answer": answer
    }