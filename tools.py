import requests
import time

BASE_URL = "http://localhost:8080/api"

class AuthManager:
    def __init__(self):
        self.token = None
        self.expiry_time = 0  # epoch times

    def get_token(self):
        current_time = time.time()

        # 🔥 If token missing OR expired → refresh
        if self.token is None or current_time >= self.expiry_time:
            print("🔄 Token expired or missing. Fetching new token...")

            self.token = get_auth_token("admin@gmail.com", "password")

            # 👉 set expiry to 30 mins from now
            self.expiry_time = current_time + (30 * 60)

            print("✅ New token stored. Expires at:", self.expiry_time)

        return self.token

auth_manager = AuthManager()

def get_student_results(student_id: int):
    print("📡 API CALL → get_student_results")

    try:
        token = auth_manager.get_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }

        res = requests.get(f"{BASE_URL}/student/attempts/student/{student_id}", headers=headers)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def get_upcoming_exams():
    print("📡 API CALL → get_upcoming_exams")

    try:
        token = auth_manager.get_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }

        res = requests.get(f"{BASE_URL}/exams", headers=headers)
        return res.json()
    except Exception as e:
        return {"error": str(e)}


def get_attempt_details(attempt_id: int):
    print("📡 API CALL → get_attempt_details")

    try:
        token = auth_manager.get_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }
        res = requests.get(f"{BASE_URL}/student/attempts/{attempt_id}", headers=headers)
        return res.json()
    except Exception as e:
        return {"error": str(e)}


def search_questions(subject=None, topic=None, difficulty=None):
    print("📡 API CALL → search_questions")

    try:
        token = auth_manager.get_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }

        params = {}

        if subject:
            params["subject"] = subject
        if topic:
            params["topic"] = topic
        if difficulty:
            params["difficulty"] = difficulty

        res = requests.get(f"{BASE_URL}/question-bank/search", params=params, headers=headers)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def supported_exam_types():
    print("📡 API CALL → supported_exam_types")

    try:
        token = auth_manager.get_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }
        res = requests.get(f"{BASE_URL}/exam-types", headers=headers)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def get_auth_token(email: str, password: str):
    print("🔐 Logging in to get JWT token...")

    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": email,
                "password": password
            }
        )

        data = response.json()

        # 🔥 adjust key based on your backend response
        token = data.get("token")

        if not token:
            print("❌ Token not found in response:", data)
            return None

        print("✅ Token received")
        return token

    except Exception as e:
        print("❌ Login failed:", str(e))
        return None

