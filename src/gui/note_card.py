"""
note_card.py

Defines a reusable GUI component representing a single note on the profile page.

Each note displays the author, timestamp, message and an optional delete button
visible to the author and users with admin permissions.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, 
    QLabel, QPushButton, QSizePolicy
)
from PySide6.QtGui import QIcon


# Constants used in formatting the note card:
MARGIN_SIZE = 12
MESSAGE_SIZE = 600
DEL_BTN_SIZE = 28


class NoteCard(QFrame):
    """
    A GUI card representing a single note on the profile page.

    Displays the note metadata and content, and provides a delete 
    button based on user permissions.
    """
    def __init__(self, text, current_user, current_role, delete_action=None):
        """
        Initialises a note card.
        
        Args:
            text (str): A string containing the author, timestamp and message content.
            current_user (str): The username of the current user.
            current_role (str): The role of the current user.
            delete_action (callable, optional): Function to run when delete is clicked.
        """
        super().__init__()

        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.text = text
        self.delete_action = delete_action

        self.setObjectName("noteCard")

        # Main layout:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)

        # Split note string into components: Author, timestamp and content.
        parts = [p.strip() for p in text.split(" , ")]
        if len(parts) >= 3:
            self.author = parts[0]
            self.timestamp = parts[1]
            self.content = " , ".join(parts[2:])          
        else:
            # If the note format is invalid:
            self.author = "Unknown"
            self.timestamp = ""
            self.content = text

        # Container for note text content:
        container = QVBoxLayout()

        # Note label: (author and timestamp)
        meta = QLabel(f"{self.author} • {self.timestamp}")
        meta.setObjectName("noteMeta")

        # Note message content:
        msg = QLabel(self.content)
        msg.setWordWrap(True)
        msg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        msg.setMaximumWidth(MESSAGE_SIZE)

        container.addWidget(meta)
        container.addWidget(msg)

        layout.addLayout(container)
        layout.addStretch()
            
        # Normalise user and role for comparison:
        user = (current_user or "").strip().lower()
        author = (self.author or "").strip().lower()
        role = (current_role or "").lower()

        # Show the delete button if user is author or has admin permissions:
        if user == author or role == "admin":     
            delete_btn = QPushButton()
            delete_btn.setObjectName("iconButton")
            delete_btn.setFixedSize(DEL_BTN_SIZE, DEL_BTN_SIZE)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setIcon(QIcon("images/icons/trash.png"))
            delete_btn.setIconSize(delete_btn.size())

            # Connect delete function:
            delete_btn.clicked.connect(self._on_delete)
            
            layout.addWidget(delete_btn)


    def refresh_theme(self):
        """
        Refreshes the page to apply updated styling.
        Used when user changes between dark and light modes.
        """
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


    def _on_delete(self):
        """
        Deletes the selected note.
        Ensures that the delete function exists.
        """
        if self.delete_action:
            self.delete_action(self.text)