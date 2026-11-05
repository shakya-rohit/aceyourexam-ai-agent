import requests

from config import BACKEND_API_BASE_URL, REQUEST_TIMEOUT


def _get(path: str, user_authorization: str, params=None, request_timeout=REQUEST_TIMEOUT):
    if not user_authorization or not user_authorization.startswith("Bearer "):
        return {"error": "The authenticated user context is unavailable."}

    try:
        response = requests.get(
            f"{BACKEND_API_BASE_URL}{path}",
            headers={"Authorization": user_authorization},
            params=params,
            timeout=request_timeout,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {"error": "The requested AceYourExam data is temporarily unavailable."}


def get_student_results(student_id: int, user_authorization: str, request_timeout=REQUEST_TIMEOUT):
    attempts = _get(
        f"/student/attempts/student/{student_id}",
        user_authorization,
        request_timeout=request_timeout,
    )
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


def get_upcoming_exams(user_authorization: str, request_timeout=REQUEST_TIMEOUT):
    return _get("/exams", user_authorization, request_timeout=request_timeout)


def get_exam_details(exam_id: int, user_authorization: str, request_timeout=REQUEST_TIMEOUT):
    return _get(f"/exams/{exam_id}", user_authorization, request_timeout=request_timeout)


def get_exam_questions(exam_id: int, user_authorization: str, request_timeout=REQUEST_TIMEOUT):
    questions = _get(
        f"/student/exams/{exam_id}/questions",
        user_authorization,
        request_timeout=request_timeout,
    )
    if isinstance(questions, list):
        return {
            "questions": questions,
            "answerKeyAvailable": False,
            "note": "This endpoint returns question text and options only; it does not provide a verified answer key.",
        }
    return questions


def get_attempt_details(attempt_id: int, user_authorization: str, request_timeout=REQUEST_TIMEOUT):
    return _get(
        f"/student/attempts/{attempt_id}",
        user_authorization,
        request_timeout=request_timeout,
    )


def search_questions(subject=None, topic=None, difficulty=None, user_authorization=None,
                    request_timeout=REQUEST_TIMEOUT):
    params = {
        key: value
        for key, value in {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
        }.items()
        if value
    }
    questions = _get(
        "/student/ai-tools/question-search",
        user_authorization,
        params,
        request_timeout=request_timeout,
    )
    if isinstance(questions, list):
        return {
            "questions": questions,
            "answerKeyAvailable": False,
            "note": "This endpoint returns question text and options only; it does not provide a verified answer key or explanations.",
        }
    return questions


def supported_exam_types(user_authorization: str, request_timeout=REQUEST_TIMEOUT):
    return _get("/exam-types", user_authorization, request_timeout=request_timeout)


def get_subjects(user_authorization: str, request_timeout=REQUEST_TIMEOUT):
    return _get(
        "/subjects",
        user_authorization,
        params={"includeTopics": "true"},
        request_timeout=request_timeout,
    )


def get_today_study_plan(user_authorization: str, request_timeout=REQUEST_TIMEOUT):
    return _get(
        "/student/study-plan/today",
        user_authorization,
        request_timeout=request_timeout,
    )
