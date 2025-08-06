# app/models/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from datetime import datetime

# -------------------------
# User Schemas - סכמות משתמשים
# -------------------------

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    user_id: str
    created_at: datetime

class LoginResponse(BaseModel):
    user_id: str
    name: str
    access_token: str
    token_type: str = "bearer"
    message: str = "התחברות בוצעה בהצלחה"

# -------------------------
# Event Schemas - סכמות אירועים
# -------------------------

class EventCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=40)
    event_code: str = Field(..., min_length=4, max_length=20)

class EventResponse(BaseModel):
    event_id: str
    name: str
    event_code: str
    created_by: str
    created_at: datetime

class EventJoin(BaseModel):
    event_code: str
    as_manager: Optional[bool] = False

class EventStats(BaseModel):
    event_id: str
    participants: int
    total_photos: int
    processed_photos: int
    total_detections: int
    processing_rate: float

# -------------------------
# Photo Schemas - סכמות תמונות
# -------------------------

class PhotoUploadResponse(BaseModel):
    photo_id: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_at: datetime

class UserPhotoResponse(PhotoUploadResponse):
    user_id: str
    is_primary: bool
    face_encoding_size: int

class EventPhotoResponse(PhotoUploadResponse):
    event_id: str
    uploaded_by: str
    processed: bool

# -------------------------
# Face Detection Schemas - סכמות זיהוי פנים
# -------------------------

class FaceCoordinates(BaseModel):
    x: int
    y: int
    width: int
    height: int

class FaceDetectionCreate(BaseModel):
    event_photo_id: str
    detected_user_id: str
    confidence_score: float = Field(..., ge=0, le=100)
    face_coordinates: FaceCoordinates

class FaceDetectionResponse(BaseModel):
    detection_id: str
    event_photo_id: str
    detected_user_id: str
    confidence_score: float
    face_coordinates: Dict[str, int]
    detected_at: datetime
    matched_at: datetime
    photo_details: Optional[Dict] = None

class UserDetectionsResponse(BaseModel):
    user_id: str
    event_id: str
    detections: List[FaceDetectionResponse]
    total_detections: int

# -------------------------
# Processing Schemas - סכמות עיבוד
# -------------------------

class ProcessPhotoRequest(BaseModel):
    photo_id: str
    extract_faces: bool = True
    save_detections: bool = True

class ProcessPhotoResponse(BaseModel):
    photo_id: str
    faces_found: int
    detections_saved: int
    processing_time: float
    status: str

class BatchProcessResponse(BaseModel):
    event_id: str
    total_photos: int
    processed_photos: int
    failed_photos: int
    total_faces_detected: int
    processing_time: float

# -------------------------
# General Schemas - סכמות כלליות
# -------------------------

class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    status_code: int

class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    timestamp: datetime
    version: str = "1.0.0"

# -------------------------
# Search & Filter Schemas - סכמות חיפוש וסינון
# -------------------------

class PhotoSearchParams(BaseModel):
    event_id: Optional[str] = None
    user_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    processed_only: bool = False
    limit: int = Field(default=50, le=200)
    offset: int = Field(default=0, ge=0)

class DetectionSearchParams(BaseModel):
    event_id: Optional[str] = None
    user_id: Optional[str] = None
    confidence_min: float = Field(default=80.0, ge=0, le=100)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=50, le=200)

# -------------------------
# Configuration Schemas - סכמות הגדרות
# -------------------------

class UserPreferences(BaseModel):
    auto_tag_enabled: bool = True
    min_confidence_score: float = Field(default=85.0, ge=50, le=100)
    email_notifications: bool = True
    privacy_mode: bool = False

class ProcessingConfig(BaseModel):
    max_faces_per_photo: int = Field(default=50, ge=1, le=100)
    min_face_size: int = Field(default=40, ge=20)
    detection_threshold: float = Field(default=0.5, ge=0.1, le=1.0)
    use_gpu: bool = False



