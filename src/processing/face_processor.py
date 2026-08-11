"""
face_processor.py

Facilitates the processing of face images.

This file handles the face processing pipeline, with functionality for 
image loading, face detection, face alignment and feature extraction. 
It standardises outputs into a structured dictionary with the data
necessary for recognition, database enrolment and system analysis.
"""

import cv2

from .face_detector import FaceDetector
from .aligner import align_face_arcface
from utils.compute import use_gpu


# Only have one instance of the face detector.
_detector = None


def get_detector():
    """
    Initialises detector or returns the current face detector instance.

    The detector is created if one doent already exist, preventing
    multiple instances. CPU/GPU usage is determined dynamically.
    """
    global _detector
    
    if _detector is None:
        # Use GPU if defined in user settings, otherwise CPU:
        _detector = FaceDetector(use_gpu=use_gpu())
    return _detector


def _failure(message, image=None):
    """
    Standardised failure response.

    Ensures all failure cases return a consistent structure, simplifying
    error handling in downstream components.
    
    Args:
        image (np.ndarray, optional): The image inputted to the system.
    """
    return {
        "success": False,
        "message": message,
        "image": image,
        "aligned_face": None,
        "embedding": None,
        "n_embedding": None,
        "metrics": None,
        "age": None,
        "gender": None,
    }


def process_image(file_path):
    """
    The main face processing pipeline.

    Loads an image, detects the largest face, aligns it, and returns
    extracted features in a structured dictionary.

    Args:
        file_path (str): The file path to the input image.

    Returns:
        dict: Contains a success flag, aligned face, embeddings, metrics,
              and optional attributes such as age and gender.
    """
    image = cv2.imread(file_path)
    
    # Handle invalid or missing image cases:
    if image is None:
        return _failure(f"Cannot load image from: {file_path}.")

    detector = get_detector()
    
    # Detect the most largest face in the image:
    result, message = detector.detect_biggest_face(image)
    
    # In the case of detection failure:
    if result is None:
        return _failure(message, image=image)
    
    # Align face using detected keypoints:
    aligned = align_face_arcface(image, result["keypoints"])
    
    return {
        "success": True,
        "message": "Face detected and aligned successfully.",
        "aligned_face": aligned,
        "image": image,
        "embedding": result["embedding"],
        "n_embedding": result["n_embedding"],
        "metrics": result["metrics"],
        "age": result.get("age"),
        "gender": result.get("gender"),
    }
    

def reset_detector():
    """
    Reset the cached detector instance. Used whhen GPU/CPU setting 
    changes so the detector can be reinitialised.
    """
    global _detector
    _detector = None