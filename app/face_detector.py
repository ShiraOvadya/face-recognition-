# app/services/face_detector.py
import dlib
import cv2
import numpy as np
from typing import List, Tuple, Optional
import os


class FaceDetector:

    def __init__(self, model_path: Optional[str] = None):

        self.is_cnn = False

        if model_path and os.path.exists(model_path):
            try:
                self.detector = dlib.cnn_face_detection_model_v1(model_path)
                self.is_cnn = True
                print(f"מודל CNN נטען בהצלחה מ: {model_path}")
            except Exception as e:
                print(f"שגיאה בטעינת מודל CNN: {e}")
                self.detector = dlib.get_frontal_face_detector()
                print("משתמש במודל הבסיסי של dlib")
        else:
            self.detector = dlib.get_frontal_face_detector()
            print("משתמש במודל הבסיסי של dlib")

    def detect_faces(self, image: np.ndarray, upsample_num: int = 1) -> List[dlib.rectangle]:
        """
        זיהוי פנים בתמונה

        Args:
            image: תמונה ב-RGB או grayscale
            upsample_num: מספר פעמים להגדלת התמונה (רק למודל בסיסי)

        Returns:
            רשימת rectangles של הפנים שזוהו
        """
        # המרה ל-RGB אם צריך
        if len(image.shape) == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image.shape[2] == 3 else image
        else:
            rgb_image = image

        if self.is_cnn:
            # עבור CNN model
            detections = self.detector(rgb_image, 1)
            return [d.rect for d in detections]
        else:
            # עבור מודל בסיסי
            return self.detector(rgb_image, upsample_num)

    def draw_faces(self, image: np.ndarray, faces: List[dlib.rectangle],
                   color: Tuple[int, int, int] = (0, 255, 0),
                   thickness: int = 2) -> np.ndarray:
        """
        ציור מסגרות סביב הפנים שזוהו

        Args:
            image: התמונה המקורית
            faces: רשימת הפנים שזוהו
            color: צבע המסגרת (BGR)
            thickness: עובי המסגרת

        Returns:
            תמונה עם המסגרות מצוירות
        """
        result_image = image.copy()

        for i, rect in enumerate(faces):
            # ציור מסגרת
            cv2.rectangle(result_image,
                          (rect.left(), rect.top()),
                          (rect.right(), rect.bottom()),
                          color, thickness)

            # הוספת מספר הפנים
            cv2.putText(result_image, f'Face {i + 1}',
                        (rect.left(), rect.top() - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        return result_image

    def get_face_landmarks(self, image: np.ndarray, faces: List[dlib.rectangle],
                           predictor_path: Optional[str] = None) -> List[np.ndarray]:
        """
        קבלת נקודות ציון של הפנים

        Args:
            image: התמונה המקורית
            faces: רשימת הפנים שזוהו
            predictor_path: נתיב למודל הנקודות ציון

        Returns:
            רשימת נקודות הציון לכל פנים
        """
        if not predictor_path or not os.path.exists(predictor_path):
            print("מודל נקודות הציון לא נמצא")
            return []

        try:
            predictor = dlib.shape_predictor(predictor_path)
            landmarks_list = []

            for rect in faces:
                landmarks = predictor(image, rect)
                points = np.array([(landmarks.part(i).x, landmarks.part(i).y)
                                   for i in range(landmarks.num_parts)])
                landmarks_list.append(points)

            return landmarks_list
        except Exception as e:
            print(f"שגיאה בקבלת נקודות הציון: {e}")
            return []

    def crop_faces(self, image: np.ndarray, faces: List[dlib.rectangle],
                   padding: int = 20) -> List[np.ndarray]:
        """
        חיתוך הפנים מהתמונה

        Args:
            image: התמונה המקורית
            faces: רשימת הפנים שזוהו
            padding: ריווח נוסף סביב הפנים

        Returns:
            רשימת תמונות פנים חתוכות
        """
        cropped_faces = []
        h, w = image.shape[:2]

        for rect in faces:
            # חישוב הגבולות עם ריווח
            left = max(0, rect.left() - padding)
            top = max(0, rect.top() - padding)
            right = min(w, rect.right() + padding)
            bottom = min(h, rect.bottom() + padding)

            # חיתוך הפנים
            face = image[top:bottom, left:right]
            cropped_faces.append(face)

        return cropped_faces

    def get_face_count(self, image: np.ndarray) -> int:
        """
        קבלת מספר הפנים בתמונה

        Args:
            image: התמונה לבדיקה

        Returns:
            מספר הפנים שזוהו
        """
        faces = self.detect_faces(image)
        return len(faces)

    def is_face_detected(self, image: np.ndarray) -> bool:
        """
        בדיקה האם יש פנים בתמונה

        Args:
            image: התמונה לבדיקה

        Returns:
            True אם זוהו פנים, False אחרת
        """
        return self.get_face_count(image) > 0