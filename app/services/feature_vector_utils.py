import math
import os
from typing import List, Optional, Tuple
from app.config import FaceRecognitionConfig


def load_vector_from_txt(file_path: str) -> List[float]:
    with open(file_path, 'r') as file:
        return [float(line.strip()) for line in file if line.strip()]

# בןדקת שוקטור תקין באורך
def is_valid_vector(vector ,expected_length=FaceRecognitionConfig.DEFAULT_VECTOR_LENGTH):
    return len(vector) == expected_length

# חישוב אורך וקטור נורמה
def calculate_vector_norm(vector):
    return math.sqrt(sum(x**2 for x in vector))

#נירמול וקטור
def normalize_vector(vector):
    norm=calculate_vector_norm(vector)
    if norm==0:
      raise ValueError("A vector with zero length cannot be normalized")
    return[x/norm for x in vector]

#מכפלה פנימית
def dot_product(vec1,vec2):
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same length")
    return sum (a * b for a , b in zip(vec1,vec2))

#חישוב דמיון קוסינוס
def cosine_similarity(vec1,vec2):
    norm1=calculate_vector_norm(vec1)
    norm2=calculate_vector_norm(vec2)
    if norm1==0 or norm2==0:
        raise ValueError("Vectors must have same length")
    return dot_product(vec1,vec2) / (norm1 * norm2)

#"השוואת וקטור משתמש לוקטורי המשתתפים באירוע

def compare_user_to_participants_vectors(user_vector, participants_vectors, similarity_threshold=FaceRecognitionConfig.DEFAULT_SIMILARITY_THRESHOLD ):

    matches = []
    if hasattr(user_vector, 'tolist'):
        user_vector = user_vector.tolist()

    for participant in participants_vectors:
        try:
            participant_vector = participant.get("face_encoding", [])
            user_id = participant.get("user_id")

            if not participant_vector or not user_id:
                continue

            # חישוב דמיון
            similarity = cosine_similarity(user_vector, participant_vector)

            if similarity >= similarity_threshold:
                matches.append({
                    "user_id": user_id,
                    "similarity": round(similarity, 4),
                    "confidence": "High" if similarity >= FaceRecognitionConfig.HIGH_CONFIDENCE_THRESHOLD else "Medium",
                    "participant_data": participant
                })
                print(f" Match found: User {user_id}, similarity: {similarity:.4f}")

        except Exception as e:
            print(f" Error comparing with participant {participant.get('user_id', 'unknown')}: {e}")
            continue

    return sorted(matches, key=lambda x: x['similarity'], reverse=True)


def process_photographer_image_faces(image_faces_vectors, participants_vectors, similarity_threshold=0.92):
    all_matches = []

    for face_index, face_vector in enumerate(image_faces_vectors):
        face_matches = compare_user_to_participants_vectors(
            face_vector,
            participants_vectors,
            similarity_threshold
        )

        # הוספת אינדקס הפנים לכל התאמה
        for match in face_matches:
            match["face_index"] = face_index
            all_matches.append(match)

    return all_matches

# ייצוא הפונקציות
__all__ = [
    "load_vector_from_txt",
    "is_valid_vector",
    "calculate_vector_norm",
    "normalize_vector",
    "dot_product",
    "cosine_similarity",
    "compare_user_to_participants_vectors",
    "process_photographer_image_faces",

]