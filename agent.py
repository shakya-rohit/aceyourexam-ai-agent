import json
import os
from openai import OpenAI
from tools import (
    get_student_results,
    get_attempt_details,
    get_upcoming_exams,
    search_questions,
    supported_exam_types
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
            "description": "Get upcoming exams for the logged-in user",
            "parameters": {
                "type": "object",
                "properties": {}
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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # -------------------------------
    # TOOL CALL HANDLING
    # -------------------------------
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # Execute tool
        if tool_name == "get_student_results":
            result = get_student_results(user_id, token)
        
        elif tool_name == "get_upcoming_exams":
            result = get_upcoming_exams(token)

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
            
        else:
            result = {"error": "Unknown tool"}

        # Append tool response
        messages.append(message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })

        # Final LLM response
        final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        return final.choices[0].message.content

    # -------------------------------
    # DIRECT RESPONSE
    # -------------------------------
    return message.content
