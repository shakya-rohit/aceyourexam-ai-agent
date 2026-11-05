import json
import time
from openai import APITimeoutError, OpenAI
from config import (
    AGENT_TIME_BUDGET_SECONDS,
    FINAL_RESPONSE_RESERVE_SECONDS,
    MAX_MODEL_CALL_SECONDS,
    MAX_TOOL_CALLS_PER_REQUEST,
    MAX_TOOL_CALLS_PER_ROUND,
    MAX_TOOL_ROUNDS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from tools import (
    get_student_results,
    get_attempt_details,
    get_upcoming_exams,
    get_exam_details,
    get_exam_questions,
    search_questions,
    supported_exam_types,
    get_subjects,
    get_today_study_plan
)

client = OpenAI(api_key=OPENAI_API_KEY, max_retries=0)


def _execute_tool(tool_call, user_id, token, request_timeout):
    tool_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be a JSON object")

    if tool_name == "get_student_results":
        return get_student_results(user_id, token, request_timeout)
    if tool_name == "get_upcoming_exams":
        return get_upcoming_exams(token, request_timeout)
    if tool_name == "get_exam_details":
        return get_exam_details(args["exam_id"], token, request_timeout)
    if tool_name == "get_exam_questions":
        return get_exam_questions(args["exam_id"], token, request_timeout)
    if tool_name == "get_attempt_details":
        return get_attempt_details(args["attempt_id"], token, request_timeout)
    if tool_name == "search_questions":
        return search_questions(
            args.get("subject"),
            args.get("topic"),
            args.get("difficulty"),
            token,
            request_timeout,
        )
    if tool_name == "supported_exam_types":
        return supported_exam_types(token, request_timeout)
    if tool_name == "get_subjects":
        return get_subjects(token, request_timeout)
    if tool_name == "get_today_study_plan":
        return get_today_study_plan(token, request_timeout)
    return {"error": "Unknown tool"}

# -------------------------------
# TOOL DEFINITIONS
# -------------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_student_results",
            "description": "Get exam results of the logged-in user",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_exams",
            "description": "List exams available to the logged-in user",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_exam_details",
            "description": "Get details for an exam the logged-in user can access",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "integer"}
                },
                "required": ["exam_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_exam_questions",
            "description": "Get questions for an exam the logged-in user is currently allowed to access; this returns no answer key",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "integer"}
                },
                "required": ["exam_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_attempt_details",
            "description": "Get detailed attempt analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "attempt_id": {"type": "integer"}
                },
                "required": ["attempt_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_questions",
            "description": "Search questions by subject/topic/difficulty",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "topic": {"type": "string"},
                    "difficulty": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "supported_exam_types",
            "description": "Use this when user asks about supported exams or exam types available on the platform",
            "parameters": {
                "type": "object",
                "properties": {
                    
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_subjects",
            "description": "List available subjects and their topics for study and practice",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_today_study_plan",
            "description": "Get the logged-in student's personalized study plan for today",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# -------------------------------
# SYSTEM PROMPT
# -------------------------------
SYSTEM_PROMPT = """
You are an AI Coach for AceYourExam.

You help students improve their performance.

Rules:
1. Use tools when data is needed.
2. Never guess student performance.
3. Give actionable insights.
4. Suggest practice strategies.
5. Be clear and helpful like a mentor.
6. When using personal results or study plan data, include a `### What your data shows` section with concrete supporting facts from tool results (such as subject, score, attempt date, or topic). Never invent missing values. If the data is unavailable or a tool returned an error, say so plainly.
7. Keep answers easy to scan: use short sections and concise bullets instead of long paragraphs. Separate observed data from your recommendation.
8. In get_student_results, subjectScores are net marks, not counts of correct answers. They may be negative due to negative marking. Use correctCount for the count of correct answers. Attempts are sorted newest first by submittedAt; only call an attempt "latest" when its date is available.
9. The question search and exam-question tools do not return verified answer keys or grading data. Never claim that an answer is correct, provide an answer key for retrieved questions, or offer to grade the student's answers. Explain that verified answer checking is unavailable if asked.
10. End every answer with a heading exactly `### Try next` followed by 1–3 short, relevant follow-up actions. Each item must be a direct, concise request that starts with an action (for example, `Find 5 Biology questions about Biomolecules`). Do not include labels such as `Request:`, quotation marks, code formatting, or assistant invitations such as `Let me know if you want...`. Do not promise capabilities the tools do not provide.
"""


# -------------------------------
# AGENT FUNCTION
# -------------------------------
def run_agent(user_query: str, req_messages=None, user_id=None, token=None):
    req_messages = req_messages or []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    for msg in req_messages:
        messages.append({
            "role": msg["role"],
            "content": msg["text"]
        })
    
    messages.append({"role": "user", "content": user_query})

    deadline = time.monotonic() + AGENT_TIME_BUDGET_SECONDS
    tool_deadline = deadline - FINAL_RESPONSE_RESERVE_SECONDS
    tool_calls_used = 0

    for _ in range(MAX_TOOL_ROUNDS):
        remaining = deadline - time.monotonic()
        model_timeout = min(MAX_MODEL_CALL_SECONDS, remaining - FINAL_RESPONSE_RESERVE_SECONDS)
        if model_timeout <= 0:
            break

        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                timeout=model_timeout,
            )
        except APITimeoutError:
            return "I couldn’t finish that request in time. Please try a narrower question."

        message = response.choices[0].message
        if not message.tool_calls:
            return message.content

        # Include the assistant's complete tool request, then return one result
        # for every call so the API can match each result by tool_call_id.
        messages.append(message)
        for call_index, tool_call in enumerate(message.tool_calls):
            remaining_tools = tool_deadline - time.monotonic()
            if call_index >= MAX_TOOL_CALLS_PER_ROUND:
                result = {"error": "This response requested more tools than can be run in one batch."}
            elif tool_calls_used >= MAX_TOOL_CALLS_PER_REQUEST:
                result = {"error": "The tool-call limit for this request was reached."}
            elif remaining_tools <= 0.2:
                result = {"error": "The request time budget for data lookups was reached."}
            else:
                # requests uses connect and read timeouts separately. Keep
                # their combined ceiling inside the remaining tool budget.
                connect_timeout = min(2.0, max(0.1, remaining_tools * 0.15))
                read_timeout = max(0.1, remaining_tools - connect_timeout - 0.1)
                try:
                    result = _execute_tool(
                        tool_call,
                        user_id,
                        token,
                        (connect_timeout, read_timeout),
                    )
                    tool_calls_used += 1
                except Exception:
                    # Keep this call's failure local so other calls in the batch
                    # can still run and the model can explain or recover.
                    result = {"error": "This tool could not be completed."}

            try:
                result_content = json.dumps(result)
            except (TypeError, ValueError):
                result_content = json.dumps({"error": "This tool returned an invalid result."})

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_content
            })

        if time.monotonic() >= tool_deadline:
            break

    # Use the reserved time for a final response. Do not run additional tools
    # after the request budget for lookups is exhausted.
    remaining = deadline - time.monotonic()
    if remaining <= 0.2:
        return "I couldn’t finish that request in time. Please try a narrower question."
    try:
        final = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            timeout=remaining,
        )
    except APITimeoutError:
        return "I couldn’t finish that request in time. Please try a narrower question."
    final_message = final.choices[0].message
    if final_message.tool_calls:
        return "I couldn’t complete this request because it needs more data lookups than I can perform in one response. Please narrow the request and try again."
    return final_message.content
