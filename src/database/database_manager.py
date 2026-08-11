"""
database_manager.py

Provides persistence for all data within the system, managing 
profiles, embeddings, images, and notes using an SQLite database.

This file is responsible for all direct database interactions,
including all table creations, migrations, and changes.
"""

import os
import numpy as np
from sqlcipher3 import dbapi2 as sqlite3 


DATABASE_DIR = "database"
DB_PATH = os.path.join(DATABASE_DIR, "database.db")


class DatabaseManager:
    """
    Handles all database operations for profiles, embeddings, images, notes
    and image metrics.

    Encapsulates database interactions to maintain separation between profile
    persistence and other system logic.
    """

    def __init__(self):
        """
        Initialises the database manager, connecting to the database and ensures
        that the required tables exist inside the current database file.

        Creates the database directory if necessary, enables foreign key 
        relationships to other tables.
        """
        os.makedirs(DATABASE_DIR, exist_ok=True)

        # Allows cross thread usage of database (Necessary for the enrol threader)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        
        # Enables transparent AES database encryption with a password.
        self.conn.execute("PRAGMA key='Secure?DatabasE!'")
    
        # Prevents invalid inserts if foreign key doesn't exist. Enables cascade delete.
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()


    def _create_tables(self):
        """
        Create database tables if they do not already exist.

        Defines tables for profiles, embeddings, images and notes,
        along with relevant indexes to optimise querying.
        """
        # Profiles table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (    
                person_id TEXT PRIMARY KEY,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Embeddings table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT,
                image_path TEXT, 
                embedding BLOB,
                FOREIGN KEY(person_id) 
                    REFERENCES profiles(person_id) 
                    ON DELETE CASCADE
            )
        """)
        
        # Images table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT,
                image_path TEXT,
                face_size REAL,
                sharpness REAL,
                brightness REAL,
                width INTEGER,
                height INTEGER,
                det_score REAL,
                pose REAL,

                FOREIGN KEY(person_id) 
                    REFERENCES profiles(person_id) 
                    ON DELETE CASCADE
            )
        """)
        
        # Notes table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT,
                note TEXT,
                created_at TEXT,
                FOREIGN KEY(person_id) 
                    REFERENCES profiles(person_id) 
                    ON DELETE CASCADE
            );
        """)
        
        
        # Indexes for faster lookups by using person_id.
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_person_id
            ON embeddings(person_id)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_images_person_id
            ON images(person_id)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_person_id
            ON notes(person_id)
        """)

        self.conn.commit()


    def add_profile(self, person_id, created_at, updated_at):
        """
        Inserts to or updates a profile record.

        Args:
            person_id (str): Unique identifier of a profile.
            created_at (str): ISO timestamp of a profiles creation.
            updated_at (str): ISO timestamp of a profiles last update.
        """
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO profiles (
                    person_id, 
                    created_at, 
                    updated_at
                )
                VALUES (?, ?, ?)
            """, (person_id, created_at, updated_at))
        

    def get_all_profiles(self):
        """
        Retrieves all stored profiles and their associated dates.

        Returns:
            list: List of tuples containing profile ID's and dates.
        """
        query = self.conn.execute("""
            SELECT person_id, created_at, updated_at FROM profiles
        """)
        return query.fetchall()
    

    def delete_profile(self, person_id):
        """
        Deletes a profile and all associated data.

        Cascading foreign key constraints ensure related data in
        other tables (embeddings, images, notes) is also removed.

        Args:
            person_id (str): Unique identifier of a profile.
        """
        with self.conn:
            self.conn.execute(
                "DELETE FROM profiles WHERE person_id = ?",
                (person_id,)
            )

    
    def add_embedding(self, person_id, embedding, image_path):
        """
        Stores the facial embedding associated with an image.

        The embedding is L2-normalised and stored as a binary blob.

        Args:
            person_id (str): Profile identifier.
            embedding (np.ndarray): Facial embedding vector.
            image_path (str): Path to the associated image.
        """
        emb = embedding.astype("float32")

        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm

        # Convert to bytes for efficient storage. 
        emb_bytes = emb.tobytes()

        with self.conn:
            self.conn.execute("""
                INSERT INTO embeddings (
                    person_id,
                    image_path,
                    embedding
                )
                VALUES (?, ?, ?)
            """, (person_id, image_path, emb_bytes))


    def get_all_embeddings(self):
        """
        Retrieves all embeddings stored in the database.

        Returns:
            list: A list of (person_id, embedding) tuples.
        """
        query = self.conn.execute("""
            SELECT person_id, embedding FROM embeddings
        """)

        results = []
        for person_id, emb_blob in query:
            # Rebuild numpy arrays from binary blobs:
            emb = np.frombuffer(emb_blob, dtype="float32")
            results.append((person_id, emb))

        return results


    def get_embeddings_by_person(self, person_id):
        """
        Retrieves all embeddings for a specific profile.
        
        Not currently used in the system but could be useful for
        potential future extensions to the system.

        Args:
            person_id (str): Unique identifier of a profile.

        Returns:
            list: A list of embedding vectors.
        """
        query = self.conn.execute("""
            SELECT embedding FROM embeddings WHERE person_id = ?
        """, (person_id,))

        embeddings = []
        for (emb_blob,) in query:
            # Rebuild nparrays from binary blobs:
            emb = np.frombuffer(emb_blob, dtype="float32")
            embeddings.append(emb)

        return embeddings
    
    
    def delete_embedding(self, person_id, image_path):
        """
        Deletes a specific images facial embedding from the database.

        Args:
            person_id (str): Unique identifier of a profile.
            image_path (str): File path of image to be deleted.
        """
        with self.conn:
            self.conn.execute(
                "DELETE FROM embeddings WHERE person_id=? AND image_path=?",
                (person_id, image_path)
            )
                
                
    def add_image(self, person_id, image_path, metrics=None):
        """
        Stores image path and metadata to a specific profile in the database.

        Args:
            person_id (str): Unique identifier of a profile.
            image_path (str): File path of a stored image.
            metrics (dict, optional): Image quality metrics.
        """
        metrics = metrics or {}

        with self.conn:
            self.conn.execute("""
                INSERT INTO images (
                    person_id, 
                    image_path,
                    face_size,
                    sharpness,
                    brightness,
                    width,
                    height,
                    det_score,
                    pose
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                image_path,
                metrics.get("face_size"),
                metrics.get("sharpness"),
                metrics.get("brightness"),
                metrics.get("width"),
                metrics.get("height"),
                metrics.get("det_score"),
                metrics.get("pose"),
            ))


    def get_image_paths(self, person_id):
        """
        Retrieves all file paths for images associated with a profile.

        Args:
            person_id (str): Unique identifier of a profile.

        Returns:
            list: A list of image file paths.
        """
        query = self.conn.execute("""
            SELECT image_path FROM images WHERE person_id = ?
        """, (person_id,))
        return [row[0] for row in query]
    
    
    def delete_image(self, person_id, image_path):
        """
        Deletes a specific image from a profile.

        Args:
            person_id (str): Profile identifier.
            image_path (str): Path of the image to be deleted.
        """
        with self.conn:
            self.conn.execute(
                "DELETE FROM images WHERE person_id=? AND image_path=?",
                (person_id, image_path)
            )
            
    
    def delete_profile_data(self, person_id):
        """
        Deletes all embeddings and images from a profile.

        Args:
            person_id (str): Unique identifier of a profile.
        """
        with self.conn:
            self.conn.execute("""
                DELETE FROM embeddings WHERE person_id = ?
                """, (person_id,))
            self.conn.execute("""
                DELETE FROM images WHERE person_id = ?
                """, (person_id,))
    
    
    def add_note(self, person_id, note, created_at):
        """
        Store a textual note within a profile.

        Args:
            person_id (str): Unique identifier of a profile.
            note (str): Content of the note.
            created_at (str): ISO Timestamp of the notes creation.
        """
        with self.conn:
            self.conn.execute("""
                INSERT INTO notes (
                    person_id, 
                    note, 
                    created_at
                )
                VALUES (?, ?, ?)
            """, (person_id, note, created_at))


    def get_notes(self, person_id):
        """
        Retrieves all notes in a profile in chronological order.

        Args:
            person_id (str): Unique identifier of a profile.

        Returns:
            list: A list of note strings.
        """
        query = self.conn.execute("""
            SELECT note FROM notes WHERE person_id = ?
            ORDER BY id ASC
        """, (person_id,))
        return [row[0] for row in query]
    
    
    def delete_notes(self, person_id):
        """
        Deletes all notes within a profile.

        Args:
            person_id (str): Unique identifier of a profile.
        """
        with self.conn:
            self.conn.execute(
                "DELETE FROM notes WHERE person_id = ?",
                (person_id,),
            )
    

    def close(self):
        """
        Closes the database connection.
        """
        self.conn.close()