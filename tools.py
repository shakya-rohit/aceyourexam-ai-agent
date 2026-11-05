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
    attempts = _get(f"/student/attempts/student/{student_id}", user_authorization)
    if not isinstance(attempts, list):
        return attempts

    normalized_attempts = []
    for attempt in attempts:
        if not isinstance(attempt, dict):
            continue
        normalized = dict(attempt)
        normalized["subjectScores"] = normalized.pop("subjects", {})
        normalized_attempts.append(normalized)

    # The backend repository does not promise an order. Sort before the model
    # compares attempts or interprets the first entry as the latest result.
    normalized_attempts.sort(
        key=lambda item: item.get("submittedAt") or "",
        reverse=True,
    )
    return {
        "attempts": normalized_attempts,
        "fieldDefinitions": {
            "correctCount": "Number of correct answers in the full exam.",
            "accuracy": "Percent of questions answered correctly.",
            "subjectScores": "Net marks earned by subject, including negative marking. These are not correct-answer counts and may be negative.",
        },
    }


def get_upcoming_exams(user_authorization: str):
    return _get("/exams", user_authorization)


def get_exam_details(exam_id: int, user_authorization: str):
    return _get(f"/exams/{exam_id}", user_authorization)


def get_exam_questions(exam_id: int, user_authorization: str):
    questions = _get(f"/student/exams/{exam_id}/questions", user_authorization)
    if isinstance(questions, list):
        return {
            "questions": questions,
            "answerKeyAvailable": False,
            "note": "This endpoint returns question text and options only; it does not provide a verified answer key.",
        }
    return questions


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
    questions = _get("/student/ai-tools/question-search", user_authorization, params)
    if isinstance(questions, list):
        return {
            "questions": questions,
            "answerKeyAvailable": False,
            "note": "This endpoint returns question text and options only; it does not provide a verified answer key or explanations.",
        }
    return questions


def supported_exam_types(user_authorization: str):
    return _get("/exam-types", user_authorization)


def get_subjects(user_authorization: str):
    return _get("/subjects", user_authorization, params={"includeTopics": "true"})


def get_today_study_plan(user_authorization: str):
    return _get("/student/study-plan/today", user_authorization)
