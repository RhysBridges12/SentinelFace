"""
aligner.py

Handles facial alignment using a predefined ArcFace template.

This file provides functionality to normalise faces based on
detected facial landmarks (keypoints). Aligning faces improves consistency across
database entries, which is critical for extracting useful facial embeddings.

The alignment process computes an affine transformation that maps detected
keypoints to a standard reference template.
"""

import numpy as np
import cv2


# Standard ArcFace 5-point facial landmark template (for 112x112 images)
# Format: [left_eye, right_eye, nose, left_mouth, right_mouth]
ARC_FACE_TEMPLATE = np.array([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041]
], dtype=np.float32)


def align_face_arcface(img, kps, output_size=(112, 112)):
    """
    Align a face image to the ArcFace reference template.

    This function applies an affine transformation to map detected facial
    keypoints onto a standard template, producing a normalised face image.

    Args:
        img (np.ndarray): The input image of a face.
        kps (list): Facial keypoints of input image (5, 2).
        output_size (tuple): Desired output image size (w, h).

    Returns:
        np.ndarray: The aligned face image at the desired resolution.
    """

    # Convert input keypoints to NumPy array if needed:
    image_kps = np.asarray(kps, dtype=np.float32)

    # Scale ArcFace template to desired size:
    template = ARC_FACE_TEMPLATE.copy()
    template[:, 0] *= output_size[0] / 112
    template[:, 1] *= output_size[1] / 112

    # Estimate affine transformation calculated using Least Median of Squares method.
    # Ignores outlier points incase landmark detections are inaccurate.
    transform, _ = cv2.estimateAffinePartial2D(image_kps, template, method=cv2.LMEDS)

    # Fallback to standard affine estimation if robust method fails.
    # May introduce slight geometric distortion.
    if transform is None:
        transform, _ = cv2.estimateAffine2D(image_kps, template)

    # Final fallback: if transformation cannot be computed, just resize image.
    if transform is None:
        return cv2.resize(img, output_size)
    
    aligned = cv2.warpAffine(img, transform, output_size, borderValue=0)

    return aligned