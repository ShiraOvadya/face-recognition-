import dlib
import cv2
import numpy as np
from typing import List, Tuple
class FaceLandmarkDetector:
    # #איתחול קובץ לזיהוי 68 נקודות
    def __init__(self, predictor_path: str):
        try:
            self.predictor = dlib.shape_predictor(predictor_path)
            print(f"Face point model successfully loaded from: {predictor_path}")
        except Exception as e:
            raise Exception(f"Error loading face point model: {e}")

    def detect_landmarks(self, rgb_image: np.ndarray, faces: List[dlib.rectangle],
                         draw_points: bool = True, draw_numbers: bool = False,
                         point_color: Tuple[int, int, int] = (0, 0, 255),
                         text_color: Tuple[int, int, int] = (255, 0, 0)) -> Tuple[
        np.ndarray, List[List[Tuple[int, int]]]]:
        all_landmarks = []
        result_image = rgb_image.copy()

        for face_idx, rect in enumerate(faces):
            # זיהוי 68 נקודות עבור הפנים הנוכחיות
            shape = self.predictor(rgb_image, rect)
            landmarks = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
            all_landmarks.append(landmarks)

            if draw_points:
                # ציור הנקודות
                for idx, (x, y) in enumerate(landmarks):
                    cv2.circle(result_image, (x, y), 2, point_color, -1)

                    if draw_numbers:
                        cv2.putText(result_image, str(idx), (x + 2, y - 2),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, text_color, 1)

                # ציור קווי חיבור בין נקודות (אופציונלי)
                self.draw_landmark_connections(result_image, landmarks)

        return result_image, all_landmarks
#ציור הפנים
    def draw_landmark_connections(self, image: np.ndarray, landmarks: List[Tuple[int, int]]):
        # מתאר הפנים (0-16)
        jaw_points = landmarks[0:17]
        for i in range(len(jaw_points) - 1):
            cv2.line(image, jaw_points[i], jaw_points[i + 1], (255, 255, 0), 1)

        # גבה ימין (17-21)
        right_brow = landmarks[17:22]
        for i in range(len(right_brow) - 1):
            cv2.line(image, right_brow[i], right_brow[i + 1], (255, 255, 0), 1)

        # גבה שמאל (22-26)
        left_brow = landmarks[22:27]
        for i in range(len(left_brow) - 1):
            cv2.line(image, left_brow[i], left_brow[i + 1], (255, 255, 0), 1)

        # אף (27-35)
        nose_bridge = landmarks[27:31]
        for i in range(len(nose_bridge) - 1):
            cv2.line(image, nose_bridge[i], nose_bridge[i + 1], (255, 255, 0), 1)

        nose_tip = landmarks[31:36]
        for i in range(len(nose_tip) - 1):
            cv2.line(image, nose_tip[i], nose_tip[i + 1], (255, 255, 0), 1)
        cv2.line(image, nose_tip[-1], nose_tip[0], (255, 255, 0), 1)  # סגירת המעגל

        # עין ימין (36-41)
        right_eye = landmarks[36:42]
        for i in range(len(right_eye) - 1):
            cv2.line(image, right_eye[i], right_eye[i + 1], (255, 255, 0), 1)
        cv2.line(image, right_eye[-1], right_eye[0], (255, 255, 0), 1)  # סגירת העין

        # עין שמאל (42-47)
        left_eye = landmarks[42:48]
        for i in range(len(left_eye) - 1):
            cv2.line(image, left_eye[i], left_eye[i + 1], (255, 255, 0), 1)
        cv2.line(image, left_eye[-1], left_eye[0], (255, 255, 0), 1)  # סגירת העין

        # פה (48-67)
        outer_lip = landmarks[48:60]
        for i in range(len(outer_lip) - 1):
            cv2.line(image, outer_lip[i], outer_lip[i + 1], (255, 255, 0), 1)
        # סגירת השפה החיצונית
        cv2.line(image, outer_lip[-1], outer_lip[0], (255, 255, 0), 1)

        inner_lip = landmarks[60:68]
        for i in range(len(inner_lip) - 1):
            cv2.line(image, inner_lip[i], inner_lip[i + 1], (255, 255, 0), 1)
            # סגירת השפה הפנימית
        cv2.line(image, inner_lip[-1], inner_lip[0], (255, 255, 0), 1)
