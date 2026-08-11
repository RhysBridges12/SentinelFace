"""
face_detector.py

Facilitates the detection of faces, embedding extraction, and image quality evaluation.

This file uses InsightFace to detect faces and compute embeddings, and applies a
series of quality filters (pose, face size, brightness, sharpness and the Insight face 
detection score) to ensure only high-quality face samples are inducted to the database.

Also tracks statistics on accepted and rejected images for system analytics.
"""

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from utils.system_logger import write_log


# Resolution used by the face detector:
DET_SIZE = (512, 512)


# Thresholds used to determine whether a detected face is acceptable.
# Calculated by analysing similarity score drop offs across each metric.
QUALITY_THRESHOLDS = {
    "enabled": True, # Enable / disable here.

    "pose": {
        "min": 0.65,  # Minimum frontal alignment score.
    },
    "face_size": {
        "min": 90,  # Minimum face dimension, width or height. (pixels)
    },
    "brightness": {
        "min": 90,  # Too dark below this.
        "max": 180,  # Too bright above this.
    },
    "sharpness": {
        "min": 140,  # Blur threshold (Laplacian variance)
    },
    "det_score": {
        "min": 0.6,  # Detection confidence threshold.
    }
}


class FaceDetector:
    """
    Enables face detection, embedding extraction, and quality filtering.

    Uses InsightFace detection and adds additional validation logic to
    ensure only high-quality face samples are allowed into the database.
    """

    def __init__(self, use_gpu=False):
        """
        Initialises the face detector.

        Selects GPU or CPU execution based on user settings, prepares 
        the InsightFace model and enables tracking of quality stats.

        Args:
            use_gpu (bool): Flag indicating to use GPU acceleration or not.
        """
        mode = 0 if use_gpu else -1

        self.app = FaceAnalysis(name="buffalo_l")
        self.app.prepare(ctx_id=mode, det_size=DET_SIZE)

        # Tracks enrolment statistics for analysis and reporting.
        self.stats = {
            "total": 0,
            "accepted": 0,
            "rejected": 0,
            "reasons": {
                "bad_pose": 0,
                "face_too_small": 0,
                "too_dark": 0,
                "too_bright": 0,
                "too_blurry": 0,
                "low_det_score": 0,
                "bad_pose_and_blur": 0,
                "no_face": 0,
            }
        }


    # Compute quality metrics.
    def compute_brightness(self, image):
        """
        Compute average brightness of an image using grayscale intensity.
                  
        Args:
            image (np.ndarray): Input image (BGR format)
            
        Returns:
            float: Mean pixel intensity across image.
        """
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(gray_image.mean())
    
    
    def compute_sharpness(self, image):
        """
        Estimate image sharpness using Laplacian variance.
        Higher values indicate sharper images (more edges)    
            
        Args:
            image (np.ndarray): Input image (BGR format)

        Returns:
            float: Sharpness score across image.
        """
        if image is None or image.size == 0:
            return 0

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray_image, cv2.CV_64F).var())


    def compute_pose_score(self, kps):
        """
        Estimate how frontal a face is using face keypoints.
        Measures horizontal alignment of the nose relative to the eyes.
        Scaled so that a centred nose = 1.0 and large deviations = 0.0
        
        Args:
            kps (list): Keypoints [left_eye, right_eye, nose, left_mouth, right_mouth].

        Returns:
            float: Pose score between 0 (poor) and 1 (frontal)
        """
        
        if kps is None or len(kps) < 5:
            return 0

        left_eye = kps[0]
        right_eye = kps[1]
        nose = kps[2]

        eye_mid = (left_eye[0] + right_eye[0]) / 2
        eye_dist = np.linalg.norm(left_eye - right_eye)

        # Ensure distance between eyes isn't negligible:
        if eye_dist < 0.00001:
            return 0

        nose_offset = abs(nose[0] - eye_mid)
        diff = nose_offset / eye_dist

        # Ensure pose score is in range 0 -> 1.
        pose_score = 1 - np.clip(diff * 2, 0, 1) 
        return float(pose_score)
    

    def compute_metrics(self, image, face):
        """
        Compute all quality metrics for a detected face.

        Includes brightness, sharpness, detection score, face size,
        pose alignment, and overall detection quality.
        
        Args:
            image (np.ndarray): Input image (BGR format)
            face (insightface.face): Detected face dictionary keypoints and embeddings.

        Returns:
            dict: Dictionary of computed metrics.
        """
        x1, y1, x2, y2 = map(int, face.bbox)

        # Bounding box must be smaller than image boundaries:
        h_img, w_img = image.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w_img, x2)
        y2 = min(h_img, y2)

        face_crop = image[y1:y2, x1:x2]

        width = x2 - x1
        height = y2 - y1

        brightness = self.compute_brightness(face_crop)
        sharpness = self.compute_sharpness(face_crop)
        det_score = float(face.det_score)
        face_size = min(width, height) # Smallest dimension used so face is big enough.
        pose = self.compute_pose_score(face.kps)

        return {
            "brightness": brightness,
            "sharpness": sharpness,
            "det_score": det_score,
            "face_size": face_size,
            "pose": pose,
        }


    def evaluate_quality(self, metrics):
        """
        Evaluate whether a face meets quality thresholds or not.
        
        Args:
            metrics (dict): The quality information about the face image.

        Returns:
            dict:
                valid (bool): True if face has no quality issues, otherwise False.
                issues (list): Reasons for rejection (One or multiple quality issues)
        """
        if not QUALITY_THRESHOLDS["enabled"]:
            return {"valid": True, "issues": []}

        issues = []

        # Detection confidence:
        if metrics["det_score"] < QUALITY_THRESHOLDS["det_score"]["min"]:
            issues.append("low_det_score")

        # Pose alignment:
        if metrics["pose"] < QUALITY_THRESHOLDS["pose"]["min"]:
            issues.append("bad_pose")

        # Face size:
        if metrics["face_size"] < QUALITY_THRESHOLDS["face_size"]["min"]:
            issues.append("face_too_small")

        # Brightness checks
        if metrics["brightness"] < QUALITY_THRESHOLDS["brightness"]["min"]:
            issues.append("too_dark")

        if metrics["brightness"] > QUALITY_THRESHOLDS["brightness"]["max"]:
            issues.append("too_bright")

        # Blur detection
        if metrics["sharpness"] < QUALITY_THRESHOLDS["sharpness"]["min"]:
            issues.append("too_blurry")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }


    def log_stats(self, user="system", role="system"):
        """
        Logs a summary of dataset quality statistics.

        Creates a structured log entry containing total processed images,
        acceptance rates, and reasons for rejection.

        Args:
            user (str): User triggering the log (default: system).
            role (str): Role associated with the log (default: system).
        """
        total = self.stats["total"]
        accepted = self.stats["accepted"]
        rejected = self.stats["rejected"]

        if total == 0:
            write_log(
                action="Enrolment Quality Report",
                user=user,
                role=role,
                category="analytics",
                details={
                    "message": "No images processed"
                }
            )
            return

        acceptance_rate = accepted / total
        rejection_rate = rejected / total

        write_log(
            action="Enrolment Quality Report",
            user=user,
            role=role,
            category="analytics",
            details={
                "total_images": total,
                "accepted": accepted,
                "rejected": rejected,
                "acceptance_rate": round(acceptance_rate, 4),
                "rejection_rate": round(rejection_rate, 4),
                "rejection_breakdown": self.stats["reasons"]
            }
        )
                                                                             

    def detect_biggest_face(self, image):
        """
        Detect and return the largest valid face in an image.

        Applies quality filtering and updates internal statistics.
        
        Args:
            image (np.ndarray): Input image (BGR format)

        Returns:
            tuple:
                dict or None: Face data (if valid)
                str: Success or failure message
        """
        self.stats["total"] += 1

        faces = self.app.get(image)

        if not faces:
            self.stats["rejected"] += 1
            self.stats["reasons"]["no_face"] += 1
            return None, "No faces detected"

        # Select the largest detected face:
        face = max(
            faces,
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
        )

        metrics = self.compute_metrics(image, face)
        quality = self.evaluate_quality(metrics)

        # Reject low-quality detections:
        if not quality["valid"]:
            self.stats["rejected"] += 1

            for issue in quality["issues"]:
                if issue in self.stats["reasons"]:
                    self.stats["reasons"][issue] += 1

            return None, f"Rejected: {', '.join(quality['issues'])}"

        self.stats["accepted"] += 1

        return {
            "box": face.bbox,
            "keypoints": face.kps,
            "embedding": face.embedding,
            "n_embedding": face.normed_embedding,
            "metrics": metrics,
        }, "Collected"