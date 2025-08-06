import os
from pathlib import Path
from typing import Optional, List
import uuid
from datetime import datetime


class FileManager:
    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_dir = Path(base_upload_dir)
        self.user_photos_dir = self.base_dir / "user_photos"
        self.event_photos_dir = self.base_dir / "event_photos"

        # יצירת תיקיות בסיס
        self._ensure_directories()

    def _ensure_directories(self):
        self.base_dir.mkdir(exist_ok=True)
        self.user_photos_dir.mkdir(exist_ok=True)
        self.event_photos_dir.mkdir(exist_ok=True)
        print(f" File directories created: {self.base_dir}")

    def save_user_photo(self, user_email: str, file_content: bytes,
                        filename: str, is_reference: bool = False) -> tuple[str, str]:

        try:
            # יצירת תיקיית משתמש על פי המייל (החלפת @ ב- _)
            safe_email = user_email.replace("@", "_").replace(".", "_")
            user_dir = self.user_photos_dir / safe_email
            user_dir.mkdir(exist_ok=True)

            # יצירת שם קובץ ייחודי
            if is_reference:
                unique_filename = f"reference_{filename}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_ext = Path(filename).suffix
                unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"

            file_path = user_dir / unique_filename

            # שמירת הקובץ
            with open(file_path, 'wb') as f:
                f.write(file_content)

            print(f" User photo saved: {file_path}")
            return str(file_path), unique_filename

        except Exception as e:
            print(f" Error saving user photo: {e}")
            raise e

    def save_event_photo(self, event_id: str, file_content: bytes,
                         filename: str, uploaded_by: str) -> tuple[str, str]:
        try:
            # יצירת תיקיית אירוע
            event_dir = self.event_photos_dir / event_id
            event_dir.mkdir(exist_ok=True)

            # יצירת שם קובץ ייחודי
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = Path(filename).suffix
            unique_filename = f"{timestamp}_{uploaded_by[:8]}_{uuid.uuid4().hex[:8]}{file_ext}"

            file_path = event_dir / unique_filename

            # שמירת הקובץ
            with open(file_path, 'wb') as f:
                f.write(file_content)

            print(f"Event photo saved: {file_path}")
            return str(file_path), unique_filename

        except Exception as e:
            print(f" Error saving event photo: {e}")
            raise e

    def read_image_file(self, file_path: str) -> Optional[bytes]:
        try:
            if not os.path.exists(file_path):
                print(f" Image file not found: {file_path}")
                return None

            with open(file_path, 'rb') as f:
                content = f.read()

            return content

        except Exception as e:
            print(f"Error reading image file: {e}")
            return None

    def delete_user_photo(self, file_path: str) -> bool:
      #  מחיקת תמונת משתמש
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f" Photo deleted: {file_path}")
                return True
            else:
                print(f" Photo file not found: {file_path}")
                return False

        except Exception as e:
            print(f" Error deleting photo: {e}")
            return False

    def get_file_size(self, file_path: str) -> int:
        #קבלת גודל קובץ
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return 0
        except:
            return 0

    def list_user_photos(self, user_email: str) -> List[str]:
       #רשימת תמונות משתמש
        try:
            safe_email = user_email.replace("@", "_").replace(".", "_")
            user_dir = self.user_photos_dir / safe_email
            if not user_dir.exists():
                return []

            photo_files = []
            for ext in ["*.jpg", "*.jpeg", "*.png"]:
                photo_files.extend([str(f) for f in user_dir.glob(ext)])

            return photo_files

        except Exception as e:
            print(f" Error listing user photos: {e}")
            return []


# יצירת אינסטנס גלובלי
file_manager = FileManager()

# ייצוא לשימוש חיצוני
__all__ = ["FileManager", "file_manager"]