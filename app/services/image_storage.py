import numpy as np
from typing import Optional, List, Dict
from app.database import Database
from app.services.file_manager import file_manager


class ImageStorageService:
    def __init__(self, database: Database):
        self.db = database
        self.file_manager = file_manager
        print(" ImageStorageService initialized with vectors in database")

    async def save_user_reference_image(self, user_id: str, user_email: str, image_data: bytes,
                                        filename: str, feature_vector: np.ndarray) -> bool:
        try:
            # שמירת התמונה במערכת הקבצים על פי המייל
            file_path, saved_filename = self.file_manager.save_user_photo(
                user_email=user_email,
                file_content=image_data,
                filename=filename,
                is_reference=True
            )

            # שמירת הנתיב והוקטור במסד הנתונים
            success = await self.db.save_user_reference_photo(
                user_id=user_id,
                file_path=file_path,
                filename=saved_filename,
                face_encoding=feature_vector.tolist()  # המרה לרשימה לשמירה במסד
            )

            if success:
                print(f" Reference image saved for user {user_email}")
                return True
            else:
                # אם נכשל במסד נתונים, מחק את הקובץ
                self.file_manager.delete_user_photo(file_path)
                return False

        except Exception as e:
            print(f" Error saving reference image: {e}")
            return False

    async def get_user_reference_image(self, user_id: str) -> Optional[Dict]:
        try:
            # קבלת הנתונים מהמסד
            photo_data = await self.db.get_user_reference_photo(user_id)
            if not photo_data:
                return None

            # החזרת הנתונים
            return {
                "user_id": user_id,
                "file_path": photo_data["file_path"],
                "face_encoding": photo_data["face_encoding"],  # וקטור פנים מהמסד
                "filename": photo_data["file_name"],
                "uploaded_at": photo_data["uploaded_at"]
            }

        except Exception as e:
            print(f" Error getting reference image: {e}")
            return None

    async def save_event_photo(self, event_id: str, uploaded_by: str,
                               image_data: bytes, filename: str) -> Optional[str]:
        try:
            # שמירת התמונה במערכת הקבצים
            file_path, saved_filename = self.file_manager.save_event_photo(
                event_id=event_id,
                file_content=image_data,
                filename=filename,
                uploaded_by=uploaded_by
            )

            # שמירת הנתיב במסד הנתונים
            photo_id = await self.db.save_event_photo(
                event_id=event_id,
                uploaded_by=uploaded_by,
                file_path=file_path,
                file_name=saved_filename,
                file_size=self.file_manager.get_file_size(file_path),
                mime_type="image/jpeg"
            )

            print(f" Event photo saved: {photo_id}")
            return photo_id

        except Exception as e:
            print(f" Error saving event photo: {e}")
            return None

    async def get_event_photo_by_path(self, file_path: str) -> Optional[bytes]:
        try:
            return self.file_manager.read_image_file(file_path)
        except Exception as e:
            print(f" Error reading event photo: {e}")
            return None