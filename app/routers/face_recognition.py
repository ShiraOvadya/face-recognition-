from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
import cv2
import numpy as np
import os
from typing import List
from datetime import datetime
from app.routers.auth import get_current_user, verify_event_manager_by_id
from app.database import database
from app.config import FaceRecognitionConfig
from app.services.face_features_extractor import face_extractor
from app.services.image_storage import ImageStorageService

router = APIRouter(prefix="/face-recognition", tags=["face-recognition"])
image_storage = ImageStorageService(database)

# # קבועים
# ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
# MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image_file(file: UploadFile) -> bool:
    if not file.content_type or not file.content_type.startswith('image/'):
        return False
    file_ext = os.path.splitext(file.filename.lower())[1] if file.filename else ''
    # if file_ext not in ALLOWED_EXTENSIONS:
    if file_ext not in FaceRecognitionConfig.ALLOWED_EXTENSIONS:
        return False
    return True
@router.post("/upload-reference-photo")
async def upload_reference_photo(
        file: UploadFile = File(...),
        current_user: str = Depends(get_current_user)
):
    print(f"Processing reference photo for user: {current_user}")

    try:
        if not validate_image_file(file):
            raise HTTPException(status_code=400, detail="File must be a valid image (JPG, PNG, WEBP, HEIC)")

        # קריאת התמונה
        contents = await file.read()
        # if len(contents) > MAX_FILE_SIZE:
        if len(contents) > FaceRecognitionConfig.MAX_FILE_SIZE:
            raise HTTPException(status_code=400,
                                detail=f"File too large. Maximum size is {FaceRecognitionConfig.MAX_FILE_SIZE // (1024 * 1024)}MB")
        print(f" File size: {len(contents)} bytes")
        user = await database.find_user_by_id(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_email = user.get("email", "unknown")
        user_name = user.get("name", "Unknown User")
        print(f" User: {user_name} ({user_email})")

        # המרת התמונה ל-OpenCV format
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)#קורא מידע מתוך הקובץ ויוצר מטריצת פקסלים
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file - cannot decode")
        print(f" Image loaded: {image.shape}")
        # חילוץ וקטור פנים באמצעות השירות הקיים שלך
        try:
            # שימוש ב-face_extractor הקיים שלך
            #חוזר לפה רשימה של וקטורים שכל אחד מהם מייצג פנים שזהו בתמונה
            face_vectors = face_extractor.extract_multiple_faces(image)

            if not face_vectors:
                raise HTTPException(
                    status_code=400,
                    detail="לא זוהו פנים בתמונה. אנא העלה תמונה ברורה עם פנים במרכז התמונה"
                )

            if len(face_vectors) > 1:
                print(f" Multiple faces detected ({len(face_vectors)}), using the largest/clearest one")

            # שימוש בוקטור הראשון (הטוב ביותר)
            face_vector = face_vectors[0]
            print(f"Face vector extracted using your service: size {len(face_vector)}")

            # המרה ל-numpy array אם צריך
            if isinstance(face_vector, list):
                face_vector_np = np.array(face_vector)
            else:
                face_vector_np = face_vector

            print(f"Vector type: {type(face_vector_np)}, shape: {face_vector_np.shape}")

        except Exception as face_error:
            print(f" Face extraction failed: {face_error}")
            raise HTTPException(status_code=400, detail=f"Face extraction failed: {str(face_error)}")

        # שמירת התמונה באמצעות השירות הקיים שלך
        print("Saving reference photo using your existing image storage service...")
        try:
            success = await image_storage.save_user_reference_image(
                user_id=current_user,
                user_email=user_email,
                image_data=contents,
                filename=file.filename,
                feature_vector=face_vector_np  # השימוש בוקטור האמיתי
            )

            if not success:
                raise HTTPException(status_code=500, detail="Failed to save reference photo")

            print(f"Photo saved using your ImageStorageService")

        except Exception as storage_error:
            print(f"Storage service failed: {storage_error}")
            # fallback - שמירה ישירה במסד נתונים
            print("Trying direct database save as fallback...")

            # מחיקת תמונות ייחוס קודמות
            await database.user_photos.delete_many({
                "user_id": current_user,
                "is_reference": True
            })

            # שמירה ישירה
            success = await database.save_user_reference_photo(
                user_id=current_user,
                file_path=f"reference_photos/{current_user}_{file.filename}",
                filename=file.filename,
                face_encoding=face_vector.tolist() if hasattr(face_vector, 'tolist') else face_vector
            )

            if not success:
                raise HTTPException(status_code=500, detail="Failed to save reference photo to database")

        # בדיקה שהתמונה נשמרה עם הוקטור
        saved_photo = await database.user_photos.find_one({
            "user_id": current_user,
            "is_reference": True
        })

        if not saved_photo or not saved_photo.get("face_encoding"):
            raise HTTPException(status_code=500, detail="Face vector not saved properly")

        print(f"Reference photo saved successfully!")
        print(f"Vector size in database: {len(saved_photo['face_encoding'])}")

        return {
            "success": True,
            "message": "תמונת הייחוס הועלתה בהצלחה באמצעות השירותים הקיימים שלך",
            "details": {
                "user_name": user_name,
                "faces_detected": len(face_vectors),
                "vector_size": len(saved_photo['face_encoding']),
                "file_name": file.filename,
                "file_size": len(contents),
                "extraction_method": "your_existing_face_extractor",
                "storage_method": "your_existing_image_storage",
                "vector_preview": saved_photo['face_encoding'][:5]  # 5 ערכים ראשונים
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error uploading reference photo: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/reference-photo-status")
async def get_reference_photo_status(current_user: str = Depends(get_current_user)):
    """בדיקת סטטוס תמונת ייחוס"""

    try:
        user = await database.find_user_by_id(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # שימוש בשירות הקיים שלך לקבלת תמונת ייחוס
        ref_data = await image_storage.get_user_reference_image(current_user)

        if not ref_data:
            return {
                "has_reference": False,
                "message": "לא קיימת תמונת ייחוס"
            }

        # בדיקת תקינות הוקטור
        face_encoding = ref_data.get("face_encoding")
        is_vector_valid = (
                face_encoding and
                isinstance(face_encoding, list) and
                len(face_encoding) > 0 and
                not all(x == 0.1 for x in face_encoding[:5])  # וודא שזה לא וקטור דמה
        )

        return {
            "has_reference": True,
            "vector_valid": is_vector_valid,
            "vector_size": len(face_encoding) if face_encoding else 0,
            "is_dummy_vector": all(x == 0.1 for x in face_encoding[:5]) if face_encoding else False,
            "file_name": ref_data.get("filename"),
            "uploaded_at": ref_data.get("uploaded_at"),
            "vector_preview": face_encoding[:5] if face_encoding else [],
            "message": "תמונת ייחוס קיימת" + (" עם וקטור פנים אמיתי" if is_vector_valid else " אבל הוקטור לא תקין"),
            "service_used": "your_existing_image_storage"
        }

    except Exception as e:
        print(f"Error checking reference photo status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-event-photos/{event_id}")
async def upload_event_photos(
        event_id: str,
        files: List[UploadFile] = File(...),
        current_user: str = Depends(get_current_user)
):
    """העלאת תמונות לאירוע באמצעות השירותים הקיימים שלך"""
    uploaded_photos = []
    failed_uploads = []

    # בדיקה שהאירוע קיים
    event = await database.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    is_manager = await verify_event_manager_by_id(event_id, current_user)
    if not is_manager:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only event managers can upload photos to this event."
        )
    print(f"Starting upload of {len(files)} files for event {event_id} using your services")

    for i, file in enumerate(files):
        try:
            print(f"Processing file {i + 1}/{len(files)}: {file.filename}")

            # ולידציה
            if not validate_image_file(file):
                failed_uploads.append({
                    "filename": file.filename,
                    "error": "Not a valid image file"
                })
                continue

            contents = await file.read()

            # בדיקת גודל
            # if len(contents) > MAX_FILE_SIZE:
            if len(contents) > FaceRecognitionConfig.MAX_FILE_SIZE:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": f"File too large (max {FaceRecognitionConfig.MAX_FILE_SIZE // (1024 * 1024)}MB)"
                })
                continue

            # שמירת התמונה באמצעות השירות הקיים שלך
            photo_id = await image_storage.save_event_photo(
                event_id=event_id,
                uploaded_by=current_user,
                image_data=contents,
                filename=file.filename
            )

            if photo_id:
                uploaded_photos.append({
                    "photo_id": photo_id,
                    "filename": file.filename,
                    "size": len(contents),
                    "storage_method": "your_existing_image_storage"
                })
                print(f"Successfully uploaded using your service: {file.filename}")
            else:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": "Failed to save using image storage service"
                })

        except Exception as e:
            print(f"Error uploading {file.filename}: {e}")
            failed_uploads.append({"filename": file.filename, "error": str(e)})

    print(f"Upload completed: {len(uploaded_photos)} success, {len(failed_uploads)} failed")

    return {
        "event_id": event_id,
        "uploaded_photos": len(uploaded_photos),
        "failed_uploads": len(failed_uploads),
        "storage_service": "your_existing_image_storage",
        "details": {
            "successful": uploaded_photos,
            "failed": failed_uploads
        }
    }


@router.get("/my-photos/{event_id}")
async def get_my_photos_in_event(
        event_id: str,
        current_user: str = Depends(get_current_user)
):
    #קבלת התמונות שלי מהאירוע
    try:
        # בדיקה שהאירוע קיים
        event = await database.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # קבלת ההתאמות שלי באירוע
        user_matches = await database.get_user_matches_in_event(current_user, event_id)

        # המרה לפורמט התגובה
        photos_info = []
        for match in user_matches:
            photos_info.append({
                "photo_id": match["event_photo_id"],
                "filename": match.get("photo_filename", "unknown.jpg"),
                "similarity": round(match["confidence_score"], 3),
                "confidence": match.get("confidence", "Medium"),
                "matched_at": match["matched_at"].isoformat() if "matched_at" in match else None
            })

        print(f"Found {len(photos_info)} photos for user {current_user} in event {event_id}")

        return {
            "event_id": event_id,
            "total_photos": len(photos_info),
            "photos": photos_info
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user photos: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving photos: {str(e)}")


@router.get("/health")
async def face_recognition_health():
     # בדיקת בריאות מודול זיהוי פנים
    try:
        # בדיקת חיבור למסד נתונים
        db_connected = True
        try:
            await database.users.count_documents({})
        except Exception as e:
            print(f"Database connection error: {e}")
            db_connected = False

        # בדיקת השירותים הקיימים שלך
        face_extractor_status = "available"
        try:
            # בדיקה שה-face_extractor הקיים שלך עובד
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            face_extractor.extract_multiple_faces(test_image)
            face_extractor_status = "available"
        except Exception as e:
            print(f"Your face_extractor error: {e}")
            face_extractor_status = "unavailable"

        # בדיקת שירות אחסון התמונות שלך
        image_storage_status = "available"
        try:
            # בדיקה שה-ImageStorageService שלך עובד
            image_storage.db  # בדיקה פשוטה
            image_storage_status = "available"
        except Exception as e:
            print(f"Your ImageStorageService error: {e}")
            image_storage_status = "unavailable"

        # מצב כללי
        overall_status = "healthy" if (db_connected and face_extractor_status == "available") else "degraded"

        return {
            "status": overall_status,
            "your_services": {
                "face_extractor": face_extractor_status,
                "image_storage": image_storage_status
            },
            "database_connected": db_connected,
            "components": {
                "database": "connected" if db_connected else "error",
                "your_face_features_extractor": face_extractor_status,
                "your_image_storage_service": image_storage_status
            },
            "message": "Using your existing services for face recognition"
        }
    except Exception as e:
        print(f"Health check error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


print("Face Recognition routes loaded using YOUR EXISTING SERVICES:")
print(" Using your face_features_extractor for face detection")
print(" Using your ImageStorageService for photo storage")
print(" Using your database structure")
print()
print("Available endpoints:")
print("  - POST /face-recognition/upload-reference-photo")
print("  - GET /face-recognition/reference-photo-status")
print("  - POST /face-recognition/upload-event-photos/{event_id}")
print("  - GET /face-recognition/my-photos/{event_id}")
print("  - GET /face-recognition/health")