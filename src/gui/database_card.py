"""
database_card.py

Defines a reusable UI component representing a single profile in the database page.
This is also used on the matches page to represent a match.

Each card displays:
- The profile ID,
- A preview image (thumbnail),
- Creation and last-updated timestamps,
- An optional similarity score (used during searches),
- A button to view the profiles page.

A signal is emitted when the user requests to view the profile.
"""

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QVBoxLayout
from PySide6.QtGui import QPixmap

from utils.ui_effects import apply_shadow
from database.profile import Profile


IMAGE_SIZE = 96 # Size of the profile preview image.
CARD_MARGIN = 16 # Padding and spacing within the card layout.
BUTTON_HEIGHT = 36 # Height of the view buttons.


class DatabaseCard(QFrame):
    """
    A GUI card representing a single profile in the database.

    Displays profile metadata and a preview image, and allows the user
    to view the full profile via a button.
    
    Signals:
        request_view (Profile): Emits when view button pressed.
    """

    # Signal emitted when a view button is clicked.
    # Sends a profile to be displayed on a profile page.
    request_view = Signal(Profile)


    def __init__(self, profile: Profile, similarity_score=None):
        """
        Initialises a database card representing a specific profile.
        A similarity score label is added if one has been parsed in. 

        Args:
            profile (Profile): The profile to be displayed.
            similarity_score (float, optional): Optional displayed similarity score
        """
        super().__init__()

        self.profile = profile
        self.similarity_score = similarity_score

        # Apply stylesheet and fixed sizing behaviour:
        self.setObjectName("dbcard")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        layout.setSpacing(CARD_MARGIN)
        layout.setAlignment(Qt.AlignTop)


        # Title:
        title = QLabel(str(profile.person_id))
        title.setProperty("class", "title")

        # Image:
        self.image_label = QLabel()
        self.image_label.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
        self.image_label.setAlignment(Qt.AlignCenter)

        # Placeholder text until image is loaded:
        if profile.image_paths:
            self.image_label.setText("Loading...")
        else:
            self.image_label.setText("No image")

        # Area for metadata to be displayed on card:
        dates_layout = QVBoxLayout()
        dates_layout.setSpacing(2)

        # Similarity score label:
        if self.similarity_score is not None:
            score_lbl = QLabel(
                f"Similarity: {self.similarity_score:.2%}"
            )
            score_lbl.setProperty("class", "score")
            dates_layout.addWidget(score_lbl)

        # Timestamp labels:
        created_dt = profile.created_at or datetime.now()
        created = QLabel(
            f"Created: {created_dt.strftime('%d %b %Y • %H:%M')}"
        )
        created.setProperty("class", "secondary")
        
        updated_dt = profile.updated_at or created_dt
        updated = QLabel(
            f"Updated: {updated_dt.strftime('%d %b %Y • %H:%M')}"
        )
        updated.setProperty("class", "secondary")

        dates_layout.addWidget(created)
        dates_layout.addWidget(updated)

        # Button for viewing profile:
        self.view_btn = QPushButton("View")
        self.view_btn.setFixedHeight(BUTTON_HEIGHT)
        self.view_btn.setCursor(Qt.PointingHandCursor)
        self.view_btn.setObjectName("primaryButton")

        # Connect function to view button press:
        self.view_btn.clicked.connect(self.view_clicked)

        # Assemble database card:
        layout.addWidget(title)
        layout.addSpacing(2)
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        layout.addLayout(dates_layout)
        layout.addStretch()
        layout.addWidget(self.view_btn)

        apply_shadow(self, radius=18, y_offset=4, opacity=40)


    def load_image(self):
        """
        Lazily load and display the profile's first image.

        This prevents unnecessary image loading during initial UI rendering.
        """
        # Check profile has images:
        if not self.profile.image_paths:
            return

        # Skip if image is already loaded:
        if self.image_label.pixmap() and not self.image_label.pixmap().isNull():
            return

        # Use first image in profile as thumbnail:
        path = self.profile.image_paths[0]

        pixmap = QPixmap(path)
        if not pixmap.isNull():
            # Scale image while preserving aspect ratio:
            pixmap = pixmap.scaled(
                IMAGE_SIZE,
                IMAGE_SIZE,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)


    def view_clicked(self):
        """
        Requests a profile page to be displayed once the view button
        is pressed.

        Emits:
            request_view (Profile): The profile the user wishes to view.
        """
        self.request_view.emit(self.profile)