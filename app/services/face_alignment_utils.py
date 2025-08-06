import cv2
import numpy as np
from typing import Optional, List, Tuple
from app.config import FaceAlignmentConfig as AlignConfig

def quick_align_face(image: np.ndarray, landmarks: List[Tuple[int, int]]) -> np.ndarray:
    try:
        landmarks_np = np.array(landmarks, dtype=np.float32)
        # חישוב מרכז העיננים ע"י חישוב ממוצע נקודות בכל העין
        left_eye = landmarks_np[AlignConfig.LEFT_EYE_START:AlignConfig.LEFT_EYE_END].mean(axis=0)
        right_eye = landmarks_np[AlignConfig.RIGHT_EYE_START:AlignConfig.RIGHT_EYE_END].mean(axis=0)
        # חישוב מרחק בין שני העניים ובדיקה האם התמונה תקינה
        eye_distance = np.linalg.norm(right_eye - left_eye)
        if eye_distance < AlignConfig.MIN_EYE_DISTANCE:  # עיניים קרובות מדי
            return image
        #ע"י חישוב זווית בן העניים  בדיקה האם הפנים נוטות לצד
        angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1],
                                    right_eye[0] - left_eye[0]))

        if abs(angle) < AlignConfig.MIN_ANGLE_TO_ALIGN:
            return image
        # יישור פשוט
        eyes_center = ((left_eye + right_eye) / 2.0).astype(int)
        # M = cv2.getRotationMatrix2D(tuple(eyes_center), angle, 1.0)
        # h, w = image.shape[:2]
        # aligned = cv2.warpAffine(image, M, (w, h))

        h, w = image.shape[:2]
        center_x, center_y = eyes_center[0], eyes_center[1]
        angle_rad = np.radians(-angle)

        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        # יצירת רשת קואורדינטות
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        #מעבירים את כל הקואורדינטות כך שמרכז הענים יהיה (0,0)
        x_centered = x_coords - center_x
        y_centered = y_coords - center_y
        #סיבוב הפיקסלים סביב מרכז העין
        x_original = x_centered * cos_a + y_centered * sin_a + center_x
        y_original = -x_centered * sin_a + y_centered * cos_a + center_y
        # עיגול לאינדקסים שלמים

        x_floor = np.floor(x_original).astype(int)
        y_floor = np.floor(y_original).astype(int)
        x_ceil = x_floor + 1
        y_ceil = y_floor + 1
        #חישוב המרחק היחסי מהפיקסלים שסביבה
        dx = x_original - x_floor
        dy = y_original - y_floor

        # יצירת מסכה בוליאנית  בגודל התמונה
        valid_mask = (
                (x_floor >= 0) & (x_ceil < w) &
                (y_floor >= 0) & (y_ceil < h)
        )

        # יצירת תמונה מיושרת
        aligned = np.zeros_like(image)

        # bilinear interpolation
        if len(image.shape) == 3:  # בןדקת האם התמונה ציבעונית מכילה שלוש ערוצי צבע
            for c in range(image.shape[2]):
                interpolated = (
                        image[y_floor, x_floor, c] * (1 - dx) * (1 - dy) +
                        image[y_floor, x_ceil, c] * dx * (1 - dy) +
                        image[y_ceil, x_floor, c] * (1 - dx) * dy +
                        image[y_ceil, x_ceil, c] * dx * dy
                )
                aligned[:, :, c][valid_mask] = interpolated[valid_mask]
        else:  # grayscale
            interpolated = (
                    image[y_floor, x_floor] * (1 - dx) * (1 - dy) +
                    image[y_floor, x_ceil] * dx * (1 - dy) +
                    image[y_ceil, x_floor] * (1 - dx) * dy +
                    image[y_ceil, x_ceil] * dx * dy
            )
            aligned[valid_mask] = interpolated[valid_mask]

        return (aligned.astype(image.dtype))
    except:
        return image