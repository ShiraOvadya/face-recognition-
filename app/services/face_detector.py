import dlib
import cv2
import numpy as np
from typing import List, Tuple, Union

class FaceDetector:
    def __init__(self, model_path: str):
        try:
            self.detector = dlib.cnn_face_detection_model_v1(model_path)
            print(f"CNN face recognition model successfully loaded from:: {model_path}")
            self.is_cnn = True
        except Exception as e:
            print(f"Error loading model CNN: {e}")
            self.detector = dlib.get_frontal_face_detector()
            self.is_cnn = False
            print("Uses the basic model of dlib")
    def detect_faces(self, rgb_image: np.ndarray, upsample_num: int = 1) -> List[dlib.rectangle]:
        if self.is_cnn:
            # עבור CNN model - אין תמיכה ב-upsample_num
            detections = self.detector(rgb_image, 1)
            return [d.rect for d in detections]
        else:
            # עבור מודל HOG
            return self.detector(rgb_image, upsample_num)
    def draw_faces(self, image: np.ndarray, faces: List[dlib.rectangle],
                   color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
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
    def get_face_info(self, faces: List[dlib.rectangle]) -> List[dict]:
        face_info = []
        for i, rect in enumerate(faces):
            info = {
                "face_id": i + 1,
                "left": rect.left(),
                "top": rect.top(),
                "right": rect.right(),
                "bottom": rect.bottom(),
                "width": rect.width(),
                "height": rect.height(),
                "center_x": rect.left() + rect.width() // 2,
                "center_y": rect.top() + rect.height() // 2
            }
            face_info.append(info)
        return face_info