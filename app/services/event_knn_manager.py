import numpy as np
from sklearn.neighbors import NearestNeighbors
from typing import List, Dict, Optional
from datetime import datetime
from app.database import database
from app.config import FaceRecognitionConfig
from app.services.feature_vector_utils import (
    normalize_vector,
    is_valid_vector,
    calculate_vector_norm,
    cosine_similarity,

)
class EventSpecificKNN:
    def __init__(self, event_id: str):
        self.event_id = event_id
        self.participants_data: List[Dict] = []
        self.knn_model: Optional[NearestNeighbors] = None
        self.vectors_matrix: Optional[np.ndarray] = None
        self.user_id_mapping: Dict[int, str] = {}
        self.is_built = False
        self.created_at = datetime.now()
        self.last_used = datetime.now()

    async def build_event_knn(self) -> bool:
        try:
            print(f"Building KNN for event {self.event_id} using your normalization functions...")
            # קבלת משתתפי האירוע עם וקטורי הפנים שלהם
            self.participants_data = await database.get_event_participants_vectors(self.event_id)

            if not self.participants_data:
                print(f"No participants with reference photos found for event {self.event_id}")
                return False
            if len(self.participants_data) < 2:
                print(
                    f"Event {self.event_id} has only {len(self.participants_data)} participants - KNN requires at least 2")
                return False

            print(f"Event {self.event_id} participants: {len(self.participants_data)} users")
            # הכנת מטריצת וקטורים מנורמלים
            normalized_vectors = []
            self.user_id_mapping = {}
            for idx, participant in enumerate(self.participants_data):
                user_id = participant.get("user_id")
                face_encoding = participant.get("face_encoding", [])
                if not face_encoding or not user_id:
                    continue
                if not is_valid_vector(face_encoding, FaceRecognitionConfig.DEFAULT_VECTOR_LENGTH):
                    print(f"Invalid vector for user {user_id}: length {len(face_encoding)}")
                    continue
                try:
                    original_norm = calculate_vector_norm(face_encoding)
                    normalized_vector = normalize_vector(face_encoding)
                    final_norm = calculate_vector_norm(normalized_vector)

                    normalized_vectors.append(normalized_vector)
                    self.user_id_mapping[len(normalized_vectors) - 1] = user_id
                    print(
                        f"User {participant.get('name', user_id)} ({user_id}): norm {original_norm:.3f} → {final_norm:.6f}")

                except Exception as norm_error:
                    print(f"Normalization failed for user {user_id}: {norm_error}")
                    continue

            if len(normalized_vectors) < 2:
                print(f"Not enough valid vectors for KNN: {len(normalized_vectors)}")
                return False

            # יצירת מטריצה numpy
            self.vectors_matrix = np.array(normalized_vectors)
            print(f"Built {FaceRecognitionConfig.DEFAULT_VECTOR_LENGTH}D matrix: {self.vectors_matrix.shape}")

            # בניית מודל KNN
            n_neighbors = min(5, len(normalized_vectors))
            self.knn_model = NearestNeighbors(
                n_neighbors=n_neighbors,
                metric='cosine',
                algorithm='auto'
            )

            self.knn_model.fit(self.vectors_matrix)
            print(f"KNN model trained: {n_neighbors} neighbors, {len(self.participants_data)} participants")

            self.is_built = True
            self.last_used = datetime.now()
            return True
        except Exception as e:
            print(f"Failed to build KNN for event {self.event_id}: {e}")
            return False
# כאשר KNNבנוי
    def find_similar_users(self, face_vector: List[float],
                           similarity_threshold: float = FaceRecognitionConfig.DEFAULT_SIMILARITY_THRESHOLD) -> List[Dict]:
        if not self.is_built or self.knn_model is None:
            return []
        self.last_used = datetime.now()
        try:
            if not is_valid_vector(face_vector, FaceRecognitionConfig.DEFAULT_VECTOR_LENGTH):
                print(f"Invalid search vector: length {len(face_vector)}")
                return []
            normalized_search_vector = normalize_vector(face_vector)
            search_vector_np = np.array([normalized_search_vector])

            # חיפוש KNN
            distances, indices = self.knn_model.kneighbors(search_vector_np)

            matches = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx in self.user_id_mapping:
                    user_id = self.user_id_mapping[idx]
                    participant = next((p for p in self.participants_data if p.get("user_id") == user_id), None)

                    if participant:
                        # המרת distance ל-similarity
                        knn_similarity = 1.0 - distance
                        participant_vector = participant.get("face_encoding", [])
                        your_cosine_sim = cosine_similarity(face_vector, participant_vector)

                        # בדיקת סף
                        if knn_similarity >= similarity_threshold:
                            matches.append({
                                "user_id": user_id,
                                "similarity": round(knn_similarity, 4),
                                "confidence": "High" if knn_similarity >= FaceRecognitionConfig.HIGH_CONFIDENCE_THRESHOLD else "Medium",
                                "participant_data": participant
                            })

                            print(
                                f"Match: {participant.get('name', user_id)} - KNN: {knn_similarity:.4f}, Cosine: {your_cosine_sim:.4f}")

            return sorted(matches, key=lambda x: x['similarity'], reverse=True)

        except Exception as e:
            print(f"KNN search failed: {e}")
            return []


class KNNEventManager:
    def __init__(self, max_events: int = FaceRecognitionConfig.MAX_KNN_CACHED_EVENTS):
        self.event_knns: Dict[str, EventSpecificKNN] = {}
        self.max_events = max_events

    async def get_or_create_event_knn(self, event_id: str) -> Optional[EventSpecificKNN]:
        # אם יש כבר - החזר אותו
        if event_id in self.event_knns:
            event_knn = self.event_knns[event_id]
            event_knn.last_used = datetime.now()
            return event_knn
        # ניקוי מטמון אם מלא
        if len(self.event_knns) >= self.max_events:
            self._cleanup_old_events()
        # יצירת KNN חדש
        event_knn = EventSpecificKNN(event_id)
        success = await event_knn.build_event_knn()
        if success:
            self.event_knns[event_id] = event_knn
            return event_knn
        return None

    def _cleanup_old_events(self):
        if len(self.event_knns) < self.max_events:
            return

        # מיון לפי זמן שימוש אחרון
        sorted_events = sorted(
            self.event_knns.items(),
            key=lambda x: x[1].last_used
        )

        # מחיקת המחצית הישנה
        to_remove = len(sorted_events) // 2
        for i in range(to_remove):
            event_id = sorted_events[i][0]
            print(f"Removing old KNN cache for event: {event_id}")
            del self.event_knns[event_id]

    def get_cache_stats(self) -> Dict:
        return {
            "active_events": len(self.event_knns),
            "max_events": self.max_events,
            "events": {event_id: knn.get_stats() for event_id, knn in self.event_knns.items()}
        }

    def clear_event_cache(self, event_id: str = None):
        if event_id:
            if event_id in self.event_knns:
                del self.event_knns[event_id]
                print(f"Cleared KNN cache for event: {event_id}")
        else:
            self.event_knns.clear()
            print("Cleared all KNN cache")
# יצירת instance גלובלי
knn_event_manager = KNNEventManager(max_events=10)
# פונקציה עזר לשימוש קל
async def find_matches_in_event_knn_with_your_functions(event_id: str, face_vector: List[float],
                                                        similarity_threshold: float = FaceRecognitionConfig.DEFAULT_SIMILARITY_THRESHOLD) -> \
List[Dict]:
    try:
        event_knn = await knn_event_manager.get_or_create_event_knn(event_id)

        if event_knn and event_knn.is_built:
            matches = event_knn.find_similar_users(face_vector, similarity_threshold)
            if matches:
                print(f"Event-KNN found {len(matches)} matches for event {event_id}")
                return matches

        # Fallback לפונקציה המקורית שלך
        print(f"Falling back to original method for event {event_id}")
        from app.services.feature_vector_utils import compare_user_to_participants_vectors

        participants = await database.get_event_participants_vectors(event_id)
        return compare_user_to_participants_vectors(face_vector, participants, similarity_threshold)

    except Exception as e:
        print(f" KNN matching failed for event {event_id}: {e}")
        # Fallback במקרה של שגיאה
        from app.services.feature_vector_utils import compare_user_to_participants_vectors
        participants = await database.get_event_participants_vectors(event_id)
        return compare_user_to_participants_vectors(face_vector, participants, similarity_threshold)