import asyncio
import cv2
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pathlib import Path
import os
import shutil
import gc
from app.database import database
from app.services.face_features_extractor import face_extractor
from app.services.feature_vector_utils import compare_user_to_participants_vectors  # הפונקציה שלך!
from app.services.image_storage import ImageStorageService
from app.services.email_service import email_service
from app.config import FaceRecognitionConfig
from app.services.event_knn_manager import find_matches_in_event_knn_with_your_functions
#עיבוד תמונות אירוע
class AutomaticFaceProcessor:
    def __init__(self):
        self.image_storage = ImageStorageService(database)
        self.active_processing = {}

    def get_processing_status(self, event_id: str) -> Dict:
        if event_id not in self.active_processing:
            return {"status": "not_processing"}
        status = self.active_processing[event_id].copy()
        # חישוב זמן עיבוד עד כה
        if "start_time" in status:
            elapsed = datetime.now() - status["start_time"]
            status["elapsed_seconds"] = elapsed.total_seconds()
        return status

    async def process_event_photos_immediately(self, event_id: str,
                                               uploaded_photo_paths: List[str]) -> Dict:
        print(f" DEBUG: Starting REAL processing for {len(uploaded_photo_paths)} photos for event {event_id}")
        if event_id in self.active_processing:
            return {"error": "Event is already being processed"}

        self.active_processing[event_id] = {
            "status": "processing",
            "start_time": datetime.now(),
            "current_photo": 0,
            "total_photos": len(uploaded_photo_paths)
        }
        try:
            # שליפה ממסד נתונים 1. קבלת נתוני האירוע
            event = await database.events.find_one({"event_id": event_id})
            if not event:
                raise Exception(f"Event {event_id} not found")
            event_name = event.get("name", "Unknown Event")
            event_code = event.get("event_code", "Unknown")
            print(f" DEBUG: Event: {event_name} (Code: {event_code})")

            # 2. קבלת משתתפים עם תמונות ייחוס
            participants = await self.get_participants_with_reference_photos(event_id)
            if not participants:
                print(" DEBUG: No participants with reference photos found")
                return {
                    "status": "completed",
                    "message": "No participants with reference photos to compare against",
                    "photos_processed": 0,
                    "faces_detected": 0,
                    "matches_found": 0,
                    "processing_time": 0
                }
            print(f" DEBUG: Found {len(participants)} participants with reference photos")
            for p in participants:
                print(f"  - {p['name']} ({p['email']})")

            # 3. עיבוד כל תמונה
            user_photo_matches = {}  # {user_id: [photo_paths]}
            total_faces = 0
            total_matches = 0

            for idx, photo_path in enumerate(uploaded_photo_paths):
                self.active_processing[event_id]["current_photo"] = idx + 1
                print(f" DEBUG: Processing photo {idx + 1}/{len(uploaded_photo_paths)}: {Path(photo_path).name}")
                photo_results = await self.process_single_photo(
                    photo_path, participants, event_id
                )
                total_faces += photo_results["faces_found"]
                total_matches += photo_results["matches_found"]
                # צבירת התמונות לכל משתמש
                for user_id in photo_results["matched_users"]:
                    if user_id not in user_photo_matches:
                        user_photo_matches[user_id] = []
                    user_photo_matches[user_id].append(photo_path)

                if (idx + 1) % 10 == 0:
                    gc.collect()
                    print(f" DEBUG: Memory cleaned after {idx + 1} images")

            print(f" DEBUG: Summary: {total_faces} faces, {total_matches} matches, {len(user_photo_matches)} users")
            print(f"DEBUG: Users matched for emails:")
            for user_id, photos in user_photo_matches.items():
                user_name = next(p['name'] for p in participants if p['user_id'] == user_id)
                user_email = next(p['email'] for p in participants if p['user_id'] == user_id)
                print(f"  - {user_name} ({user_email}): {len(photos)} photos")
            # 4. ארגון תמונות ושליחת התראות
            notification_results = await self.organize_and_notify(
                user_photo_matches, participants, event_name, event_code
            )
            print(f" DEBUG: Email results: {notification_results}")
            # 5. תוצאות סופיות
            processing_time = (datetime.now() - self.active_processing[event_id]["start_time"]).total_seconds()
            final_results = {
                "status": "completed",
                "event_id": event_id,
                "event_name": event_name,
                "photos_processed": len(uploaded_photo_paths),
                "faces_detected": total_faces,
                "matches_found": total_matches,
                "users_with_photos": len(user_photo_matches),
                "emails_sent": notification_results["emails_sent"],
                "email_failures": len(notification_results["email_failures"]),
                "processing_time": round(processing_time, 2)
            }
            print(
                f"DEBUG: REAL Processing completed: {notification_results['emails_sent']} emails sent in {processing_time:.1f}s")
            return final_results
        except Exception as e:
            print(f"DEBUG: Processing failed: {e}")
            return {"error": str(e), "status": "failed"}
        finally:
            if event_id in self.active_processing:
                del self.active_processing[event_id]

    async def get_participants_with_reference_photos(self, event_id: str) -> List[Dict]:
        try:
            # קבלת וקטורי הפנים מהמסד - משתמש בפונקציה שכבר קיימת
            participants_vectors = await database.get_event_participants_vectors(event_id)
            print(f" DEBUG: Found {len(participants_vectors)} participants with vectors")

            participants_with_data = []
            for participant in participants_vectors:
                user_id = participant["user_id"]

                # קבלת פרטי המשתמש
                user = await database.find_user_by_id(user_id)
                if not user:
                    print(f"DEBUG: User {user_id} not found in database")
                    continue

                email = user.get("email", "")
                name = user.get("name", f"User {user_id}")

                if not email:
                    print(f"DEBUG: User {name} has no email address")
                participants_with_data.append({
                    "user_id": user_id,
                    "name": name,
                    "email": email,
                    "face_encoding": participant["face_encoding"]
                })
                print(f"DEBUG: {name} ({email if email else 'NO EMAIL'}) - ready for matching")
            return participants_with_data
        except Exception as e:
            print(f" DEBUG: Error getting participants vectors: {e}")
            return []

    async def process_single_photo(self, photo_path: str, participants: List[Dict], event_id: str) -> Dict:
        results = {
            "faces_found": 0,
            "matches_found": 0,
            "matched_users": []
        }
        try:
            if not os.path.exists(photo_path):
                print(f"DEBUG: Photo not found: {photo_path}")
                return results
            # טעינת התמונה לזיכרון באמצעות cv2
            image = cv2.imread(photo_path)
            if image is None:
                print(f"  DEBUG: Failed to load image")
                return results
            # בדיקת מוכנות face_extractor
            if not face_extractor.is_ready:
                print(f" DEBUG: Face extractor not ready")
                return results
            face_vectors = face_extractor.extract_multiple_faces(image)
            results["faces_found"] = len(face_vectors)
            if not face_vectors:
                print(f" DEBUG: No faces detected")
                return results
            print(f"  DEBUG: Found {len(face_vectors)} faces")
            # שמירת התמונה במסד נתונים
            photo_id = await self._save_photo_to_database(photo_path, event_id)
            print(f"DEBUG: Photo saved with ID: {photo_id}")
            for face_idx, face_vector in enumerate(face_vectors):
                print(f"DEBUG: Analyzing face {face_idx + 1}...")
                # השוואה עם המשתתפים באמצעות הפונקציה שלך
                # matches = compare_user_to_participants_vectors(
                #     face_vector,
                #     participants,
                #     similarity_threshold=FaceRecognitionConfig.SIMILARITY_THRESHOLD
                #  )
                try:
                    #  KNN מהיר שמשתמש
                    matches = await find_matches_in_event_knn_with_your_functions(
                        event_id,
                        face_vector,
                        similarity_threshold=FaceRecognitionConfig.SIMILARITY_THRESHOLD
                    )
                    print(f"Using KNN matching for event {event_id}")

                except Exception as knn_error:
                    print(f" KNN failed for event {event_id}, using fallback: {knn_error}")
                    # fallback לשיטה הישנה
                    matches = compare_user_to_participants_vectors(
                        face_vector,
                        participants,
                        similarity_threshold=FaceRecognitionConfig.SIMILARITY_THRESHOLD
                    )
                    print(f" Using original matching method")

                if matches:
                    best_match = matches[0]  # הטוב ביותר
                    matched_user = next(p for p in participants if p["user_id"] == best_match["user_id"])
                    print(f" DEBUG: MATCH: {matched_user['name']} (Similarity: {best_match['similarity']:.3f})")

                    # שמירת ההתאמה במסד נתונים
                    if photo_id:
                        try:
                            await database.save_face_match(
                                user_id=best_match["user_id"],
                                event_id=event_id,
                                photo_id=photo_id,
                                similarity_score=best_match["similarity"],
                                face_index=face_idx
                            )
                            results["matches_found"] += 1
                            if best_match["user_id"] not in results["matched_users"]:
                                results["matched_users"].append(best_match["user_id"])

                        except Exception as e:
                            print(f" DEBUG: Error saving match: {e}")
                else:
                    print(f" DEBUG: No match for face {face_idx + 1}")
            print(f"DEBUG: Photo results: {results['faces_found']} faces, {results['matches_found']} matches")
            return results
        except Exception as e:
            print(f" DEBUG: Error processing {photo_path}: {e}")
            return results
        #מנקה זיכרון
        finally:
            try:
                del image, face_vectors
                gc.collect()
            except:
                pass

    async def _save_photo_to_database(self, photo_path: str, event_id: str) -> Optional[str]:
        try:
            photo_filename = Path(photo_path).name
            # בדיקה אם התמונה כבר קיימת
            existing_photo = await database.event_photos.find_one({
                "event_id": event_id,
                "file_name": photo_filename
            })

            if existing_photo:
                print(f" DEBUG: Photo already exists with ID: {existing_photo['photo_id']}")
                return existing_photo["photo_id"]

            # שמירת תמונה חדשה באמצעות השירות שלך
            with open(photo_path, 'rb') as f:
                image_data = f.read()

            photo_id = await self.image_storage.save_event_photo(
                event_id=event_id,
                uploaded_by="system_processor",
                image_data=image_data,
                filename=photo_filename
            )
            print(f" DEBUG: New photo saved with ID: {photo_id}")
            return photo_id
        except Exception as e:
            print(f"DEBUG: Error saving photo to database: {e}")
            return None

    async def organize_and_notify(self, user_photo_matches: Dict, participants: List[Dict],
                                  event_name: str, event_code: str) -> Dict:
        # יצירת תיקיית בסיס
        user_photos_base = Path("uploads/user_event_photos")
        user_photos_base.mkdir(exist_ok=True)
        emails_sent = 0
        email_failures = []

        for user_id, photo_paths in user_photo_matches.items():
            try:
                user_data = next(p for p in participants if p["user_id"] == user_id)
                user_name = user_data['name']
                user_email = user_data.get('email', '')
                # יצירת תיקיית משתמש
                user_folder = user_photos_base / f"user_{user_id}_{event_code}"
                user_folder.mkdir(exist_ok=True)
                print(f" DEBUG: Created folder: {user_folder}")

                # העתקת תמונות לתיקיית המשתמש
                copied_photos = []
                for photo_path in photo_paths:
                    try:
                        source_path = Path(photo_path)
                        if source_path.exists():
                            dest_filename = f"{event_code}_{source_path.name}"
                            dest_path = user_folder / dest_filename
                            shutil.copy2(source_path, dest_path)
                            copied_photos.append(str(dest_path))
                            print(f" DEBUG: Copied {source_path.name}")
                    except Exception as e:
                        print(f"DEBUG: Failed to copy {photo_path}: {e}")

                print(f"DEBUG: Copied {len(copied_photos)} photos to {user_folder}")
                # שליחת מייל התראה
                if user_email and copied_photos:
                    print(f" DEBUG: Attempting to send email to {user_email}")
                    try:
                        success = await self.send_notification_email(
                            user_data, len(copied_photos), event_name, event_code
                        )
                        if success:
                            emails_sent += 1
                            print(f" DEBUG: Email sent successfully to {user_email}")
                        else:
                            email_failures.append(user_email)
                            print(f" DEBUG: Email failed to {user_email}")
                    except Exception as e:
                        email_failures.append(f"{user_email}: {str(e)}")
                        print(f"DEBUG: Email error: {e}")
                elif not user_email:
                    print(f" DEBUG: No email address for {user_name}")
                elif not copied_photos:
                    print(f"DEBUG: No photos copied for {user_name}")
            except Exception as e:
                print(f" DEBUG: Error processing user {user_id}: {e}")
        print(f"DEBUG: Final email results: {emails_sent} sent, {len(email_failures)} failed")
        return {
            "emails_sent": emails_sent,
            "email_failures": email_failures
        }

    async def send_notification_email(self, user_data: Dict, photo_count: int,
                                      event_name: str, event_code: str) -> bool:
        try:
            user_name = user_data["name"]
            user_email = user_data["email"]
            # שליחה אסינכרונית עם המיילים המעוצבים החדשים
            success = await asyncio.get_event_loop().run_in_executor(
                None,
                email_service.send_photo_notification,
                user_email,
                user_name,
                event_name,
                photo_count,
                event_code
            )
            print(f"DEBUG: Email service returned: {success}")
            return success
        except Exception as e:
            print(f"DEBUG: Error in send_notification_email: {e}")
            return False
# יצירת instance גלובלי
automatic_processor = AutomaticFaceProcessor()
# ייצוא לשימוש חיצוני
__all__ = ["AutomaticFaceProcessor", "automatic_processor"]