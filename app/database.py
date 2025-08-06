
# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Optional, List
import uuid
from datetime import datetime, timezone
import os
import random
import string

class Database:
    def __init__(self, connection_string: str = None):
        if connection_string is None:
            connection_string = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client.face_recognition_db

        # Collections
        self.users = self.db.users
        self.events = self.db.events
        self.event_participants = self.db.event_participants
        self.user_photos = self.db.user_photos
        self.event_photos = self.db.event_photos
        self.face_detections = self.db.face_detections

    async def init_database(self):
        #אתחול המסד נתונים והאינדקסים
        try:
            # Users indexes
            await self.users.create_index("email", unique=True)
            await self.users.create_index("user_id", unique=True)

            # Events indexes
            await self.events.create_index("event_code", unique=True)
            await self.events.create_index("event_id", unique=True)

            # Event participants indexes
            await self.event_participants.create_index(
                [("event_id", 1), ("user_id", 1)],
                unique=True
            )

            # User photos indexes
            await self.user_photos.create_index("user_id")
            await self.user_photos.create_index([("user_id", 1), ("is_reference", 1)])

            # Event photos indexes
            await self.event_photos.create_index("event_id")
            await self.event_photos.create_index("photo_id", unique=True)

            # Face detections indexes
            await self.face_detections.create_index("event_photo_id")
            await self.face_detections.create_index("detected_user_id")
            await self.face_detections.create_index("event_id")

            print(" Database initialized with all indexes")
        except Exception as e:
            print(f" Error initializing database: {e}")
            raise e

    # ===========================
    # User Methods
    # ===========================

    async def add_user(self, name: str, email: str, password_hash: str) -> str:
        #הוספת משתמש חדש
        try:
            existing_user = await self.users.find_one({"email": email})
            if existing_user:
                raise ValueError("User with this email already exists")

            user_id = str(uuid.uuid4())
            user_doc = {
                "user_id": user_id,
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "created_at": datetime.now(timezone.utc)
            }

            await self.users.insert_one(user_doc)
            return user_id
        except Exception as e:
            print(f"Error adding user: {e}")
            raise e

    async def find_user_by_email(self, email: str) -> Optional[Dict]:
       # חיפוש משתמש לפי אימייל
        user = await self.users.find_one({"email": email})
        if user:
            user.pop('_id', None)
        return user

    async def find_user_by_id(self, user_id: str) -> Optional[Dict]:
        user = await self.users.find_one({"user_id": user_id})
        if user:
            user.pop('_id', None)
        return user

    # ===========================
    # Event Methods
    # ===========================

    async def create_event(self, name: str, event_code: str, created_by: str) -> str:
       # יצירת אירוע חדש
        try:
            existing_event = await self.events.find_one({"event_code": event_code})
            if existing_event:
                raise ValueError("Event code already exists")

            event_id = str(uuid.uuid4())
            event_doc = {
                "event_id": event_id,
                "name": name,
                "event_code": event_code,
                "created_by": created_by,
                "created_at": datetime.now(timezone.utc)
            }

            await self.events.insert_one(event_doc)
            await self.join_event(event_code, created_by)

            return event_id
        except Exception as e:
            print(f"Error creating event: {e}")
            raise e

    async def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """קבלת אירוע לפי ID"""
        event = await self.events.find_one({"event_id": event_id})
        if event:
            event.pop('_id', None)
        return event

    async def get_event_by_code(self, event_code: str) -> Optional[Dict]:
        #קבלת אירוע לפי קוד
        event = await self.events.find_one({"event_code": event_code})
        if event:
            event.pop('_id', None)
        return event

    # ===========================
    # Event Participants Methods
    # ===========================

    async def join_event(self, event_code: str, user_id: str) -> bool:
        # הצטרפות לאירוע
        try:
            event = await self.get_event_by_code(event_code)
            if not event:
                return False

            existing = await self.event_participants.find_one({
                "event_id": event["event_id"],
                "user_id": user_id
            })

            if existing:
                return True

            participant_doc = {
                "event_id": event["event_id"],
                "user_id": user_id,
                "joined_at": datetime.now(timezone.utc)
            }

            await self.event_participants.insert_one(participant_doc)
            return True
        except Exception as e:
            print(f"Error joining event: {e}")
            return False

    async def get_user_events(self, user_id: str) -> List[Dict]:
        """קבלת כל האירועים של משתמש"""
        try:
            participations = await self.event_participants.find(
                {"user_id": user_id}
            ).to_list(None)

            event_ids = [p["event_id"] for p in participations]

            events = await self.events.find(
                {"event_id": {"$in": event_ids}}
            ).to_list(None)

            for event in events:
                event.pop('_id', None)

            return events
        except Exception as e:
            print(f"Error getting user events: {e}")
            return []

    # ===========================
    # User Photos Methods - עם וקטורים במסד
    # ===========================

    async def save_user_photo(self, user_id: str, file_path: str, file_name: str,
                              file_size: int, mime_type: str,
                              face_encoding: List[float],
                              is_primary: bool = False) -> str:
        """שמירת תמונת משתמש עם וקטור פנים במסד"""
        try:
            photo_id = str(uuid.uuid4())

            if is_primary:
                await self.user_photos.update_many(
                    {"user_id": user_id, "is_primary": True},
                    {"$set": {"is_primary": False}}
                )

            photo_doc = {
                "photo_id": photo_id,
                "user_id": user_id,
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "mime_type": mime_type,
                "face_encoding": face_encoding,
                "is_primary": is_primary,
                "uploaded_at": datetime.now(timezone.utc)
            }

            await self.user_photos.insert_one(photo_doc)
            return photo_id
        except Exception as e:
            print(f"Error saving user photo: {e}")
            raise e

    async def get_user_primary_photo(self, user_id: str) -> Optional[Dict]:
        #קבלת התמונה הראשית של משתמש
        photo = await self.user_photos.find_one({
            "user_id": user_id,
            "is_primary": True
        })
        if photo:
            photo.pop('_id', None)
        return photo

    async def get_user_photos(self, user_id: str) -> List[Dict]:
      #  קבלת כל התמונות של משתמש
        photos = await self.user_photos.find({"user_id": user_id}).to_list(None)
        for photo in photos:
            photo.pop('_id', None)
        return photos

    # ===========================
    # Event Photos Methods
    # ===========================

    async def save_event_photo(self, event_id: str, uploaded_by: str,
                               file_path: str, file_name: str, file_size: int,
                               mime_type: str) -> str:
        #שמירת תמונת אירוע
        try:
            photo_id = str(uuid.uuid4())

            photo_doc = {
                "photo_id": photo_id,
                "event_id": event_id,
                "uploaded_by": uploaded_by,
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "mime_type": mime_type,
                "uploaded_at": datetime.now(timezone.utc),
                "processed": False
            }

            await self.event_photos.insert_one(photo_doc)
            return photo_id
        except Exception as e:
            print(f"Error saving event photo: {e}")
            raise e

    async def mark_photo_as_processed(self, photo_id: str) -> bool:
        """סימון תמונה כמעובדת"""
        result = await self.event_photos.update_one(
            {"photo_id": photo_id},
            {"$set": {"processed": True}}
        )
        return result.modified_count > 0

    async def get_event_photos(self, event_id: str, processed_only: bool = False) -> List[Dict]:
        """קבלת תמונות אירוע"""
        query = {"event_id": event_id}
        if processed_only:
            query["processed"] = True

        photos = await self.event_photos.find(query).to_list(None)
        for photo in photos:
            photo.pop('_id', None)
        return photos

    async def get_photo_by_id(self, photo_id: str) -> Optional[Dict]:
        """קבלת תמונה לפי ID"""
        photo = await self.event_photos.find_one({"photo_id": photo_id})
        if photo:
            photo.pop('_id', None)
        return photo

    # ===========================
    # Reference Photos Methods
    # ===========================

    async def save_user_reference_photo(self, user_id: str, file_path: str,
                                        filename: str, face_encoding: List[float]) -> bool:
      # שמירת תמונת ייחוס עם וקטור פנים במסד
        try:
            # מחק תמונות ייחוס קודמות
            await self.user_photos.delete_many({
                "user_id": user_id,
                "is_reference": True
            })

            photo_doc = {
                "photo_id": str(uuid.uuid4()),
                "user_id": user_id,
                "file_path": file_path,
                "file_name": filename,
                "face_encoding": face_encoding,  # וקטור פנים במסד
                "is_reference": True,
                "uploaded_at": datetime.now(timezone.utc)
            }

            result = await self.user_photos.insert_one(photo_doc)
            print(f" Reference photo saved for user {user_id}")
            return result.inserted_id is not None
        except Exception as e:
            print(f" Error saving reference photo: {e}")
            return False
#קבלת תמונת ייחוס עם וקטור פנים
    async def get_user_reference_photo(self, user_id: str) -> Optional[Dict]:

        try:
            photo = await self.user_photos.find_one({
                "user_id": user_id,
                "is_reference": True
            })
            if photo:
                photo.pop('_id', None)
            return photo
        except Exception as e:
            print(f" Error getting reference photo: {e}")
            return None
      #קבלת וקטורי פנים של כל משתתפי האירוע
    async def get_event_participants_vectors(self, event_id: str) -> List[Dict]:
        try:
            # קבלת כל המשתתפים באירוע
            participants = await self.event_participants.find(
                {"event_id": event_id}
            ).to_list(None)
            user_ids = [p["user_id"] for p in participants]
            # קבלת תמונות הייחוס של כל המשתתפים
            user_vectors = await self.user_photos.find({
                "user_id": {"$in": user_ids},
                "is_reference": True
            }).to_list(None)
            for vector in user_vectors:
                vector.pop('_id', None)
            print(f" Found {len(user_vectors)} participant vectors for event {event_id}")
            return user_vectors
        except Exception as e:
            print(f" Error getting participant vectors: {e}")
            return []

    # ===========================
    # Face Detection Methods
    # ===========================
#        שמירת זיהוי פנים

    async def save_face_detection(self, event_photo_id: str, detected_user_id: str,
                                  confidence_score: float, face_coordinates: Dict[str, int]) -> str:
        try:
            detection_id = str(uuid.uuid4())

            detection_doc = {
                "detection_id": detection_id,
                "event_photo_id": event_photo_id,
                "detected_user_id": detected_user_id,
                "confidence_score": confidence_score,
                "face_coordinates": face_coordinates,
                "detected_at": datetime.now(timezone.utc),
                "matched_at": datetime.now(timezone.utc)
            }

            await self.face_detections.insert_one(detection_doc)
            return detection_id
        except Exception as e:
            print(f"Error saving face detection: {e}")
            raise e
#        קבלת כל הזיהויים של משתמש באירוע

    async def get_user_detections_in_event(self, user_id: str, event_id: str) -> List[Dict]:
        event_photos = await self.get_event_photos(event_id)
        photo_ids = [p["photo_id"] for p in event_photos]

        detections = await self.face_detections.find({
            "event_photo_id": {"$in": photo_ids},
            "detected_user_id": user_id
        }).to_list(None)

        for detection in detections:
            detection.pop('_id', None)
            photo = next((p for p in event_photos if p["photo_id"] == detection["event_photo_id"]), None)
            if photo:
                detection["photo_details"] = {
                    "file_name": photo["file_name"],
                    "file_path": photo["file_path"],
                    "uploaded_at": photo["uploaded_at"]
                }

        return detections
#        שמירת התאמת פנים

    async def save_face_match(self, user_id: str, event_id: str, photo_id: str,
                              similarity_score: float, face_index: int = 0) -> bool:
        try:
            match_doc = {
                "detection_id": str(uuid.uuid4()),
                "user_id": user_id,
                "event_id": event_id,
                "event_photo_id": photo_id,
                "detected_user_id": user_id,
                "confidence_score": similarity_score,
                "face_index": face_index,
                "matched_at": datetime.now(timezone.utc)
            }

            result = await self.face_detections.insert_one(match_doc)
            print(f" Face match saved: user {user_id}, photo {photo_id}, similarity {similarity_score:.3f}")
            return result.inserted_id is not None
        except Exception as e:
            print(f"Error saving face match: {e}")
            return False

    async def get_user_matches_in_event(self, user_id: str, event_id: str) -> List[Dict]:
        try:
            matches = await self.face_detections.find({
                "detected_user_id": user_id,
                "event_id": event_id
            }).to_list(None)

            for match in matches:
                match.pop('_id', None)
                photo = await self.get_photo_by_id(match["event_photo_id"])
                if photo:
                    match["photo_filename"] = photo.get("file_name")
                    match["photo_path"] = photo.get("file_path")
                    match["confidence"] = "High" if match["confidence_score"] >= 0.9 else "Medium"

            return matches
        except Exception as e:
            print(f" Error getting user matches: {e}")
            return []

    async def close_connection(self):
        self.client.close()


# יצירת אינסטנס גלובלי
database = Database()

# ייצוא לשימוש חיצוני
__all__ = ["Database", "database"]