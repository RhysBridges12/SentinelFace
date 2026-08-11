"""
help_page.py

Defines a dialog displaying help and user guidance.

Provides users with an overview of the system's functionality, including
enrolment, searching, similarity thresholds and notification meanings.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, 
    QFrame, QScrollArea, QWidget
)


# Constants used in formatting the help page:
PAGE_WIDTH = 560
PAGE_HEIGHT = 640
MARGIN_SIZE = 24


class HelpPage(QDialog):
    """
    Pop-up window providing system help and usage instructions.
    """

    def __init__(self, parent=None):
        """
        Initialises the help pop-up page.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        self.setObjectName("helpBackground")
        self.setWindowTitle("System Help")
        self.setMinimumSize(PAGE_WIDTH, PAGE_HEIGHT)

        # Main layout:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)

        # Main card container:
        card = QFrame()
        card.setObjectName("card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        card_layout.setSpacing(16)

        # Title:
        title = QLabel("Face Recognition System - Help")
        title.setObjectName("settingsTitle")
        title.setAlignment(Qt.AlignCenter)

        # Scrollable area:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setAlignment(Qt.AlignTop)
        scroll_layout.setSpacing(14)

        # Sections of text in the help page:
        scroll_layout.addWidget(self._create_section( # System overview.
            "System Overview",
            "This system allows users to enrol individuals, search for matches "
            "using facial recognition, and manage stored profiles."
        ))

        scroll_layout.addWidget(self._create_section( # Enrolling Individuals.
            "Enrolling Individuals",
            "1. Click 'Enrol Individual' on the home page.\n"
            "2. Select one or more images.\n"
            "3. The system will detect faces and compare them with existing profiles.\n"
            "4. High-confidence matches are automatically added.\n"
            "5. Uncertain matches will ask for confirmation."
        ))

        scroll_layout.addWidget(self._create_section( # Matching individuals.
            "Searching for Matches",
            "You can search the database using images or video files.\n"
            "Faces detected in the media will be compared against stored profiles.\n"
            "The system will then display potential matches ranked by similarity."
        ))

        scroll_layout.addWidget(self._create_section( # Similarity scores.
            "Managing Profiles",
            "Profiles contain stored images, notes, timestamps, and profile history.\n"
            "Images and notes can be added or removed depending on user permissions."
        ))
 
        scroll_layout.addWidget(self._create_section( # Notification colours.
            "Notification Colours",
            "Blue  → Information messages\n"
            "Green → Successful actions\n"
            "Orange → Warnings\n"
            "Red → Errors or failed actions"
        ))

        scroll_layout.addStretch()

        scroll.setWidget(container)

        # Assemble layout:
        card_layout.addWidget(title)
        card_layout.addWidget(scroll)

        main_layout.addWidget(card)


    def _create_section(self, title, text):
        """
        Creates a formatted help section to be displayed on the help page.

        Args:
            title (str): The new section header.
            text (str): The content for the new section.

        Returns:
            QFrame: A styled container with title and text.
        """
        container = QFrame()
        container.setObjectName("noteCard")

        layout = QVBoxLayout(container)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("settingsSectionLabel")

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setProperty("class", "secondary")
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(title_label)
        layout.addWidget(text_label)

        return container