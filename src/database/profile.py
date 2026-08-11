"""
profile.py

Defines the Profile class, which represents an individual identity
in the database. Each profile stores associated image paths, facial
embeddings, optional metadata and relevant dates.

Embeddings are normalised to support cosine similarity comparisons.
"""

import os
from datetime import datetime

import cv2
import numpy as np


class Profile:
    """
    Represents a single person within the database.

    A profile maintains a list of image file paths and their corresponding
    facial embeddings. It also stores optional metadata and timestamps for 
    creation and last update.
    """

    def __init__(self, person_id, image_path, embedding=None, metadata=None):
        """
        Initialises a new profile object.

        Args:
            person_id (str): Unique identifier for the individual.
            image_path (str): Path to the initial image.
            embedding (np.ndarray, optional): Facial embedding of input image.
            metadata (dict, optional): Additional attributes such as age or gender.
        """
        self.person_id = person_id

        self.image_paths = [image_path] if image_path else []

        self.embeddings = []
        if embedding is not None:
            self.embeddings.append(np.array(embedding, dtype=np.float32))

        self.metadata = metadata or {}

        self.created_at = datetime.now()
        self.updated_at = self.created_at
        
        self._image_metrics = [] # Image information used for database analysis


    @property
    def mean_embedding(self):
        """
        Compute the mean embedding for the profile.

        The mean embedding is calculated across all stored embeddings
        and L2-normalised to be used in calculating cosine similarity.

        Returns:
            np.ndarray or None: Normalised mean embedding vector, or None
            if no embeddings are available or the norm is zero.
        """
        if not self.embeddings:
            return None

        mean = np.mean(self.embeddings, axis=0)
        norm = np.linalg.norm(mean)

        if norm == 0:
            return None

        return mean / norm


    def add_image(self, image_path):
        """
        Add a new image path to the profile.

        Updates the 'updated_at' timestamp.

        Args:
            image_path (str): Path to the image in database.
        """
        self.image_paths.append(image_path)
        self.updated_at = datetime.now()

    
    def add_embedding(self, embedding):
        """
        Adds a new embedding to the profile.

        The embedding is converted to float32 and is L2-normalised 
        for the use of cosine similarity comparisons.

        Args:
            embedding (array): Facial embedding vector.
        """
        emb = np.array(embedding, dtype=np.float32, copy=False)

        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm

        self.embeddings.append(emb)
        self.updated_at = datetime.now()
        

    def load_image(self, index=0):
        """
        Load an image from the list of stored image paths.

        Validates that the index is valid and the image file 
        exists before reading the image to the system.

        Args:
            index (int, optional): Index of the image to load.

        Returns:
            np.ndarray or None: Loaded image in OpenCV format, 
            or None if the index is invalid or the file does not exist.
        """
        if index >= len(self.image_paths):
            return None

        path = self.image_paths[index]
        if not os.path.exists(path):
            return None

        return cv2.imread(path)