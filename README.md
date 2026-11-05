# 🤖 AI Coach (LLM Agent) – AceYourExam

AceYourExam now includes an **AI-powered coaching assistant** that acts as a **personal mentor for students**.

This feature leverages **LLM + Tool Calling + Backend APIs** to provide:

- Personalized insights
- Real-time performance analysis
- Smart study recommendations
- Context-aware conversations

---

## 🚀 Key Capabilities

### 🧠 1. Conversational AI Coach

Students can ask natural questions like:

- “Analyze my past performance”
- “What are my weak subjects?”
- “Give me a study plan”
- “Suggest questions to practice”

The AI responds like a **real mentor**, not just raw data.

---

### 🔧 2. Tool Calling (Function-Based AI)

The agent intelligently calls backend APIs:

| Tool                   | Purpose                      |
| ---------------------- | ---------------------------- |
| `get_student_results`  | Fetch past exam results      |
| `get_upcoming_exams`   | List exams available to the student |
| `get_exam_details`     | Fetch details for an accessible exam |
| `get_exam_questions`   | Fetch questions for an exam currently available to the student |
| `get_attempt_details`  | Deep analysis of attempts    |
| `search_questions`     | Recommend practice questions |
| `supported_exam_types` | Show supported exams         |
| `get_subjects`         | List available subjects and topics |
| `get_today_study_plan` | Fetch the personalized plan for today |

👉 No hardcoding — AI decides dynamically.

---

### 🔐 3. Secure Personalization (JWT Based)

- Angular sends its JWT only to Spring Boot.
- Spring Boot validates the token and derives the user ID from the authenticated principal.
- Spring Boot calls FastAPI using a server-to-server key and forwards the user's JWT for user-scoped backend tool requests.
- Supports queries like:

✅ “Show my results”  
❌ No need to expose userId manually

---

### 🧩 4. Context-Aware Conversations

The system maintains **chat history (last few messages)**:

- Follow-up questions supported
- Multi-step conversations enabled

Example:

User: “Analyze my performance”  
User: “Focus only on Physics”  
→ AI understands context

---

### ⚡ 5. Smart Suggestions (Dynamic UI)

After every response, AI generates contextual suggestions:

- “Analyze weak areas”
- “Give me a study plan”
- “Focus on Physics”
- “Start beginner level”

This creates a **guided learning experience**.

---

### 🖥️ 6. Full Chat UI (Angular)

- ChatGPT-like interface
- User / AI message bubbles
- Sticky input box
- Real-time suggestions
- Auto-scroll behavior

---

## 📸 AI Assistant

| AI Chat Interface                |
| -------------------------------- |
| ![Exam](screenshots/ai-chat.png) |

---

## 🏗️ AI Architecture

Angular UI → Spring Boot → FastAPI AI agent → OpenAI
                                     ↓
                              Spring Boot APIs → PostgreSQL

The browser calls Spring Boot at `/api/ai/ask`; it does not call the AI agent directly or send a `userId`.
Spring Boot derives the user ID from the authenticated principal and calls the agent with
`AI_AGENT_INTERNAL_API_KEY`. The agent uses the forwarded user JWT only when it calls user-scoped
Spring Boot APIs. Set `AI_AGENT_BASE_URL` and the same `AI_AGENT_INTERNAL_API_KEY` in the backend
and agent environments. Set `BACKEND_API_BASE_URL` in the agent environment to the backend's
internal `/api` base URL. Do not expose the internal key to the frontend.

---

## 🔁 Request Flow

User Query  
↓  
AI Agent (LLM decides tool)  
↓  
Backend API call  
↓  
Tool response  
↓  
LLM generates final answer  
↓  
UI renders response + suggestions

---

## 🧠 Why This is Powerful

- Not just a chatbot → **Decision-making AI**
- Real backend integration → **No hallucination**
- Personalized coaching → **User-specific insights**
- Extensible → Add more tools anytime

---
