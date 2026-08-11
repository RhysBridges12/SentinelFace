"""
user_manager.py

Provides user management functionality including user creation,
password hashing, user authentication, and persistence using a JSON file.

Passwords are securely stored using the Argon2 hashing algorithm.
"""

import os
import json
from datetime import datetime

from argon2 import PasswordHasher


DATABASE_DIR = "database"
USERS_FILE = os.path.join(DATABASE_DIR, "users.json")


class UserManager:
    """
    Manages user accounts stored in a JSON file.

    Handles loading, saving, authentication, and creation of users.
    """

    def __init__(self):
        """
        Initialises the user manager.

        Ensures required directories and files exist, and loads all users
        into memory. The Argon2 password hasher is initialised here.
        """
        os.makedirs(DATABASE_DIR, exist_ok=True)
        
        # time_cost = Times hasher is run, (Hasher will run 3 times currently)
        # memory_cost = RAM usage of hasher (65536 = 64MB)
        # parallelism = Concurrent threads used during hashing (2 threads currently)
        self.hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)

        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        self.users = self.load_users()


    def load_users(self):
        """
        Load all users from the JSON file.

        Returns:
            list: A list of dictionaries representing users.
        """
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


    def save_users(self):
        """
        Persists all users to the database.

        Writes the user list in system memory to the JSON file.
        """
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.users, f, indent=2)


    def authenticate(self, username, password):
        """
        Authenticate a user using a username and password.

        Verifies the provided password against the stored Argon2 hash.
        If the stored hash parameters are outdated, the password is
        rehashed and updated automatically.

        Args:
            username (str): Username provided by the user.
            password (str): Password provided by the user.

        Returns:
            dict or None: User object if authentication succeeds,
            otherwise None.
        """
        for user in self.users:
            if user["username"] == username:
                try:
                    if self.hasher.verify(user["password"], password):
                        
                        # Rehash password if hashing parameters have changed.
                        if self.hasher.check_needs_rehash(user["password"]):
                            user["password"] = self.hasher.hash(password)
                            self.save_users()
                            
                        return user 

                except Exception:
                    # Verification failed (incorrect password or invalid hash)
                    continue

        return None 


    def add_user(self, username, password, role="user"):
        """
        Creates and stores a new user in the database.

        Ensures usernames are unique and stores the password securely
        as an Argon2 hash.

        Args:
            username (str): Username of the new user.
            password (str): Password of the new user.
            role (str, optional): Role assigned to the user. (default: 'user')

        Raises:
            ValueError: If the username already exists.
        """
        if any(user["username"] == username for user in self.users):
            raise ValueError("Username already exists")
        
        new_user = {
            "username": username,
            "password": self._hash_password(password),
            "role": role,
            "created_at": datetime.now().isoformat()
        }

        self.users.append(new_user)
        self.save_users()


    def _hash_password(self, password: str):
        """
        Hash a password using the Argon2 hashing algorithm.

        Args:
            password (str): The password to be hashed.

        Returns:
            str: The Argon2 hash of the new password.
        """
        return self.hasher.hash(password)