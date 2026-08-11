"""
profile_manager.py

Manages Profile objects, including creation, edits,
storage, retrieval, and comparisons.

This file is responsible for database persistence.
Uses FAISS-based vector searching to compare L2-normalised
embeddings with one another using cosine similarity.
"""

import json
import os
import random
import shutil
import uuid
from datetime import datetime

import cv2
import faiss
import numpy as np

from .database_manager import DatabaseManager
from .profile import Profile


DATABASE_DIR = "database"
IMAGES_DIR = os.path.join(DATABASE_DIR, "images")
INDEX_PATH = os.path.join(DATABASE_DIR, "faiss.index")

EMBEDDING_DIM = 512

# Similarity threshold for adding a new embedding to a profile:
SEARCH_THRESHOLD = 0.35


class ProfileManager:
    """
    Manages all profile objects in the database.
    
    Combines persistent storage with FAISS indexing to facilitate 
    database-wise similarity searches over all facial embeddings.
    """

    def __init__(self):
        """
        Initialises the profile manager.

        Loads existing profiles from the database folder and validates the
        FAISS index is consistent with stored facial embeddings. 
        If a mismatch is detected, the FAISS index is rebuilt.
        """
        self.db = DatabaseManager()
        self.profiles = {}
        self._next_id = 1 # Tracks next available ID for a new profile.

        os.makedirs(DATABASE_DIR, exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)

        self.load_profiles()
        
        # Try to load existing FAISS index and embedding-profile mapping.
        if os.path.exists(INDEX_PATH) and os.path.exists(INDEX_PATH + ".map"):
            self.index = faiss.read_index(INDEX_PATH)

            with open(INDEX_PATH + ".map", "r") as f:
                self.embedding_owners = json.load(f)
            
            # Rebuild FAISS index length is different from number of embeddings.
            if self.index.ntotal != len(self.embedding_owners):
                print("[WARN] FAISS mismatch — rebuilding")
                self.build_embedding_index()
                self.save_index()

        else:
            self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
            self.embedding_owners = []
            self.build_embedding_index()
            self.save_index()


    def _generate_id(self):
        """
        Generate a unique name for new profiles added to database.
        Incremnts the next ID counter.

        Returns:
            str: Sequentially generated ID of the form 'person_XXXXXX'.
        """
        person_id = f"person_{self._next_id:06d}"
        self._next_id += 1
        return person_id


    def _store_image_array(self, person_id, image_array):
        """
        Saves an image array to database and returns the file path
        the image was written to.

        Images are stored in a directory specific to the profile,
        using a UUID filename for uniqueness.

        Args:
            person_id (str): Identifier of a profile.
            image_array (np.ndarray): Image in BGR OpenCV format: (H, W, 3)

        Returns:
            str: File path of the newly stored image.
        """
        person_dir = os.path.join(IMAGES_DIR, person_id)
        os.makedirs(person_dir, exist_ok=True) # Ensure profiles directory exists.

        filename = f"{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(person_dir, filename)

        cv2.imwrite(file_path, image_array)

        return file_path
    
    
    def find_best_match(self, embedding):
        """
        Find the best matching profile for a given embedding.

        Performs a nearest neighbour search using FAISS and aggregates
        results per profile to identify the highest scoring candidate.

        Args:
            embedding (np.ndarray): Query embedding vector.

        Returns:
            tuple: (Profile, best_score, second_best_score) or (None, -1, -1) 
            if FAISS index is empty or no matches found above threshold.
        """
        if self.index.ntotal == 0:
            return None, -1.0, -1.0

        query = embedding.reshape(1, -1).astype("float32")
        faiss.normalize_L2(query)

        # Get top 10 nearest embeddings to facilitate the aggregation of profiles.
        scores, indices = self.index.search(query, 10)

        candidates = {}

        for score, index in zip(scores[0], indices[0]):
            if index == -1:
                continue

            pid = self.embedding_owners[index]

            if pid not in candidates or score > candidates[pid]: 
                candidates[pid] = float(score)

        if not candidates:
            return None, -1.0, -1.0

        # Sort profiles by highest similarity in descending order.
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: x[1],
            reverse=True
        )

        best_pid, best_score = sorted_candidates[0]
        best_profile = self.profiles.get(best_pid)

        # Second best calculated for score margin (top-1 vs top-2) used in enrolment.
        second_score = (
            sorted_candidates[1][1]
            if len(sorted_candidates) > 1
            else -1.0
        )
        
        return best_profile, best_score, second_score
    
    
    def find_top_matches(self, embedding, k=5):
        """
        Returns the top-k unique profile matches sorted by similarity.

        Performs a nearest neighbour search using FAISS and aggregates
        results per profile to identify the top k-scoring candidates.

        Args:
            embedding (np.ndarray): Query embedding vector.
            k (int, optional): Number of embeddings to return.

        Returns:
            tuple: (Profile, best_score, second_best_score) or (None, -1, -1) 
            if FAISS index is empty or no matches found above threshold.
        """
        if self.index.ntotal == 0:
            return []

        query = embedding.reshape(1, -1).astype("float32")
        faiss.normalize_L2(query)

        # Search more than k to allow aggregation
        scores, indices = self.index.search(query, k * 5)

        candidates = {}

        for score, index in zip(scores[0], indices[0]):
            if index == -1:
                continue

            pid = self.embedding_owners[index]

            if pid not in candidates or score > candidates[pid]:
                candidates[pid] = float(score)

        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: x[1],
            reverse=True
        )

        results = []
        for pid, score in sorted_candidates[:k]:
            profile = self.profiles.get(pid)
            if profile:
                results.append((profile, score))

        return results


    def register_face(self, image_array, embedding, metrics):
        """
        Register a face by matching or creating a profile.

        The embedding is compared against existing profiles using FAISS.
        If a sufficiently strong match is found, the face is added to the
        existing profile; otherwise, a new profile is created.

        Args:
            image_array (np.ndarray): Input image.
            embedding (np.ndarray): Face embedding vector.
            metrics (dict): Quality or diagnostic metrics.

        Returns:
            tuple: (Profile, bool) where bool indicates if a new profile was created.
        """
        profile, score, second_score = self.find_best_match(embedding)

        # If similarity above set decimal threshold:
        if profile and score >= SEARCH_THRESHOLD:
            stored_path = self._store_image_array(profile.person_id, image_array)

            profile.embeddings.append(embedding)
            profile.image_paths.append(stored_path)

            profile._image_metrics.append(metrics) 

            self.save_profile(profile)
            return profile, False

        # If no sufficiently similar embedding found, create new profile.
        else:
            person_id = self._generate_id()

            stored_path = self._store_image_array(person_id, image_array)

            profile = Profile(
                person_id=person_id,
                image_path=stored_path,
                embedding=embedding,
                metadata={},
            )

            profile._image_metrics = [metrics]

            self.save_profile(profile)
            return profile, True


    def save_profile(self, profile):
        """
        Writes or updates a profile and its associated data.

        Stores profile metadata, embeddings, image paths, and metrics
        in the database and updates the FAISS index.

        Args:
            profile (Profile): Profile to be persisted.
        """
        self.db.add_profile(
            profile.person_id,
            profile.created_at.isoformat(),
            profile.updated_at.isoformat(),
        )
        
        # Delete current data for profile before inserting updated data.
        self.db.delete_profile_data(profile.person_id)

        # Insert updated embeddings, images and metrics to the database:
        for emb, image_path in zip(profile.embeddings, profile.image_paths):
            self.db.add_embedding(profile.person_id, emb, image_path)
            
        metrics_list = getattr(profile, "_image_metrics", [])

        for image_path, metrics in zip(profile.image_paths, metrics_list):
            self.db.add_image(
                profile.person_id,
                image_path,
                metrics
            )

        self.profiles[profile.person_id] = profile
    
        new_embeddings = []
        
        # Get new embedding to be added to FAISS (Latest embedding added to profile)
        if len(profile.embeddings) == 1:
            new_embeddings = profile.embeddings
        else:
            new_embeddings = [profile.embeddings[-1]]
        
        for emb in new_embeddings:
            vec = emb.reshape(1, -1).astype("float32")
            faiss.normalize_L2(vec)

            self.index.add(vec) # Incrementally add new embedding to FAISS index.
            self.embedding_owners.append(profile.person_id)

        self.save_index()
    

    def load_profiles(self):
        """
        Load all profiles and embeddings from the database into memory.

        Reconstructs Profile objects in memory.
        Updates the internal ID counter reflect current database state.
        """
        self.profiles.clear() # Delete every profile instances in the system's memory.
        biggest_id = 0

        rows = self.db.get_all_profiles()
        
        for person_id, created_at, updated_at in rows:
            profile = Profile(
                person_id=person_id,
                image_path=None,
                embedding=None,
                metadata={},
            )
            
            profile.created_at = datetime.fromisoformat(created_at)
            profile.updated_at = datetime.fromisoformat(updated_at)
            
             # Add all image paths from database to loaded profiles.
            self.profiles[person_id] = profile
            profile.image_paths = self.db.get_image_paths(person_id)

            try:
                current_id = int(person_id.split("_")[1])
                biggest_id = max(biggest_id, current_id)
            except ValueError:
                pass
        
        # Add all image embeddings from database to loaded profiles.
        emb_rows = self.db.get_all_embeddings()
        for person_id, emb in emb_rows:
            if person_id in self.profiles:
                self.profiles[person_id].embeddings.append(emb)
                
        self._next_id = biggest_id + 1


    def build_embedding_index(self):
        """
        Rebuild the FAISS index from all stored embeddings normalised in float 32. 

        Used when embeddings are deleted from the system or if the FAISS
        index is inconsistent with embedding-profile mapping.
        """
        # Creates empty vector index for storing and searching facial embeddings.
        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        embeddings = []
        owners = []

        for profile in self.profiles.values():
            for emb in profile.embeddings:
                # Lists grow incrementally. (e.g. index x in each list aligns)
                embeddings.append(emb)
                owners.append(profile.person_id)

        if not embeddings:
            self.embedding_owners = []
            return

        matrix = np.vstack(embeddings).astype("float32")
        faiss.normalize_L2(matrix)

        self.index.add(matrix)
        self.embedding_owners = owners
            

    def add_face_to_profile(self, profile, image_array, embedding, metrics):
        """
        Adds a new image to an existing profile by storing the image in the database
        and adding embeddings and associating quality metrics to the profile object.

        Args:
            profile (Profile): Profile to be edited.
            image_array (np.ndarray): Input image.
            embedding (np.ndarray): Facial embedding.
            metrics (dict): Associated image metrics.

        Returns:
            str: Path to newly stored image.
        """
        stored_path = self._store_image_array(profile.person_id, image_array)

        profile.embeddings.append(embedding)
        profile.image_paths.append(stored_path)
        profile._image_metrics.append(metrics)

        self.save_profile(profile)

        return stored_path


    def save_index(self):
        """
        Persists the FAISS index and embedding-owner mapping to the database.
        Called when the FAISS index is updated or rebuilt.
        """
        faiss.write_index(self.index, INDEX_PATH)

        with open(INDEX_PATH + ".map", "w") as f:
            json.dump(self.embedding_owners, f)
            
    
    def add_note(self, person_id, text):
        """
        Add a user-written note to a profile.

        Args:
            person_id (str): Profile identifier.
            text (str): Text content of the note.
        """
        text = text.strip()
        if not text:
            return

        self.db.add_note(
            person_id,
            text,
            datetime.now().isoformat(),
        )


    def get_notes(self, person_id):
        """
        Read all notes associated with a profile from the database.
        """
        return self.db.get_notes(person_id)
    
    
    def replace_notes(self, person_id, notes):
        """
        Replace all notes for a profile.
        Called upon adding or removing a note to/from a profile.

        Args:
            person_id (str): Profile identifier.
            notes (list): List of note strings.
        """
        self.db.delete_notes(person_id)
        for n in notes:
            self.db.add_note(person_id, n, datetime.now().isoformat())
            
            
    def remove_image(self, person_id, image_path):
        """
        Remove an image and its associated embeddings and metrics from a profile.

        This includes removal from memory, database, and rebuilding
        the FAISS index to maintain consistency.

        Args:
            person_id (str): A profiles unique identifier.
            image_path (str): Path of the image to delete.
        """
        profile = self.profiles.get(person_id)
        if not profile:
            return
        
        if image_path in profile.image_paths:
            index = profile.image_paths.index(image_path)
            profile.image_paths.pop(index)

            if index < len(profile.embeddings):
                profile.embeddings.pop(index)

            if hasattr(profile, "_image_metrics") and index < len(profile._image_metrics):
                profile._image_metrics.pop(index)

        self.db.delete_image(person_id, image_path)
        self.db.delete_embedding(person_id, image_path)

        # Ensure empty profiles don't exist in the database.
        if len(profile.image_paths) == 0:
            self.db.delete_profile(person_id)

            del self.profiles[person_id]

        else:
            profile.updated_at = datetime.now()

        self.build_embedding_index()
        self.save_index()