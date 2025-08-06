
import os
from typing import Dict, Any

# טעינת משתני סביבה
from dotenv import load_dotenv

load_dotenv()


# ===========================
# הגדרות אבטחה
# ===========================
class SecurityConfig:
    """הגדרות אבטחה"""

    # JWT Token
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

    # הגדרות קוד משתמש
    USER_CODE_LENGTH = 8
    USER_CODE_INCLUDE_SPECIAL_CHARS = True
    USER_CODE_SPECIAL_CHARS = "!@#$%&*+-="
    USER_CODE_FORMAT = "mixed"

    # הגדרות סיסמאות
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL_CHAR = True
    PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"


# ===========================
# הגדרות כלליות
# ===========================
class Config:
    # HTTP Status Codes
    HTTP_200 = 200
    HTTP_400 = 400
    HTTP_401 = 401
    HTTP_403 = 403
    HTTP_404 = 404
    HTTP_500 = 500

    # Database
    DB_FIND_LIMIT = 100
    DELETE_COUNT_ZERO = 0
    PHOTOS_COUNT_ZERO = 0


# ===========================
# פונקציות
# ===========================
def get_user_code_config() -> Dict[str, Any]:
    return {
        "length": SecurityConfig.USER_CODE_LENGTH,
        "include_special": SecurityConfig.USER_CODE_INCLUDE_SPECIAL_CHARS,
        "special_chars": SecurityConfig.USER_CODE_SPECIAL_CHARS,
        "format": SecurityConfig.USER_CODE_FORMAT
    }

#בדיקת תקינות סיסמא
def validate_password(password: str) -> Dict[str, Any]:
    errors = []

    # בדיקת אורך
    if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
        errors.append(f"הסיסמה חייבת להכיל לפחות {SecurityConfig.MIN_PASSWORD_LENGTH} תווים")

    # בדיקת אות גדולה
    if SecurityConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("הסיסמה חייבת להכיל לפחות אות גדולה אחת (A-Z)")

    # בדיקת אות קטנה
    if SecurityConfig.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("הסיסמה חייבת להכיל לפחות אות קטנה אחת (a-z)")

    # בדיקת מספר
    if SecurityConfig.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        errors.append("הסיסמה חייבת להכיל לפחות מספר אחד (0-9)")

    # בדיקת תו מיוחד
    if SecurityConfig.REQUIRE_SPECIAL_CHAR:
        has_special = any(c in SecurityConfig.PASSWORD_SPECIAL_CHARS for c in password)
        if not has_special:
            errors.append("הסיסמה חייבת להכיל לפחות תו מיוחד אחד")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "strength": "חזקה" if len(errors) == 0 else "חלשה"
    }


# ===========================
# יצירת אובייקטים
# ===========================
config = Config()
security_config = SecurityConfig()

# ===========================
# הגדרות זיהוי פנים והעלאות
# ===========================
class FaceRecognitionConfig:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
    DUMMY_VECTOR_VALUE = 0.1
    VECTOR_PREVIEW_LENGTH = 5
    SIMILARITY_THRESHOLD = 0.93

    MAX_KNN_CACHED_EVENTS = 10
    HIGH_CONFIDENCE_THRESHOLD = 0.95

    DEFAULT_VECTOR_LENGTH = 128  # אורך צפוי לוקטור תווי פנים
    DEFAULT_SIMILARITY_THRESHOLD = 0.92  # סף התאמה בסיסי בין וקטורים
    HIGH_CONFIDENCE_THRESHOLD = 0.95  # מעל סף זה נחשב התאמה "גבוהה"
    VERY_HIGH_SIMILARITY = 0.9  # ערך נוסף להשוואות כלליות
    LOWER_CONFIDENCE_THRESHOLD = 0.85  # סף מינימלי להשוואות כלליות


class FaceAlignmentConfig:
    RIGHT_EYE_START = 36
    RIGHT_EYE_END = 42
    LEFT_EYE_START = 42
    LEFT_EYE_END = 48

    MIN_EYE_DISTANCE = 15
    MIN_ANGLE_TO_ALIGN = 3


# ===========================
# ייצוא
# ===========================
__all__ = ["Config", "SecurityConfig", "config", "security_config", "get_user_code_config", "validate_password","FaceRecognitionConfig",FaceAlignmentConfig]