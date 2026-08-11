"""
match_processor.py

Handles processing of input media (images and videos) for facial recognition.

Extracts facial embeddings from images and tracks faces across video frames
per individual.
"""

import cv2
import numpy as np  

from processing.face_detector import FaceDetector
from utils.compute import use_gpu


# Initialises a face detector with optional GPU acceleration:
detector = FaceDetector(use_gpu=use_gpu())

# Maximum squared distance between face centroids to consider the same track in videos:
TRACK_DISTANCE_SQ = 10000


def process_search_image(file_path):
    """
    Processes a single image for face recognition.

    Loads the image, detects the largest face, and extracts
    its corresponding facial embedding vector.

    Args:
        file_path (str): The file path of the input image.

    Returns:
        dict: Contains a success boolean, message, image, and embedding.
    """
    image = cv2.imread(file_path)
    
    if image is None:
        return {    
            "success": False,
            "message": f"Cannot load image from: {file_path}",
            "image": image,
            "embedding": None
        }
        
    # Detect the face with the largest bounding box:
    result, message = detector.detect_biggest_face(image)
    
    if result is None:
        return {
            "success": False,
            "message": "Cannot detect any faces in the image.",
            "image": image,
            "embedding": None
        }
        
    # Extract and format embedding as a L2-normalised float32 vector
    embedding = result["embedding"]
    embedding = embedding.astype("float32").flatten()
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return {
        "success": True,
        "message": "Image inputted successfully.",
        "image": image,
        "embedding": embedding
    }
    
    
def process_search_video(video_path,
                         max_seconds=10,
                         sample_interval=0.25,
                         min_det_score=0.5,
                         min_track_samples=3):
    """
    Processes a video for face recognition by tracking faces over time and
    extracting embeddings for each track afterwards.

    Samples frames from the video, detects faces, and groups them into tracks
    based on spatial proximity. Each track represents a consistent face across frames.

    Args:
        video_path (str): File path to the input video file.
        max_seconds (int, optional): Maximum duration of video that is processed.
        sample_interval (float, optional): Interval, in secondsl, between frames.
        min_det_score (float, optional): Minimum detection confidence threshold.
        min_track_samples (int, optional): Number of embeddings required to retain track.

    Returns:
        dict: Result containing success status, message, and tracked face data.
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return {
            "success": False,
            "message": "Cannot open video file.",
            "tracks": []
        }

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Default for FPS if metadata is unavailable.
    if fps <= 0:
        fps = 25
        
    max_frames = int(min(total_frames, fps * max_seconds))

    # Determine how many frames to skip between samples
    frame_step = max(1, int(fps * sample_interval))

    tracks = {}
    next_track_id = 0

    frame_index = 0
    skip_counter = 0
    
    while frame_index < max_frames:
        success, frame = cap.read()

        if not success:
            break
        
        # Skip frames based on the sampling interval.
        skip_counter += 1
        if skip_counter < frame_step:
            frame_index += 1
            continue

        skip_counter = 0

        faces = detector.app.get(frame)

        for face in faces:
            # Filter detections by confidence score.
            if face.det_score < min_det_score:
                continue    
            
            # Compute face bounding box and centroid.
            x1, y1, x2, y2 = map(int, face.bbox)
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            
            # Extract and L2-normalise the facial embedding.
            embedding = face.embedding
            embedding = embedding.astype("float32").flatten()
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            matched_track = None
            min_distance = float("inf")
                    
            # Match current face to an existing track based on centroid distance.
            for track_id, track in tracks.items():
                prev_cx, prev_cy = track["last_centroid"]

                dx = cx - prev_cx
                dy = cy - prev_cy
                dist_sq = dx * dx + dy * dy

                if dist_sq < TRACK_DISTANCE_SQ and dist_sq < min_distance:
                    matched_track = track_id
                    min_distance = dist_sq
            
            # If no track found:
            if matched_track is None:
                matched_track = next_track_id
                tracks[matched_track] = {
                    "embeddings": [],
                    "last_centroid": (cx, cy),
                    "best_frame": None,
                    "best_score": 0
                }
                next_track_id += 1
            
            track = tracks[matched_track]

            # Update track with new embedding and position
            track["embeddings"].append(embedding)
            track["last_centroid"] = (cx, cy)

            # Store highest quality frame based on detection confidence
            if face.det_score > track["best_score"]:
                track["best_score"] = face.det_score
                track["best_frame"] = frame[y1:y2, x1:x2]

        frame_index += 1

    cap.release()
        
    # Converts the dictionary of tracks into a list for output
    output_tracks = []

    for track_id, track in tracks.items():

        # Discard tracks with insufficient samples.
        if len(track["embeddings"]) < min_track_samples:
            continue

        output_tracks.append({
            "track_id": track_id,
            "embeddings": track["embeddings"],
            "thumbnail": track["best_frame"]
        })

    return {
        "success": True,
        "message": "Video processed successfully.",
        "tracks": output_tracks
    }