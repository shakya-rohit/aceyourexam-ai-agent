import os

import requests


BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8080/api").rstrip("/")
REQUEST_TIMEOUT = (3, 20)


def _get(path: str, user_authorization: str, params=None):
    if not user_authorization or not user_authorization.startswith("Bearer "):
        return {"error": "The authenticated user context is unavailable."}

    try:
        response = requests.get(
            f"{BASE_URL}{path}",
            headers={"Authorization": user_authorization},
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {"error": "The requested AceYourExam data is temporarily unavailable."}


def get_student_results(student_id: int, user_authorization: str):
    return _get(f"/student/attempts/student/{student_id}", user_authorization)


def get_upcoming_exams(user_authorization: str):
    return _get("/exams", user_authorization)


def get_attempt_details(attempt_id: int, user_authorization: str):
    return _get(f"/student/attempts/{attempt_id}", user_authorization)


def search_questions(subject=None, topic=None, difficulty=None, user_authorization=None):
    params = {
        key: value
        for key, value in {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
        }.items()
        if value
    }
    return _get("/student/ai-tools/question-search", user_authorization, params)


def supported_exam_types(user_authorization: str):
    return _get("/exam-types", user_authorization)
