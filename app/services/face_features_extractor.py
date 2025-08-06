

import cv2
import numpy as np
import dlib
from typing import Optional, List
import os
import gc

from app.services.face_detector import FaceDetector


class FaceLandmarkDetector:
    def __init__(self, predictor_path: str):
        try:
            self.predictor = dlib.shape_predictor(predictor_path)
            print(f"Face point model successfully loaded from: {predictor_path}")
        except Exception as e:
            raise Exception(f"Error loading face point model: {e}")


class FaceFeatureExtractor:
    def __init__(self):
        self._load_models()
        self._check_readiness()

    def _load_models(self):
        try:
            # נתיבי המודלים
            cnn_model_path = "models/mmod_human_face_detector.dat"
            landmarks_model_path = "models/shape_predictor_68_face_landmarks.dat"
            recognition_model_path = "models/dlib_face_recognition_resnet_model_v1.dat"

            # אתחול גלאי פנים
            try:
                if os.path.exists(cnn_model_path):
                    self.detector = FaceDetector(cnn_model_path)
                    print("FaceDetector (CNN) initialized successfully")
                else:
                    print(f" Warning: CNN model not found, using basic detector")
                    self.face_detector_basic = dlib.get_frontal_face_detector()
                    self.detector = None
            except Exception as e:
                print(f"Warning: Using basic face detector: {e}")
                self.face_detector_basic = dlib.get_frontal_face_detector()
                self.detector = None

            # אתחול זיהוי נקודות פנים
            try:
                if os.path.exists(landmarks_model_path):
                    self.landmark_detector = FaceLandmarkDetector(landmarks_model_path)
                    print("FaceLandmarkDetector initialized successfully")
                else:
                    print(f" Warning: Landmarks model not found: {landmarks_model_path}")
                    self.landmark_detector = None
            except Exception as e:
                print(f"Warning: Could not load landmarks detector: {e}")
                self.landmark_detector = None

            # אתחול מודל זיהוי פנים
            try:
                if os.path.exists(recognition_model_path):
                    self.face_rec_model = dlib.face_recognition_model_v1(recognition_model_path)
                    print("Face recognition model loaded successfully")
                else:
                    print(f" Warning: Model not found at path: {recognition_model_path}")
                    self.face_rec_model = None
            except Exception as e:
                print(f"Error loading recognition model: {e}")
                self.face_rec_model = None

        except Exception as e:
            print(f" Error initializing FaceFeatureExtractor: {e}")
            # אתחול ערכי ברירת מחדל במקרה של שגיאה
            self.detector = None
            self.landmark_detector = None
            self.face_rec_model = None

    def _check_readiness(self):
        self.is_ready = (
                self.landmark_detector is not None and
                self.face_rec_model is not None and
                (self.detector is not None or hasattr(self, 'face_detector_basic'))
        )

        if self.is_ready:
            print(" FaceFeatureExtractor is ready!")
        else:
            print("FaceFeatureExtractor not fully ready - missing models")
            print("Required files:")
            print("   - models/shape_predictor_68_face_landmarks.dat")
            print("   - models/dlib_face_recognition_resnet_model_v1.dat")
            print("   - models/mmod_human_face_detector.dat (optional)")

    def _prepare_image_for_processing(self, image: np.ndarray, max_size: int = 1024) -> np.ndarray:
        try:
            # הקטנת התמונה אם צריך
            height, width = image.shape[:2]
            if width > max_size or height > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                print(f"Resized image from {width}x{height} to {new_width}x{new_height}")

            # המרה ל-RGB
            if len(image.shape) == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image

            return rgb_image

        except Exception as e:
            print(f"Error preparing image: {e}")
            return image

    def _detect_faces_internal(self, rgb_image: np.ndarray) -> List:
        try:
            if self.detector:
                # שימוש ב-FaceDetector
                return self.detector.detect_faces(rgb_image)
            elif hasattr(self, 'face_detector_basic'):
                # fallback לגלאי בסיסי
                return self.face_detector_basic(rgb_image)
            else:
                return []
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []

    def extract_feature_vector(self, image: np.ndarray) -> Optional[np.ndarray]:
       # חילוץ וקטור מאפיינים עם יישור נכון לתמונת ייחוס

        if not self.is_ready:
            print("FaceFeatureExtractor not ready - missing models")
            return None

        try:
            # הכנת התמונה
            rgb_image = self._prepare_image_for_processing(image)

            # זיהוי פנים
            face_boxes = self._detect_faces_internal(rgb_image)

            if not face_boxes:
                print("No faces detected in image")
                return None

            if len(face_boxes) > 1:
                print(f"Multiple faces detected ({len(face_boxes)}), using the largest one")

                # בחירת הפנים הגדולות ביותר (יותר מדויק מהראשונות)
                face_areas = [(face_box.width() * face_box.height(), i, face_box)
                              for i, face_box in enumerate(face_boxes)]
                face_areas.sort(reverse=True)  # מהגדול לקטן
                _, face_index, face_box = face_areas[0]
                print(f" Selected face {face_index + 1} (largest: {face_box.width()}x{face_box.height()})")
            else:
                face_box = face_boxes[0]

            # זיהוי נקודות ציון
            shape = self.landmark_detector.predictor(rgb_image, face_box)
            landmarks = [(shape.part(i).x, shape.part(i).y) for i in range(shape.num_parts)]

            # יישור פנים באמצעות הפונקציה שלך
            try:
                from app.services.face_alignment_utils import quick_align_face
                aligned_image = quick_align_face(rgb_image, landmarks)

                # זיהוי פנים מחדש בתמונה המיושרת
                aligned_face_boxes = self._detect_faces_internal(aligned_image)

                if aligned_face_boxes:
                    # מציאת הפנים הקרובות ביותר למיקום המקורי
                    original_center = (face_box.center().x, face_box.center().y)
                    best_match = None
                    min_distance = float('inf')

                    for aligned_face in aligned_face_boxes:
                        aligned_center = (aligned_face.center().x, aligned_face.center().y)
                        distance = np.sqrt((original_center[0] - aligned_center[0]) ** 2 +
                                           (original_center[1] - aligned_center[1]) ** 2)
                        if distance < min_distance:
                            min_distance = distance
                            best_match = aligned_face

                    if best_match:
                        shape_aligned = self.landmark_detector.predictor(aligned_image, best_match)
                        try:
                            face_descriptor = self.face_rec_model.compute_face_descriptor(aligned_image, shape_aligned, 1)
                        except:
                            face_descriptor = self.face_rec_model.compute_face_descriptor(aligned_image, 1)
                        print("Used aligned face (reference photo)")
                    else:
                        try:
                            face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, shape, 1)
                        except:
                            face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, 1)
                        print("No matching face found in aligned image, used original")
                else:
                    try:
                        face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, shape, 1)
                    except:
                        face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, 1)
                    print("Face detection failed in aligned image, used original")

            except Exception as align_error:
                try:
                    face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, shape, 1)
                except:
                    face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, 1)
                print(f" Face alignment failed: {align_error}, used original")

            feature_vector = np.array(face_descriptor, dtype=np.float32)
            print(f"Feature vector extracted: {len(feature_vector)} dimensions")
            return feature_vector

        except Exception as e:
            print(f" Error extracting feature vector: {e}")
            print(f"Detailed error: {type(e).__name__}: {str(e)}")
            return None
        finally:
            try:
                del rgb_image, face_boxes
                gc.collect()
            except:
                pass

    def extract_multiple_faces(self, image: np.ndarray) -> List[np.ndarray]:
        #חילוץ וקטורי מאפיינים ממספר פנים בתמונה עם יישור נכון
        if not self.is_ready:
            print("FaceFeatureExtractor not ready - missing models")
            return []

        try:
            # הכנת התמונה
            rgb_image = self._prepare_image_for_processing(image)

            # זיהוי פנים בתמונה המקורית
            face_boxes = self._detect_faces_internal(rgb_image)

            if not face_boxes:
                print("No faces detected in image")
                return []

            feature_vectors = []

            # עיבוד כל פנים בנפרד
            for i, face_box in enumerate(face_boxes):
                try:
                    print(f" Processing face {i + 1}/{len(face_boxes)}")

                    # זיהוי נקודות ציון על הפנים הספציפיות האלה
                    shape = self.landmark_detector.predictor(rgb_image, face_box)
                    landmarks = [(shape.part(j).x, shape.part(j).y) for j in range(shape.num_parts)]

                    try:
                        # חיתוך אזור הפנים עם מרווח
                        margin = 50  # מרווח בפיקסלים
                        face_left = max(0, face_box.left() - margin)
                        face_top = max(0, face_box.top() - margin)
                        face_right = min(rgb_image.shape[1], face_box.right() + margin)
                        face_bottom = min(rgb_image.shape[0], face_box.bottom() + margin)

                        # חיתוך הפנים
                        face_region = rgb_image[face_top:face_bottom, face_left:face_right]

                        # התאמת נקודות הציון לאזור החתוך
                        adjusted_landmarks = [(x - face_left, y - face_top) for x, y in landmarks]

                        # יישור הפנים החתוכות באמצעות הפונקציה שלך
                        from app.services.face_alignment_utils import quick_align_face
                        aligned_face_region = quick_align_face(face_region, adjusted_landmarks)

                        # זיהוי פנים באזור המיושר
                        aligned_faces = self._detect_faces_internal(aligned_face_region)

                        if aligned_faces:
                            # זיהוי נקודות ציון באזור המיושר
                            aligned_shape = self.landmark_detector.predictor(aligned_face_region, aligned_faces[0])

                            # חילוץ וקטור מהפנים המיושרות
                            try:
                                face_descriptor = self.face_rec_model.compute_face_descriptor(aligned_face_region, aligned_shape, 1)
                            except:
                                face_descriptor = self.face_rec_model.compute_face_descriptor(aligned_face_region, 1)
                            print(f"Face {i + 1}: aligned and extracted")
                        else:
                            try:
                                face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, shape, 1)
                            except:
                                face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, 1)
                            print(f" Face {i + 1}: alignment detection failed, used original")

                    except Exception as align_error:
                        try:
                            face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, shape, 1)
                        except:
                            face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, 1)
                        print(f"Face {i + 1}: alignment failed ({str(align_error)}), used original")

                    # המרה לוקטור
                    feature_vector = np.array(face_descriptor, dtype=np.float32)
                    feature_vectors.append(feature_vector)

                    print(f"Face {i + 1}: vector size {len(feature_vector)}")

                except Exception as e:
                    print(f" Error processing face {i + 1}: {e}")
                    continue

            print(f" Successfully extracted {len(feature_vectors)} face vectors with proper alignment")
            return feature_vectors

        except Exception as e:
            print(f" Error extracting multiple faces: {e}")
            return []
        finally:
            try:
                del rgb_image, face_boxes
                gc.collect()
            except:
                pass

    def process_image(self, image: np.ndarray, draw_faces: bool = True, draw_landmarks: bool = True):
        if not self.is_ready:
            print(" Required models not loaded")
            return image, [], [], []

        try:
            # הכנת התמונה
            rgb_image = self._prepare_image_for_processing(image)

            # זיהוי פנים
            face_boxes = self._detect_faces_internal(rgb_image)

            landmarks_list = []
            feature_vectors = []
            result_image = image.copy()

            for i, face_box in enumerate(face_boxes):
                try:
                    # זיהוי נקודות ציון
                    shape = self.landmark_detector.predictor(rgb_image, face_box)
                    landmarks = [(shape.part(j).x, shape.part(j).y) for j in range(shape.num_parts)]
                    landmarks_list.append(landmarks)

                    # חילוץ וקטור מאפיינים
                    try:
                        # חיתוך ויישור כמו ב-extract_multiple_faces
                        margin = 50
                        face_left = max(0, face_box.left() - margin)
                        face_top = max(0, face_box.top() - margin)
                        face_right = min(rgb_image.shape[1], face_box.right() + margin)
                        face_bottom = min(rgb_image.shape[0], face_box.bottom() + margin)

                        face_region = rgb_image[face_top:face_bottom, face_left:face_right]
                        adjusted_landmarks = [(x - face_left, y - face_top) for x, y in landmarks]

                        from app.services.face_alignment_utils import quick_align_face
                        aligned_face_region = quick_align_face(face_region, adjusted_landmarks)

                        aligned_faces = self._detect_faces_internal(aligned_face_region)
                        if aligned_faces:
                            aligned_shape = self.landmark_detector.predictor(aligned_face_region, aligned_faces[0])
                            try:
                                face_descriptor = self.face_rec_model.compute_face_descriptor(aligned_face_region, aligned_shape, 1)
                            except:
                                face_descriptor = self.face_rec_model.compute_face_descriptor(aligned_face_region, 1)
                        else:
                            try:
                                face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, shape, 1)
                            except:
                                face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, 1)
                    except:
                        try:
                            face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, shape, 1)
                        except:
                            face_descriptor = self.face_rec_model.compute_face_descriptor(rgb_image, 1)

                    feature_vectors.append(np.array(face_descriptor, dtype=np.float32))

                    # ציור מסגרות (אם יש FaceDetector)
                    if draw_faces and self.detector:
                        result_image = self.detector.draw_faces(result_image, [face_box])

                    # ציור נקודות
                    if draw_landmarks:
                        for (x, y) in landmarks:
                            cv2.circle(result_image, (x, y), 1, (255, 0, 0), -1)

                except Exception as e:
                    print(f" Error processing face {i + 1}: {e}")
                    continue

            return result_image, face_boxes, landmarks_list, feature_vectors

        except Exception as e:
            print(f"Error processing image: {e}")
            return image, [], [], []

    def detect_faces_count(self, image: np.ndarray) -> int:
        try:
            # הכנת התמונה
            rgb_image = self._prepare_image_for_processing(image)

            # זיהוי פנים
            faces = self._detect_faces_internal(rgb_image)

            count = len(faces)
            print(f"Detected {count} faces in image")
            return count

        except Exception as e:
            print(f"Error counting faces: {e}")
            return 0


# יצירת אינסטנס גלובלי
face_extractor = FaceFeatureExtractor()

# ייצוא לשימוש חיצוני
__all__ = ["FaceFeatureExtractor", "face_extractor", "FaceLandmarkDetector"]

# import cv2
# import numpy as np
# import dlib
# from typing import Optional, List
# import os
# import gc
#
# from app.services.face_detector import FaceDetector
#
#
# class FaceLandmarkDetector:
#     def __init__(self, predictor_path: str):
#         try:
#             self.predictor = dlib.shape_predictor(predictor_path)
#             print(f"Face point model successfully loaded from: {predictor_path}")
#         except Exception as e:
#             raise Exception(f"Error loading face point model: {e}")
#
#
# class FaceFeatureExtractor:
#     def __init__(self):
#         self._load_models()
#         self._check_readiness()
#
#     def _load_models(self):
#         try:
#             # נתיבי המודלים
#             cnn_model_path = "models/mmod_human_face_detector.dat"
#             landmarks_model_path = "models/shape_predictor_68_face_landmarks.dat"
#             recognition_model_path = "models/dlib_face_recognition_resnet_model_v1.dat"
#
#             # אתחול גלאי פנים
#             try:
#                 if os.path.exists(cnn_model_path):
#                     self.detector = FaceDetector(cnn_model_path)
#                     print("FaceDetector (CNN) initialized successfully")
#                 else:
#                     print(f" Warning: CNN model not found, using basic detector")
#                     self.face_detector_basic = dlib.get_frontal_face_detector()
#                     self.detector = None
#             except Exception as e:
#                 print(f"Warning: Using basic face detector: {e}")
#                 self.face_detector_basic = dlib.get_frontal_face_detector()
#                 self.detector = None
#
#             # אתחול זיהוי נקודות פנים
#             try:
#                 if os.path.exists(landmarks_model_path):
#                     self.landmark_detector = FaceLandmarkDetector(landmarks_model_path)
#                     print("FaceLandmarkDetector initialized successfully")
#                 else:
#                     print(f" Warning: Landmarks model not found: {landmarks_model_path}")
#                     self.landmark_detector = None
#             except Exception as e:
#                 print(f"Warning: Could not load landmarks detector: {e}")
#                 self.landmark_detector = None
#
#             # אתחול מודל זיהוי פנים
#             try:
#                 if os.path.exists(recognition_model_path):
#                     self.face_rec_model = dlib.face_recognition_model_v1(recognition_model_path)
#                     print("Face recognition model loaded successfully")
#                 else:
#                     print(f" Warning: Model not found at path: {recognition_model_path}")
#                     self.face_rec_model = None
#             except Exception as e:
#                 print(f"Error loading recognition model: {e}")
#                 self.face_rec_model = None
#
#         except Exception as e:
#             print(f" Error initializing FaceFeatureExtractor: {e}")
#             # אתחול ערכי ברירת מחדל במקרה של שגיאה
#             self.detector = None
#             self.landmark_detector = None
#             self.face_rec_model = None
#
#     def _check_readiness(self):
#         self.is_ready = (
#                 self.landmark_detector is not None and
#                 self.face_rec_model is not None and
#                 (self.detector is not None or hasattr(self, 'face_detector_basic'))
#         )
#
#         if self.is_ready:
#             print(" FaceFeatureExtractor is ready!")
#         else:
#             print("FaceFeatureExtractor not fully ready - missing models")
#             print("Required files:")
#             print("   - models/shape_predictor_68_face_landmarks.dat")
#             print("   - models/dlib_face_recognition_resnet_model_v1.dat")
#             print("   - models/mmod_human_face_detector.dat (optional)")
#
#     def _prepare_image_for_processing(self, image: np.ndarray, max_size: int = 1024) -> np.ndarray:
#         try:
#             # הקטנת התמונה אם צריך
#             height, width = image.shape[:2]
#             if width > max_size or height > max_size:
#                 scale = max_size / max(width, height)
#                 new_width = int(width * scale)
#                 new_height = int(height * scale)
#                 image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
#                 print(f"Resized image from {width}x{height} to {new_width}x{new_height}")
#
#             # המרה ל-RGB
#             if len(image.shape) == 3:
#                 rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#             else:
#                 rgb_image = image
#
#             return rgb_image
#
#         except Exception as e:
#             print(f"Error preparing image: {e}")
#             return image
#
#     def _detect_faces_internal(self, rgb_image: np.ndarray) -> List:
#         try:
#             if self.detector:
#                 # שימוש ב-FaceDetector שלך
#                 return self.detector.detect_faces(rgb_image)
#             elif hasattr(self, 'face_detector_basic'):
#                 # fallback לגלאי בסיסי
#                 return self.face_detector_basic(rgb_image)
#             else:
#                 return []
#         except Exception as e:
#             print(f"Error detecting faces: {e}")
#             return []
#
#     def _compute_face_descriptor_robust(self, image: np.ndarray, shape=None, num_jitters: int = 0,
#                                         padding: float = 0.25) -> np.ndarray:
#         """
#         Robust wrapper for compute_face_descriptor that handles all dlib versions properly
#         """
#         # ווידא שהתמונה בפורמט הנכון
#         if image.dtype != np.uint8:
#             image = image.astype(np.uint8)
#
#         # וודא שהתמונה רציפה בזיכרון (C-contiguous)
#         if not image.flags['C_CONTIGUOUS']:
#             image = np.ascontiguousarray(image)
#
#         # וודא שהתמונה תלת-ממדית ב-RGB
#         if len(image.shape) != 3 or image.shape[2] != 3:
#             raise ValueError(f"Image must be 3-channel RGB, got shape: {image.shape}")
#
#         # נסיון 1: החתימה הפשוטה ביותר - רק image ו-shape
#         if shape is not None:
#             try:
#                 return self.face_rec_model.compute_face_descriptor(image, shape)
#             except Exception as e1:
#                 print(f"🔧 DEBUG: Simple (img, shape) failed: {str(e1)[:200]}")
#
#         # נסיון 2: רק image (בלי shape)
#         try:
#             return self.face_rec_model.compute_face_descriptor(image)
#         except Exception as e2:
#             print(f"🔧 DEBUG: Image only failed: {str(e2)[:200]}")
#
#         # אם הכל נכשל - זה אומר שיש בעיה עם הכנת התמונה
#         print(f"🔧 DEBUG: All basic attempts failed!")
#         print(f"🔧 DEBUG: Image shape: {image.shape}, dtype: {image.dtype}")
#         print(f"🔧 DEBUG: Image contiguous: {image.flags['C_CONTIGUOUS']}")
#         print(f"🔧 DEBUG: Image min/max: {image.min()}/{image.max()}")
#
#         raise Exception(f"Cannot compute face descriptor - image format issue")
#
#     def extract_feature_vector(self, image: np.ndarray) -> Optional[np.ndarray]:
#         """חילוץ וקטור מאפיינים עם יישור נכון לתמונת ייחוס"""
#
#         if not self.is_ready:
#             print("FaceFeatureExtractor not ready - missing models")
#             return None
#
#         try:
#             # הכנת התמונה
#             rgb_image = self._prepare_image_for_processing(image)
#
#             # זיהוי פנים
#             face_boxes = self._detect_faces_internal(rgb_image)
#
#             if not face_boxes:
#                 print("👤 No faces detected in image")
#                 return None
#
#             if len(face_boxes) > 1:
#                 print(f"👥 Multiple faces detected ({len(face_boxes)}), using the largest one")
#
#                 # בחירת הפנים הגדולות ביותר (יותר מדויק מהראשונות)
#                 face_areas = [(face_box.width() * face_box.height(), i, face_box)
#                               for i, face_box in enumerate(face_boxes)]
#                 face_areas.sort(reverse=True)  # מהגדול לקטן
#                 _, face_index, face_box = face_areas[0]
#                 print(f"📏 Selected face {face_index + 1} (largest: {face_box.width()}x{face_box.height()})")
#             else:
#                 face_box = face_boxes[0]
#
#             # זיהוי נקודות ציון
#             shape = self.landmark_detector.predictor(rgb_image, face_box)
#             landmarks = [(shape.part(i).x, shape.part(i).y) for i in range(shape.num_parts)]
#
#             # יישור פנים באמצעות הפונקציה שלך
#             try:
#                 from app.services.face_alignment_utils import quick_align_face
#                 aligned_image = quick_align_face(rgb_image, landmarks)
#
#                 # זיהוי פנים מחדש בתמונה המיושרת
#                 aligned_face_boxes = self._detect_faces_internal(aligned_image)
#
#                 if aligned_face_boxes:
#                     # מציאת הפנים הקרובות ביותר למיקום המקורי
#                     original_center = (face_box.center().x, face_box.center().y)
#                     best_match = None
#                     min_distance = float('inf')
#
#                     for aligned_face in aligned_face_boxes:
#                         aligned_center = (aligned_face.center().x, aligned_face.center().y)
#                         distance = np.sqrt((original_center[0] - aligned_center[0]) ** 2 +
#                                            (original_center[1] - aligned_center[1]) ** 2)
#                         if distance < min_distance:
#                             min_distance = distance
#                             best_match = aligned_face
#
#                     if best_match:
#                         shape_aligned = self.landmark_detector.predictor(aligned_image, best_match)
#                         face_descriptor = self._compute_face_descriptor_robust(aligned_image, shape_aligned,
#                                                                                num_jitters=1)
#                         print("✅ Used aligned face (reference photo)")
#                     else:
#                         face_descriptor = self._compute_face_descriptor_robust(rgb_image, shape, num_jitters=1)
#                         print("⚠️ No matching face found in aligned image, used original")
#                 else:
#                     face_descriptor = self._compute_face_descriptor_robust(rgb_image, shape, num_jitters=1)
#                     print("⚠️ Face detection failed in aligned image, used original")
#
#             except Exception as align_error:
#                 face_descriptor = self._compute_face_descriptor_robust(rgb_image, shape, num_jitters=1)
#                 print(f"⚠️ Face alignment failed: {align_error}, used original")
#
#             feature_vector = np.array(face_descriptor, dtype=np.float32)
#             print(f"✅ Feature vector extracted: {len(feature_vector)} dimensions")
#             return feature_vector
#
#         except Exception as e:
#             print(f"❌ Error extracting feature vector: {e}")
#             print(f"Detailed error: {type(e).__name__}: {str(e)}")
#             return None
#         finally:
#             try:
#                 del rgb_image, face_boxes
#                 gc.collect()
#             except:
#                 pass
#
#     def extract_multiple_faces(self, image: np.ndarray) -> List[np.ndarray]:
#         """חילוץ וקטורי מאפיינים ממספר פנים בתמונה עם יישור נכון"""
#         if not self.is_ready:
#             print("FaceFeatureExtractor not ready - missing models")
#             return []
#
#         try:
#             # הכנת התמונה
#             rgb_image = self._prepare_image_for_processing(image)
#
#             # זיהוי פנים בתמונה המקורית
#             face_boxes = self._detect_faces_internal(rgb_image)
#
#             if not face_boxes:
#                 print("👤 No faces detected in image")
#                 return []
#
#             feature_vectors = []
#
#             # עיבוד כל פנים בנפרד - זה הפתרון!
#             for i, face_box in enumerate(face_boxes):
#                 try:
#                     print(f"🔍 Processing face {i + 1}/{len(face_boxes)}")
#
#                     # זיהוי נקודות ציון על הפנים הספציפיות האלה
#                     shape = self.landmark_detector.predictor(rgb_image, face_box)
#                     landmarks = [(shape.part(j).x, shape.part(j).y) for j in range(shape.num_parts)]
#
#                     # --- החלק המתוקן: יישור חכם ---
#
#                     # חיתוך הפנים + יישור (מומלץ)
#                     try:
#                         # חיתוך אזור הפנים עם מרווח
#                         margin = 50  # מרווח בפיקסלים
#                         face_left = max(0, face_box.left() - margin)
#                         face_top = max(0, face_box.top() - margin)
#                         face_right = min(rgb_image.shape[1], face_box.right() + margin)
#                         face_bottom = min(rgb_image.shape[0], face_box.bottom() + margin)
#
#                         # בדיקה שהחיתוך תקין
#                         if face_right <= face_left or face_bottom <= face_top:
#                             raise ValueError("Invalid face region")
#
#                         face_region = rgb_image[face_top:face_bottom, face_left:face_right]
#
#                         if face_region.size == 0:
#                             raise ValueError("Empty face region")
#
#                         # התאמת נקודות הציון לאזור החתוך
#                         adjusted_landmarks = []
#                         for x, y in landmarks:
#                             adj_x = x - face_left
#                             adj_y = y - face_top
#                             # בדיקה שהנקודות בתוך האזור
#                             if 0 <= adj_x < face_region.shape[1] and 0 <= adj_y < face_region.shape[0]:
#                                 adjusted_landmarks.append((adj_x, adj_y))
#
#                         if len(adjusted_landmarks) < 10:  # לא מספיק נקודות ציון
#                             raise ValueError("Not enough valid landmarks")
#
#                         # יישור הפנים החתוכות באמצעות הפונקציה שלך
#                         from app.services.face_alignment_utils import quick_align_face
#
#                         # DEBUG: בדיקה לפני יישור
#                         print(f"🔧 DEBUG: Face region shape: {face_region.shape}")
#                         print(f"🔧 DEBUG: Adjusted landmarks count: {len(adjusted_landmarks)}")
#                         print(
#                             f"🔧 DEBUG: Sample landmarks: {adjusted_landmarks[:3] if len(adjusted_landmarks) >= 3 else adjusted_landmarks}")
#
#                         # בדיקה שיש לפחות 68 נקודות ציון (standard face landmarks)
#                         if len(adjusted_landmarks) < 68:
#                             print(f"❌ Not enough landmarks for alignment: {len(adjusted_landmarks)} < 68")
#                             raise ValueError(f"Not enough landmarks: {len(adjusted_landmarks)}")
#
#                         # בדיקה שהנקודות בטווח התמונה
#                         valid_landmarks = 0
#                         for x, y in adjusted_landmarks:
#                             if 0 <= x < face_region.shape[1] and 0 <= y < face_region.shape[0]:
#                                 valid_landmarks += 1
#
#                         print(f"🔧 DEBUG: Valid landmarks in region: {valid_landmarks}/{len(adjusted_landmarks)}")
#
#                         if valid_landmarks < 60:  # לפחות 60 נקודות חוקיות
#                             print(f"❌ Not enough valid landmarks: {valid_landmarks} < 60")
#                             raise ValueError(f"Not enough valid landmarks: {valid_landmarks}")
#
#                         # נסיון יישור עם טיפול בשגיאות מפורט
#                         try:
#                             aligned_face_region = quick_align_face(face_region, adjusted_landmarks)
#                             print(
#                                 f"✅ Alignment successful! Original: {face_region.shape}, Aligned: {aligned_face_region.shape}")
#
#                             # בדיקה שהתמונה המיושרת לא ריקה
#                             if aligned_face_region is None or aligned_face_region.size == 0:
#                                 print("❌ Alignment returned empty image")
#                                 raise ValueError("Alignment returned empty image")
#
#                             # בדיקה שהתמונה שונה מהמקורית (באמת התיישרה)
#                             if np.array_equal(aligned_face_region, face_region):
#                                 print("⚠️ Alignment returned same image (probably no rotation needed)")
#                             else:
#                                 print("✅ Image was actually rotated/aligned")
#
#                         except Exception as align_sub_error:
#                             print(f"❌ Alignment function failed: {type(align_sub_error).__name__}: {align_sub_error}")
#                             # אם היישור נכשל, נחזור לתמונה המקורית
#                             print("🔄 Falling back to original face region")
#                             face_descriptor = self._compute_face_descriptor_robust(rgb_image, shape, num_jitters=0)
#                             print(f"✅ Face {i + 1}: used original after alignment failure")
#                             feature_vector = np.array(face_descriptor, dtype=np.float32)
#                             feature_vectors.append(feature_vector)
#                             print(f"📊 Face {i + 1}: vector size {len(feature_vector)}")
#                             continue  # לעבור לפנים הבאות
#
#                         # זיהוי פנים באזור המיושר
#                         aligned_faces = self._detect_faces_internal(aligned_face_region)
#                         print(f"🔧 DEBUG: Found {len(aligned_faces)} faces in aligned region")
#
#                         if aligned_faces:
#                             print(f"✅ Face detected in aligned region")
#                             # זיהוי נקודות ציון באזור המיושר
#                             aligned_shape = self.landmark_detector.predictor(aligned_face_region, aligned_faces[0])
#
#                             # חילוץ וקטור מהפנים המיושרות
#                             face_descriptor = self._compute_face_descriptor_robust(aligned_face_region, aligned_shape,
#                                                                                    num_jitters=1)
#                             print(f"✅ Face {i + 1}: aligned and extracted")
#                         else:
#                             print(f"❌ No faces detected in aligned region, falling back to original")
#                             # אם זיהוי נכשל באזור המיושר - השתמש במקורי
#                             face_descriptor = self._compute_face_descriptor_robust(rgb_image, shape, num_jitters=1)
#                             print(f"⚠️ Face {i + 1}: alignment detection failed, used original")
#
#                     except Exception as align_error:
#                         print(f"❌ Full alignment process failed: {type(align_error).__name__}: {align_error}")
#                         print(f"🔧 DEBUG: Error details: {str(align_error)}")
#
#                         # אם כל התהליך נכשל - השתמש בתמונה המקורית
#                         face_descriptor = self._compute_face_descriptor_robust(rgb_image, shape, num_jitters=1)
#                         print(f"⚠️ Face {i + 1}: alignment failed ({str(align_error)}), used original")
#
#                     # המרה לוקטור
#                     feature_vector = np.array(face_descriptor, dtype=np.float32)
#                     feature_vectors.append(feature_vector)
#
#                     print(f"📊 Face {i + 1}: vector size {len(feature_vector)}")
#
#                 except Exception as e:
#                     print(f"❌ Error processing face {i + 1}: {e}")
#                     continue
#
#             print(f" Successfully extracted {len(feature_vectors)} face vectors with proper alignment")
#             return feature_vectors
#
#         except Exception as e:
#             print(f" Error extracting multiple faces: {e}")
#             return []
#         finally:
#             try:
#                 del rgb_image, face_boxes
#                 gc.collect()
#             except:
#                 pass
#
#     def process_image(self, image: np.ndarray, draw_faces: bool = True, draw_landmarks: bool = True):
#         if not self.is_ready:
#             print(" Required models not loaded")
#             return image, [], [], []
#
#         try:
#             # הכנת התמונה
#             rgb_image = self._prepare_image_for_processing(image)
#
#             # זיהוי פנים
#             face_boxes = self._detect_faces_internal(rgb_image)
#
#             landmarks_list = []
#             feature_vectors = []
#             result_image = image.copy()
#
#             for i, face_box in enumerate(face_boxes):
#                 try:
#                     # זיהוי נקודות ציון
#                     shape = self.landmark_detector.predictor(rgb_image, face_box)
#                     landmarks = [(shape.part(j).x, shape.part(j).y) for j in range(shape.num_parts)]
#                     landmarks_list.append(landmarks)
#
#                     # חילוץ וקטור מאפיינים (עם יישור אוטומטי חכם)
#                     try:
#                         # חיתוך ויישור כמו ב-extract_multiple_faces
#                         margin = 50
#                         face_left = max(0, face_box.left() - margin)
#                         face_top = max(0, face_box.top() - margin)
#                         face_right = min(rgb_image.shape[1], face_box.right() + margin)
#                         face_bottom = min(rgb_image.shape[0], face_box.bottom() + margin)
#
#                         face_region = rgb_image[face_top:face_bottom, face_left:face_right]
#                         adjusted_landmarks = [(x - face_left, y - face_top) for x, y in landmarks]
#
#                         from app.services.face_alignment_utils import quick_align_face
#                         aligned_face_region = quick_align_face(face_region, adjusted_landmarks)
#
#                         aligned_faces = self._detect_faces_internal(aligned_face_region)
#                         if aligned_faces:
#                             aligned_shape = self.landmark_detector.predictor(aligned_face_region, aligned_faces[0])
#                             face_descriptor = self._compute_face_descriptor_robust(aligned_face_region, aligned_shape,
#                                                                                    num_jitters=1)
#                         else:
#                             face_descriptor = self._compute_face_descriptor_robust(rgb_image, shape, num_jitters=1)
#                     except:
#                         face_descriptor = self._compute_face_descriptor_robust(rgb_image, shape, num_jitters=1)
#
#                     feature_vectors.append(np.array(face_descriptor, dtype=np.float32))
#
#                     # ציור מסגרות (אם יש FaceDetector)
#                     if draw_faces and self.detector:
#                         result_image = self.detector.draw_faces(result_image, [face_box])
#
#                     # ציור נקודות
#                     if draw_landmarks:
#                         for (x, y) in landmarks:
#                             cv2.circle(result_image, (x, y), 1, (255, 0, 0), -1)
#
#                 except Exception as e:
#                     print(f" Error processing face {i + 1}: {e}")
#                     continue
#
#             return result_image, face_boxes, landmarks_list, feature_vectors
#
#         except Exception as e:
#             print(f"Error processing image: {e}")
#             return image, [], [], []
#
#     def detect_faces_count(self, image: np.ndarray) -> int:
#         try:
#             # הכנת התמונה
#             rgb_image = self._prepare_image_for_processing(image)
#
#             # זיהוי פנים
#             faces = self._detect_faces_internal(rgb_image)
#
#             count = len(faces)
#             print(f"Detected {count} faces in image")
#             return count
#
#         except Exception as e:
#             print(f"Error counting faces: {e}")
#             return 0
#
#
# # יצירת אינסטנס גלובלי
# face_extractor = FaceFeatureExtractor()
#
# # ייצוא לשימוש חיצוני
# __all__ = ["FaceFeatureExtractor", "face_extractor", "FaceLandmarkDetector"]