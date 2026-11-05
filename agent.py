import json
import os
from openai import OpenAI
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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MAX_TOOL_ROUNDS = 5

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

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        if not message.tool_calls:
            return message.content

        # Include the assistant's complete tool request, then return one result
        # for every call so the API can match each result by tool_call_id.
        messages.append(message)
        for tool_call in message.tool_calls:
            try:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                if not isinstance(args, dict):
                    raise ValueError("Tool arguments must be a JSON object")

                if tool_name == "get_student_results":
                    result = get_student_results(user_id, token)
                elif tool_name == "get_upcoming_exams":
                    result = get_upcoming_exams(token)
                elif tool_name == "get_exam_details":
                    result = get_exam_details(args["exam_id"], token)
                elif tool_name == "get_exam_questions":
                    result = get_exam_questions(args["exam_id"], token)
                elif tool_name == "get_attempt_details":
                    result = get_attempt_details(args["attempt_id"], token)
                elif tool_name == "search_questions":
                    result = search_questions(
                        args.get("subject"),
                        args.get("topic"),
                        args.get("difficulty"),
                        token
                    )
                elif tool_name == "supported_exam_types":
                    result = supported_exam_types(token)
                elif tool_name == "get_subjects":
                    result = get_subjects(token)
                elif tool_name == "get_today_study_plan":
                    result = get_today_study_plan(token)
                else:
                    result = {"error": "Unknown tool"}
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

    # Allow one final answer from the completed tool results, but do not run a
    # sixth tool round. If the model still needs another tool, report the limit
    # rather than returning an answer that may be missing required data.
    final = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    final_message = final.choices[0].message
    if final_message.tool_calls:
        return "I couldn’t complete this request because it needs more data lookups than I can perform in one response. Please narrow the request and try again."
    return final_message.content
