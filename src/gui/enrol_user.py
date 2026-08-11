"""
enrol_user.py

Provides a pop-up for creating new system users.

This file allows an authorised user to input a username, password, and role,
then submits the data to the user manager for validation and storage.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QMessageBox,
    QLineEdit, QPushButton, QComboBox
)

from utils.system_logger import write_log


class EnrolUser(QDialog):
    """
    A pop-up window for creating a new user account.
    """

    def __init__(self, user_manager, current_user):
        """
        Initialises the enrol user pop-up.

        Args:
            user_manager: The user manager handling all user operations.
            current_user (dict): The user performing the enrolment.
        """
        super().__init__()

        self.user_manager = user_manager
        self.current_user = current_user
        
        self.setWindowTitle("Create User")

        layout = QVBoxLayout(self)

        # Username input.
        layout.addWidget(QLabel("Username"))
        self.username = QLineEdit()
        layout.addWidget(self.username)

        # Password input: (Hidden: *****)
        layout.addWidget(QLabel("Password"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)

        # Role selection dropdown:
        layout.addWidget(QLabel("Role"))
        self.role = QComboBox()
        self.role.addItems(["user", "auditor", "admin"])
        layout.addWidget(self.role)

        # Create user button:
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_user)
        layout.addWidget(create_btn)


    def create_user(self):
        """
        Validates user input fields and attempts to create a new user account.

        Displays feedback messages based on success or failure, and logs 
        successful user creation events.
        """
        
        username = self.username.text().strip()
        password = self.password.text().strip()

        # Ensure required fields are provided:
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password required")
            return
        
        try:
            self.user_manager.add_user(
                username,
                password,
                self.role.currentText()
            )
            
            QMessageBox.information(self, "Success", "User created successfully.")
            self.accept()

            write_log(
                action="create_user",
                user=self.current_user["username"],
                role=self.current_user["role"],
                category="security",
                details={"new_user": username}
            )

        except ValueError as error:
            QMessageBox.warning(self, "Error", str(error))