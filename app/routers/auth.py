# # app/routers/auth.py
# from fastapi import APIRouter, HTTPException, Depends
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# import hashlib
# import jwt
# from datetime import datetime, timedelta, timezone
# from typing import Optional
#
# from app.models.schemas import (
#     UserCreate, UserLogin, UserResponse, LoginResponse
# )
# from app.database import database
# from app.config import SecurityConfig, validate_password  # 🔧 תיקון הייבוא
#
# router = APIRouter(prefix="/auth", tags=["authentication"])
# security = HTTPBearer()
#
# # הגדרות מהקובץ config
# SECRET_KEY = SecurityConfig.SECRET_KEY
# ALGORITHM = SecurityConfig.ALGORITHM
# ACCESS_TOKEN_EXPIRE_MINUTES = SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES
#
#
# # הצפנת סיסמא
# def hash_password(password: str) -> str:
#     return hashlib.sha256(password.encode()).hexdigest()
#
#
# def verify_password(password: str, hashed_password: str) -> bool:
#     return hash_password(password) == hashed_password
#
#
# # יצירת טוקן
# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.now(timezone.utc) + expires_delta
#     else:
#         expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt
#
#
# # זיהוי המשתמש
# async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
#     token = credentials.credentials
#
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub")
#         if user_id is None:
#             raise HTTPException(status_code=401, detail="Invalid authentication credentials")
#         return user_id
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except jwt.PyJWTError:
#         raise HTTPException(status_code=401, detail="Could not validate credentials")
#
#
# @router.post("/register", response_model=UserResponse)
# async def register(user_data: UserCreate):
#     try:
#         # בדיקת תקינות הסיסמה
#         password_check = validate_password(user_data.password)
#         if not password_check["is_valid"]:
#             raise HTTPException(
#                 status_code=400,
#                 detail={
#                     "message": "הסיסמה לא עומדת בדרישות הבטיחות",
#                     "errors": password_check["errors"],
#                     "requirements": {
#                         "min_length": SecurityConfig.MIN_PASSWORD_LENGTH,
#                         "require_uppercase": SecurityConfig.REQUIRE_UPPERCASE,
#                         "require_lowercase": SecurityConfig.REQUIRE_LOWERCASE,
#                         "require_digit": SecurityConfig.REQUIRE_DIGIT,
#                         "require_special": SecurityConfig.REQUIRE_SPECIAL_CHAR
#                     }
#                 }
#             )
#
#         # בדיקה אם המשתמש כבר קיים
#         existing_user = await database.find_user_by_email(user_data.email)
#         if existing_user:
#             raise HTTPException(
#                 status_code=400,
#                 detail="User with this email already exists"
#             )
#
#         # הצפנת סיסמה
#         password_hash = hash_password(user_data.password)
#
#         # יצירת משתמש
#         user_id = await database.add_user(
#             name=user_data.name,
#             email=user_data.email,
#             password_hash=password_hash
#         )
#
#         # קבלת פרטי המשתמש החדש
#         new_user = await database.find_user_by_id(user_id)
#
#         return UserResponse(
#             user_id=user_id,
#             name=new_user["name"],
#             email=new_user["email"],
#             created_at=new_user["created_at"]
#         )
#
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except HTTPException:
#         raise  # העבר את ה-HTTPException כמו שהוא
#     except Exception as e:
#         print(f"❌ Error in register: {e}")  # הדפסה לדיבוג
#         raise HTTPException(status_code=500, detail="Internal server error")
#
#
# @router.post("/login", response_model=LoginResponse)
# async def login(credentials: UserLogin):
#     try:
#         # חיפוש משתמש
#         user = await database.find_user_by_email(credentials.email)
#
#         if not user:
#             raise HTTPException(
#                 status_code=400,
#                 detail="User not found"
#             )
#
#         # בדיקת סיסמה
#         if not verify_password(credentials.password, user["password_hash"]):
#             raise HTTPException(
#                 status_code=401,
#                 detail="Incorrect password"
#             )
#
#         # יצירת טוקן
#         access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#         access_token = create_access_token(
#             data={"sub": user["user_id"]},
#             expires_delta=access_token_expires
#         )
#
#         return LoginResponse(
#             user_id=user["user_id"],
#             name=user["name"],
#             access_token=access_token,
#             token_type="bearer",
#             message="התחברות בוצעה בהצלחה"
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"❌ Error in login: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#
#
# @router.get("/me", response_model=UserResponse)
# async def get_current_user_info(current_user_id: str = Depends(get_current_user)):
#     user = await database.find_user_by_id(current_user_id)
#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="User not found"
#         )
#
#     return UserResponse(
#         user_id=user["user_id"],
#         name=user["name"],
#         email=user["email"],
#         created_at=user["created_at"]
#     )
#
#
# @router.post("/logout")
# async def logout(current_user_id: str = Depends(get_current_user)):
#     return {"message": "Successfully logged out"}
#
#
# @router.post("/refresh", response_model=LoginResponse)
# async def refresh_token(current_user_id: str = Depends(get_current_user)):
#     user = await database.find_user_by_id(current_user_id)
#
#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="User not found"
#         )
#
#     # יצירת טוקן חדש
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user["user_id"]},
#         expires_delta=access_token_expires
#     )
#
#     return LoginResponse(
#         user_id=user["user_id"],
#         name=user["name"],
#         access_token=access_token,
#         token_type="bearer",
#         message="Token refreshed successfully"
#     )
#
#
# # Alias for backward compatibility
# verify_token = get_current_user
#
# # Export for use in other routers
# __all__ = ["router", "get_current_user", "verify_token"]


# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.schemas import (
    UserCreate, UserLogin, UserResponse, LoginResponse
)
from app.database import database
from app.config import SecurityConfig, validate_password  # 🔧 תיקון הייבוא

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# הגדרות מהקובץ config
SECRET_KEY = SecurityConfig.SECRET_KEY
ALGORITHM = SecurityConfig.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES


# הצפנת סיסמא
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password


# יצירת טוקן
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# זיהוי המשתמש
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


#  פונקציה חדשה לבדיקת הרשאות מנהל אירוע על בסיס קוד אירוע
async def verify_event_manager_by_code(event_code: str, current_user: str) -> bool:
    """בדיקה אם המשתמש הנוכחי הוא מנהל האירוע על בסיס קוד אירוע"""
    try:
        event = await database.events.find_one({"event_code": event_code})

        if not event:
            return False

        return event["created_by"] == current_user
    except Exception:
        return False


#  פונקציה חדשה לבדיקת הרשאות מנהל אירוע על בסיס event_id
async def verify_event_manager_by_id(event_id: str, current_user: str) -> bool:
    """בדיקה אם המשתמש הנוכחי הוא מנהל האירוע על בסיס event_id"""
    try:
        event = await database.get_event_by_id(event_id)

        if not event:
            return False

        return event["created_by"] == current_user
    except Exception:
        return False


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    try:
        # בדיקת תקינות הסיסמה
        password_check = validate_password(user_data.password)
        if not password_check["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "הסיסמה לא עומדת בדרישות הבטיחות",
                    "errors": password_check["errors"],
                    "requirements": {
                        "min_length": SecurityConfig.MIN_PASSWORD_LENGTH,
                        "require_uppercase": SecurityConfig.REQUIRE_UPPERCASE,
                        "require_lowercase": SecurityConfig.REQUIRE_LOWERCASE,
                        "require_digit": SecurityConfig.REQUIRE_DIGIT,
                        "require_special": SecurityConfig.REQUIRE_SPECIAL_CHAR
                    }
                }
            )

        # בדיקה אם המשתמש כבר קיים
        existing_user = await database.find_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )

        # הצפנת סיסמה
        password_hash = hash_password(user_data.password)

        # יצירת משתמש
        user_id = await database.add_user(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash
        )

        # קבלת פרטי המשתמש החדש
        new_user = await database.find_user_by_id(user_id)

        return UserResponse(
            user_id=user_id,
            name=new_user["name"],
            email=new_user["email"],
            created_at=new_user["created_at"]
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # העבר את ה-HTTPException כמו שהוא
    except Exception as e:
        print(f" Error in register: {e}")  # הדפסה לדיבוג
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    try:
        # חיפוש משתמש
        user = await database.find_user_by_email(credentials.email)

        if not user:
            raise HTTPException(
                status_code=400,
                detail="User not found"
            )

        # בדיקת סיסמה
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Incorrect password"
            )

        # יצירת טוקן
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["user_id"]},
            expires_delta=access_token_expires
        )

        return LoginResponse(
            user_id=user["user_id"],
            name=user["name"],
            access_token=access_token,
            token_type="bearer",
            message="התחברות בוצעה בהצלחה"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f" Error in login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user_id: str = Depends(get_current_user)):
    user = await database.find_user_by_id(current_user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return UserResponse(
        user_id=user["user_id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"]
    )


@router.post("/logout")
async def logout(current_user_id: str = Depends(get_current_user)):
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(current_user_id: str = Depends(get_current_user)):
    user = await database.find_user_by_id(current_user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # יצירת טוקן חדש
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["user_id"]},
        expires_delta=access_token_expires
    )

    return LoginResponse(
        user_id=user["user_id"],
        name=user["name"],
        access_token=access_token,
        token_type="bearer",
        message="Token refreshed successfully"
    )


# Alias for backward compatibility
verify_token = get_current_user

# Export for use in other routers
__all__ = ["router", "get_current_user", "verify_token", "verify_event_manager_by_code", "verify_event_manager_by_id"]