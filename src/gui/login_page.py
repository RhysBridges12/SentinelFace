"""
login_page.py

Defines the login page responsible for authenticating users.

This page provides input fields for username and password, validates credentials
via the user manager and routes users to the home page upon successful login.

Login attempts are logged using the system logger.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFrame
)
from PySide6.QtGui import QPixmap

from utils.ui_effects import apply_shadow
from utils.system_logger import write_log


# Constants for formatting the login page:
LOGO_SIZE = 240
CARD_WIDTH = 400
MARGIN_SIZE = 30
BOX_HEIGHT = 38


class LoginPage(QWidget):
    """
    GUI page for user authentication.

    Allows users to:
    - Enter username and password
    - Submit credentials for verification
    - Receive feedback on login status

    Successful logins initialise user session data and navigate to the home page.
    All login attempts are recorded in the system logs.
    """

    def __init__(self, main_window):
        """
        Initialises the login page upon loading.
        
        Args:
            main_window: Reference to the main application window.
        """
        super().__init__()

        self.main_window = main_window

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)
        root.setSpacing(20)

        # System logo:
        logo = QLabel()
        pix = QPixmap("images/icons/logo.png")

        # Load and scale logo:
        if not pix.isNull():
            logo.setPixmap(
                pix.scaled(
                    LOGO_SIZE,
                    LOGO_SIZE,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        logo.setAlignment(Qt.AlignCenter)

        # Container for input boxes and labels:
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(CARD_WIDTH)

        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(MARGIN_SIZE , MARGIN_SIZE , MARGIN_SIZE , MARGIN_SIZE )

        # Username label:
        user_label = QLabel("Username")
        user_label.setProperty("class", "title")

        # Username input:
        self.username_input = QLineEdit()
        self.username_input.setObjectName("noteEditor")
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setFixedHeight(BOX_HEIGHT)

        # Password label:
        pass_label = QLabel("Password")
        pass_label.setProperty("class", "title")

        # Password input: (Hidden: *****)
        self.password_input = QLineEdit()
        self.password_input.setObjectName("noteEditor")
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(BOX_HEIGHT)

        # Allows pressing enter to trigger login.
        self.password_input.returnPressed.connect(self.login_clicked)

        # Login button:
        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("primaryButton")
        self.login_btn.setFixedHeight(BOX_HEIGHT)

        self.login_btn.clicked.connect(self.login_clicked)
        
        # Message label for login feedback:
        self.message_label = QLabel("")
        self.message_label.setProperty("class", "loginError")
        self.message_label.setAlignment(Qt.AlignCenter)
        
        # Assemble login boxes:
        layout.addWidget(user_label)
        layout.addWidget(self.username_input)
        layout.addSpacing(6)
        layout.addWidget(pass_label)
        layout.addWidget(self.password_input)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn)

        # Assemble login page:
        root.addStretch()
        root.addWidget(logo, alignment=Qt.AlignCenter)
        root.addWidget(card, alignment=Qt.AlignCenter)
        root.addWidget(self.message_label, alignment=Qt.AlignCenter)
        root.addStretch()
        
        apply_shadow(card, radius=24, y_offset=4, opacity=45)
        

    def login_clicked(self):
        """
        Handles login attempts when the user submits username and password.

        Authenticates user via the user manager, progressing to the home page
        if successful or an error message if not.
        
        All login attempts, success or failure, are logged.
        """
        username = self.username_input.text()
        password = self.password_input.text()

        # Authenticate username and password with stored credientials:
        authenticated = self.main_window.user_manager.authenticate(username, password)

        if authenticated:
            # Store current session details:
            self.main_window.current_user = authenticated["username"]
            self.main_window.current_role = authenticated["role"]
            
            self.message_label.setText("")
            
            # Log successful login:
            write_log(
                action="login_success",
                user=authenticated["username"],
                role=authenticated["role"],
                category="authentication",
                details={"role": authenticated["role"]}
            )
               
            # Navigate to home page:
            self.main_window.show_home_page()
            
            self.main_window.home_page.notif_panel.add_event(
                f"{username} logged in successfully.",
                severity="info"
            )

        else:
            # Display error message:
            self.message_label.setText("Invalid username or password")
            
            # Log failed login attempt:
            write_log(
                action="login_failed",
                user=username,
                category="authentication"
            )