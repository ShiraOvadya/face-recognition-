# # app/routers/face_recognition_enhanced.py - עם עיבוד אוטומטי אמיתי
# from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
# from typing import List
# from pathlib import Path
# from app.routers.auth import get_current_user
# from app.database import database
# from app.services.automatic_processor import automatic_processor
#
# router = APIRouter(prefix="/face-recognition", tags=["Face Recognition Enhanced"])
#
#
# @router.post("/upload-and-process-event-photos/{event_id}")
# async def upload_and_process_event_photos(
#         event_id: str,
#         photos: List[UploadFile] = File(...),
#         current_user: str = Depends(get_current_user)
# ):
#     """
#     🚀 העלאת תמונות אירוע + עיבוד אוטומטי מיידי אמיתי + שליחת מיילים
#     זה הנתיב הראשי שמבצע הכל!
#     """
#
#     print(f"🚀 Starting REAL upload and process for event {event_id}")
#     print(f"📸 Received {len(photos)} photos for automatic processing")
#
#     try:
#         # בדיקת הרשאות
#         event = await database.events.find_one({"event_id": event_id})
#         if not event:
#             raise HTTPException(status_code=404, detail="Event not found")
#
#         # בדיקה שהמשתמש מורשה (בעל האירוע או משתתף)
#         is_creator = event["created_by"] == current_user
#         is_participant = await database.event_participants.find_one({
#             "event_id": event_id,
#             "user_id": current_user
#         })
#
#         if not is_creator and not is_participant:
#             raise HTTPException(status_code=403, detail="Not authorized to upload photos to this event")
#
#         event_name = event.get("name", "Unknown Event")
#         event_code = event.get("event_code", "Unknown")
#
#         print(f"📅 Event: {event_name} (Code: {event_code})")
#         print(f"👤 Uploader: {'Owner' if is_creator else 'Participant'}")
#
#         # העלאת התמונות לתיקיית האירוע
#         event_photos_dir = Path("uploads/event_photos") / event_id
#         event_photos_dir.mkdir(parents=True, exist_ok=True)
#
#         uploaded_photo_paths = []
#         upload_errors = []
#
#         for idx, photo in enumerate(photos):
#             try:
#                 print(f"   📸 Uploading photo {idx + 1}: {photo.filename}")
#
#                 if not photo.content_type.startswith("image/"):
#                     upload_errors.append(f"{photo.filename}: Not an image file")
#                     continue
#
#                 # שמירת התמונה לדיסק
#                 photo_path = event_photos_dir / photo.filename
#                 with open(photo_path, "wb") as buffer:
#                     content = await photo.read()
#                     buffer.write(content)
#
#                 uploaded_photo_paths.append(str(photo_path))
#                 print(f"   ✅ Saved: {photo_path}")
#
#             except Exception as e:
#                 error_msg = f"{photo.filename}: {str(e)}"
#                 upload_errors.append(error_msg)
#                 print(f"   ❌ Failed: {error_msg}")
#
#         if not uploaded_photo_paths:
#             raise HTTPException(status_code=400, detail="No photos were uploaded successfully")
#
#         print(f"✅ Upload completed: {len(uploaded_photo_paths)} photos saved")
#
#         # עיבוד אוטומטי מיידי אמיתי עם המערכת שלך!
#         print(f"🤖 Starting REAL AUTOMATIC FACE RECOGNITION...")
#         print(f"🔍 Will detect faces and match against all participants")
#         print(f"📧 Will send emails to participants found in photos")
#
#         try:
#             # קריאה לעיבוד האמיתי שלך - זה יעשה הכל!
#             processing_results = await automatic_processor.process_event_photos_immediately(
#                 event_id=event_id,
#                 uploaded_photo_paths=uploaded_photo_paths
#             )
#
#             if "error" in processing_results:
#                 print(f"❌ Processing error: {processing_results['error']}")
#                 raise HTTPException(status_code=500, detail=processing_results["error"])
#
#             print(f"✅ REAL PROCESSING COMPLETED!")
#             print(f"📊 Results: {processing_results}")
#
#             # תוצאות מפורטות
#             final_results = {
#                 "success": True,
#                 "message": "תמונות הועלו ועובדו בהצלחה עם זיהוי פנים אמיתי ושליחת מיילים",
#                 "event_id": event_id,
#                 "event_name": event_name,
#                 "upload_summary": {
#                     "photos_uploaded": len(uploaded_photo_paths),
#                     "upload_errors": upload_errors
#                 },
#                 "processing_summary": processing_results,
#                 "automatic_features": {
#                     "face_recognition": "REAL_COMPLETED",
#                     "email_notifications": f"{processing_results.get('emails_sent', 0)} emails sent",
#                     "matches_found": processing_results.get('matches_found', 0),
#                     "participants_notified": processing_results.get('users_with_photos', 0),
#                     "faces_detected": processing_results.get('faces_detected', 0)
#                 },
#                 "processing_type": "REAL_FACE_RECOGNITION_WITH_EMAILS"
#             }
#
#             return final_results
#
#         except Exception as processing_error:
#             print(f"❌ Processing error: {processing_error}")
#             raise HTTPException(status_code=500, detail=f"Processing failed: {str(processing_error)}")
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"❌ General error: {e}")
#         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
#
#
# @router.get("/processing-status/{event_id}")
# async def get_processing_status(
#         event_id: str,
#         current_user: str = Depends(get_current_user)
# ):
#     """📊 קבלת סטטוס עיבוד לאירוע - אמיתי"""
#
#     try:
#         event = await database.events.find_one({"event_id": event_id})
#         if not event:
#             raise HTTPException(status_code=404, detail="Event not found")
#
#         # בדיקה אם האירוע נמצא בעיבוד אמיתי
#         try:
#             processing_status = await automatic_processor.get_processing_status(event_id)
#
#             if processing_status["status"] == "processing":
#                 return {
#                     "status": "processing",
#                     "details": processing_status,
#                     "message": "Real face recognition in progress",
#                     "processing_type": "REAL_FACE_RECOGNITION"
#                 }
#         except:
#             processing_status = {"status": "not_processing"}
#
#         # בדיקת תוצאות עיבוד קיימות
#         try:
#             # ספירת זיהויים
#             matches = await database.face_detections.find({"event_id": event_id}).to_list(None)
#             event_photos = await database.event_photos.find({"event_id": event_id}).to_list(None)
#
#             # ספירת משתתפים ייחודיים שנמצאו
#             unique_users = set()
#             for match in matches:
#                 user_id = match.get("detected_user_id") or match.get("user_id")
#                 if user_id:
#                     unique_users.add(user_id)
#
#         except:
#             matches = []
#             event_photos = []
#             unique_users = set()
#
#         return {
#             "status": "completed" if matches else "not_started",
#             "event_id": event_id,
#             "event_name": event.get("name"),
#             "statistics": {
#                 "total_photos": len(event_photos),
#                 "total_matches": len(matches),
#                 "unique_users_found": len(unique_users),
#                 "processing_complete": len(matches) > 0
#             },
#             "processing_type": "REAL_FACE_RECOGNITION" if matches else "NONE",
#             "message": f"Found {len(unique_users)} participants in {len(event_photos)} photos" if matches else "No processing completed yet"
#         }
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"❌ Error getting processing status: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.get("/user-photos/{event_id}")
# async def get_user_photos_for_event(
#         event_id: str,
#         current_user: str = Depends(get_current_user)
# ):
#     """📷 קבלת התמונות של המשתמש מאירוע מסוים"""
#
#     try:
#         event = await database.events.find_one({"event_id": event_id})
#         if not event:
#             raise HTTPException(status_code=404, detail="Event not found")
#
#         # קבלת כל ההתאמות של המשתמש באירוע הזה
#         try:
#             user_matches = await database.face_detections.find({
#                 "event_id": event_id,
#                 "$or": [
#                     {"detected_user_id": current_user},
#                     {"user_id": current_user}
#                 ]
#             }).to_list(None)
#         except:
#             user_matches = []
#
#         if not user_matches:
#             return {
#                 "event_id": event_id,
#                 "event_name": event.get("name"),
#                 "user_photos": [],
#                 "total_photos": 0,
#                 "message": "No photos found for this user in this event",
#                 "processing_type": "REAL_FACE_RECOGNITION"
#             }
#
#         # קבלת פרטי התמונות
#         photo_ids = list(set([
#             match.get("event_photo_id") or match.get("photo_id")
#             for match in user_matches if match.get("event_photo_id") or match.get("photo_id")
#         ]))
#
#         photos = []
#         for photo_id in photo_ids:
#             try:
#                 photo = await database.event_photos.find_one({"photo_id": photo_id})
#                 if photo:
#                     # ספירת ההתאמות בתמונה הזו
#                     matches_in_photo = [
#                         m for m in user_matches
#                         if (m.get("event_photo_id") or m.get("photo_id")) == photo_id
#                     ]
#
#                     photos.append({
#                         "photo_id": photo_id,
#                         "filename": photo["file_name"],
#                         "file_path": photo.get("file_path"),
#                         "uploaded_at": photo.get("uploaded_at"),
#                         "matches_count": len(matches_in_photo),
#                         "confidence_scores": [
#                             m.get("similarity_score") or m.get("confidence_score", 0)
#                             for m in matches_in_photo
#                         ]
#                     })
#             except:
#                 continue
#
#         user = await database.find_user_by_id(current_user)
#         user_name = user.get("name", "Unknown") if user else "Unknown"
#
#         return {
#             "event_id": event_id,
#             "event_name": event.get("name"),
#             "participant_name": user_name,
#             "user_photos": photos,
#             "total_photos": len(photos),
#             "total_matches": len(user_matches),
#             "user_folder": f"uploads/user_event_photos/user_{current_user}_{event.get('event_code', 'unknown')}",
#             "processing_type": "REAL_FACE_RECOGNITION",
#             "message": f"נמצאו {len(photos)} תמונות של {user_name} באירוע"
#         }
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"❌ Error getting user photos: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# print("🚀 ENHANCED REAL FACE RECOGNITION SYSTEM LOADED:")
# print("📸 AUTOMATIC PROCESSING:")
# print("  - POST /face-recognition/upload-and-process-event-photos/{event_id}")
# print("    → Upload + Real Face Detection + Email Notifications")
# print()
# print("📊 MONITORING:")
# print("  - GET /face-recognition/processing-status/{event_id}")
# print("  - GET /face-recognition/user-photos/{event_id}")
# print()
# print("🎯 CORE FEATURES:")
# print("  ✅ Real face recognition with your face_extractor")
# print("  ✅ Automatic email notifications")
# print("  ✅ Multiple faces per photo support")
# print("  ✅ Photo organization per user")
# print("  ✅ Real-time processing status")


# app/routers/face_recognition_enhanced.py - עם עיבוד אוטומטי אמיתי
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from typing import List
from pathlib import Path
from app.routers.auth import get_current_user ,verify_event_manager_by_id
from app.database import database
from app.services.automatic_processor import automatic_processor

router = APIRouter(prefix="/face-recognition", tags=["Face Recognition Enhanced"])


@router.post("/upload-and-process-event-photos/{event_id}")
async def upload_and_process_event_photos(
        event_id: str,
        photos: List[UploadFile] = File(...),
        current_user: str = Depends(get_current_user)
):


    print(f"Starting REAL upload and process for event {event_id}")
    print(f"Received {len(photos)} photos for automatic processing")

    try:
        # בדיקת הרשאות
        event = await database.events.find_one({"event_id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        is_manager = await verify_event_manager_by_id(event_id, current_user)
        if not is_manager:
            raise HTTPException(
                status_code=403,
                detail="Access denied. Only event managers can upload and process photos."
            )

        # # בדיקה שהמשתמש מורשה (בעל האירוע או משתתף)
        # is_creator = event["created_by"] == current_user
        # is_participant = await database.event_participants.find_one({
        #     "event_id": event_id,
        #     "user_id": current_user
        # })
        #
        # if not is_creator and not is_participant:
        #     raise HTTPException(status_code=403, detail="Not authorized to upload photos to this event")

        event_name = event.get("name", "Unknown Event")
        event_code = event.get("event_code", "Unknown")

        print(f"Event: {event_name} (Code: {event_code})")
        print(f"Uploader: Event Manager")

        # העלאת התמונות לתיקיית האירוע
        event_photos_dir = Path("uploads/event_photos") / event_id
        event_photos_dir.mkdir(parents=True, exist_ok=True)

        uploaded_photo_paths = []
        upload_errors = []

        for idx, photo in enumerate(photos):
            try:
                print(f"Uploading photo {idx + 1}: {photo.filename}")

                if not photo.content_type.startswith("image/"):
                    upload_errors.append(f"{photo.filename}: Not an image file")
                    continue

                # שמירת התמונה לדיסק
                photo_path = event_photos_dir / photo.filename
                with open(photo_path, "wb") as buffer:
                    content = await photo.read()
                    buffer.write(content)

                uploaded_photo_paths.append(str(photo_path))
                print(f"Saved: {photo_path}")

            except Exception as e:
                error_msg = f"{photo.filename}: {str(e)}"
                upload_errors.append(error_msg)
                print(f" Failed: {error_msg}")

        if not uploaded_photo_paths:
            raise HTTPException(status_code=400, detail="No photos were uploaded successfully")

        print(f"Upload completed: {len(uploaded_photo_paths)} photos saved")

        # # עיבוד אוטומטי מיידי אמיתי עם המערכת שלך!
        # print(f"Starting REAL AUTOMATIC FACE RECOGNITION...")
        # print(f"Will detect faces and match against all participants")
        # print(f"Will send emails to participants found in photos")

        try:
            processing_results = await automatic_processor.process_event_photos_immediately(
                event_id=event_id,
                uploaded_photo_paths=uploaded_photo_paths
            )

            if "error" in processing_results:
                print(f"Processing error: {processing_results['error']}")
                raise HTTPException(status_code=500, detail=processing_results["error"])

            print(f"REAL PROCESSING COMPLETED!")
            print(f"Results: {processing_results}")

            # תוצאות מפורטות
            final_results = {
                "success": True,
                "message": "תמונות הועלו ועובדו בהצלחה עם זיהוי פנים אמיתי ושליחת מיילים",
                "event_id": event_id,
                "event_name": event_name,
                "upload_summary": {
                    "photos_uploaded": len(uploaded_photo_paths),
                    "upload_errors": upload_errors
                },
                "processing_summary": processing_results,
                "automatic_features": {
                    "face_recognition": "REAL_COMPLETED",
                    "email_notifications": f"{processing_results.get('emails_sent', 0)} emails sent",
                    "matches_found": processing_results.get('matches_found', 0),
                    "participants_notified": processing_results.get('users_with_photos', 0),
                    "faces_detected": processing_results.get('faces_detected', 0)
                },
                "processing_type": "REAL_FACE_RECOGNITION_WITH_EMAILS"
            }

            return final_results

        except Exception as processing_error:
            print(f"Processing error: {processing_error}")
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(processing_error)}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"General error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/processing-status/{event_id}")
async def get_processing_status(
        event_id: str,
        current_user: str = Depends(get_current_user)
):


    try:
        event = await database.events.find_one({"event_id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # בדיקה אם האירוע נמצא בעיבוד אמיתי
        try:
            processing_status = await automatic_processor.get_processing_status(event_id)

            if processing_status["status"] == "processing":
                return {
                    "status": "processing",
                    "details": processing_status,
                    "message": "Real face recognition in progress",
                    "processing_type": "REAL_FACE_RECOGNITION"
                }
        except:
            processing_status = {"status": "not_processing"}

        # בדיקת תוצאות עיבוד קיימות
        try:
            # ספירת זיהויים
            matches = await database.face_detections.find({"event_id": event_id}).to_list(None)
            event_photos = await database.event_photos.find({"event_id": event_id}).to_list(None)

            # ספירת משתתפים ייחודיים שנמצאו
            unique_users = set()
            for match in matches:
                user_id = match.get("detected_user_id") or match.get("user_id")
                if user_id:
                    unique_users.add(user_id)

        except:
            matches = []
            event_photos = []
            unique_users = set()

        return {
            "status": "completed" if matches else "not_started",
            "event_id": event_id,
            "event_name": event.get("name"),
            "statistics": {
                "total_photos": len(event_photos),
                "total_matches": len(matches),
                "unique_users_found": len(unique_users),
                "processing_complete": len(matches) > 0
            },
            "processing_type": "REAL_FACE_RECOGNITION" if matches else "NONE",
            "message": f"Found {len(unique_users)} participants in {len(event_photos)} photos" if matches else "No processing completed yet"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-photos/{event_id}")
async def get_user_photos_for_event(
        event_id: str,
        current_user: str = Depends(get_current_user)
):

    try:
        event = await database.events.find_one({"event_id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # קבלת כל ההתאמות של המשתמש באירוע הזה
        try:
            user_matches = await database.face_detections.find({
                "event_id": event_id,
                "$or": [
                    {"detected_user_id": current_user},
                    {"user_id": current_user}
                ]
            }).to_list(None)
        except:
            user_matches = []

        if not user_matches:
            return {
                "event_id": event_id,
                "event_name": event.get("name"),
                "user_photos": [],
                "total_photos": 0,
                "message": "No photos found for this user in this event",
                "processing_type": "REAL_FACE_RECOGNITION"
            }

        # קבלת פרטי התמונות
        photo_ids = list(set([
            match.get("event_photo_id") or match.get("photo_id")
            for match in user_matches if match.get("event_photo_id") or match.get("photo_id")
        ]))

        photos = []
        for photo_id in photo_ids:
            try:
                photo = await database.event_photos.find_one({"photo_id": photo_id})
                if photo:
                    # ספירת ההתאמות בתמונה הזו
                    matches_in_photo = [
                        m for m in user_matches
                        if (m.get("event_photo_id") or m.get("photo_id")) == photo_id
                    ]

                    photos.append({
                        "photo_id": photo_id,
                        "filename": photo["file_name"],
                        "file_path": photo.get("file_path"),
                        "uploaded_at": photo.get("uploaded_at"),
                        "matches_count": len(matches_in_photo),
                        "confidence_scores": [
                            m.get("similarity_score") or m.get("confidence_score", 0)
                            for m in matches_in_photo
                        ]
                    })
            except:
                continue

        user = await database.find_user_by_id(current_user)
        user_name = user.get("name", "Unknown") if user else "Unknown"

        return {
            "event_id": event_id,
            "event_name": event.get("name"),
            "participant_name": user_name,
            "user_photos": photos,
            "total_photos": len(photos),
            "total_matches": len(user_matches),
            "user_folder": f"uploads/user_event_photos/user_{current_user}_{event.get('event_code', 'unknown')}",
            "processing_type": "REAL_FACE_RECOGNITION",
            "message": f"נמצאו {len(photos)} תמונות של {user_name} באירוע"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user photos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === התוספות החדשות לגלריה ===

@router.get("/my-photos-with-images/{event_id}")
async def get_my_photos_with_images(
        event_id: str,
        current_user: str = Depends(get_current_user)
):
    """קבלת התמונות שלי מהאירוע עם התמונות עצמן"""
    try:
        from app.services.image_storage import ImageStorageService
        image_storage = ImageStorageService(database)

        print(f"Getting photos for user {current_user} in event {event_id}")

        # קבלת כל ההתאמות שלי באירוע
        user_matches = await database.face_detections.find({
            "event_id": event_id,
            "$or": [
                {"detected_user_id": current_user},
                {"user_id": current_user}
            ]
        }).to_list(None)

        print(f"Found {len(user_matches)} matches")

        photos_with_data = []
        processed_photo_ids = set()

        for match in user_matches:
            try:
                photo_id = match.get("event_photo_id") or match.get("photo_id")
                if not photo_id or photo_id in processed_photo_ids:
                    continue

                processed_photo_ids.add(photo_id)
                print(f"Processing photo {photo_id}")

                # קבלת נתוני התמונה
                photo_data = await database.event_photos.find_one({"photo_id": photo_id})
                if not photo_data:
                    print(f"Photo data not found for {photo_id}")
                    continue

                # קבלת התמונה עצמה
                image_bytes = await image_storage.get_event_photo_by_path(
                    photo_data["file_path"]
                )

                if not image_bytes:
                    print(f"Image file not found for {photo_id}")
                    continue

                # המרה ל-base64 להצגה בדפדפן
                import base64
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')

                photos_with_data.append({
                    "photo_id": photo_id,
                    "filename": photo_data.get("file_name", f"photo_{len(photos_with_data) + 1}.jpg"),
                    "matched_at": match.get("matched_at"),
                    "image_data": f"data:image/jpeg;base64,{image_base64}"
                })
                print(f"Photo {photo_id} processed successfully")

            except Exception as e:
                print(f"Error processing photo: {e}")
                continue

        print(f"Returning {len(photos_with_data)} photos")
        return {
            "event_id": event_id,
            "total_photos": len(photos_with_data),
            "photos": photos_with_data
        }

    except Exception as e:
        print(f"Error in get_my_photos_with_images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-photo/{photo_id}")
async def download_photo(
        photo_id: str,
        current_user: str = Depends(get_current_user)
):
    try:
        from app.services.image_storage import ImageStorageService
        from fastapi.responses import Response

        image_storage = ImageStorageService(database)

        print(f"Download request: user {current_user}, photo {photo_id}")

        # בדיקה שהמשתמש מורשה לראות את התמונה הזו
        user_match = await database.face_detections.find_one({
            "$or": [
                {"detected_user_id": current_user, "event_photo_id": photo_id},
                {"user_id": current_user, "event_photo_id": photo_id},
                {"detected_user_id": current_user, "photo_id": photo_id},
                {"user_id": current_user, "photo_id": photo_id}
            ]
        })

        if not user_match:
            print(f"Access denied: user {current_user} not found in photo {photo_id}")
            raise HTTPException(status_code=403, detail="Access denied")

        # קבלת התמונה
        photo_data = await database.event_photos.find_one({"photo_id": photo_id})
        if not photo_data:
            print(f"Photo data not found: {photo_id}")
            raise HTTPException(status_code=404, detail="Photo not found")

        image_bytes = await image_storage.get_event_photo_by_path(photo_data["file_path"])
        if not image_bytes:
            print(f"Image file not found: {photo_data['file_path']}")
            raise HTTPException(status_code=404, detail="Photo file not found")

        filename = photo_data.get('file_name', 'photo.jpg')
        print(f"Serving download: {filename}")

        # החזרת התמונה להורדה
        return Response(
            content=image_bytes,
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f" Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# print("ENHANCED REAL FACE RECOGNITION SYSTEM LOADED:")
# print("AUTOMATIC PROCESSING:")
# print("  - POST /face-recognition/upload-and-process-event-photos/{event_id}")
# print("    → Upload + Real Face Detection + Email Notifications")
# print()
# print("MONITORING:")
# print("  - GET /face-recognition/processing-status/{event_id}")
# print("  - GET /face-recognition/user-photos/{event_id}")
# print("  - GET /face-recognition/my-photos-with-images/{event_id}")
# print("  - GET /face-recognition/download-photo/{photo_id}")
# print()
# print(" CORE FEATURES:")
# print(" Real face recognition with your face_extractor")
# print(" Automatic email notifications")
# print(" Multiple faces per photo support")
# print(" Photo organization per user")
# print("Real-time processing status")
# print("Photo gallery and download")