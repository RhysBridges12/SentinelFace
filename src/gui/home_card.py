"""
home_card.py

Defines a reusable card component for the home page.

Each card displays a title, description, image, and action button.
Used for performing core system functions and accessing the database.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QVBoxLayout
from PySide6.QtGui import QPixmap

from utils.ui_effects import apply_shadow

CARD_WIDTH = 220
CARD_HEIGHT = 300
MARGIN_SIZE = 16
BUTTON_MIN_HEIGHT = 40


class HomeCard(QFrame):
    """
    A GUI card displaying a title, description, image, and action button.
    """

    def __init__(self, title, description, button_text, image_path):
        """
        Initialises the home card component.

        Args:
            title (str): The card's title text.
            description (str): A text description displayed on the card.
            button_text (str): The label on the action button.
            image_path (str): The file path of the image displayed on the card.
        """
        super().__init__()

        # Set styling:
        self.setObjectName("card")

        self.setMinimumSize(CARD_WIDTH, CARD_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        layout.setSpacing(MARGIN_SIZE)

        # Title:
        title_lbl = QLabel(title)
        title_lbl.setProperty("class", "title")

        # Description:
        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setProperty("class", "secondary")
        desc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # Image display:
        self.image_lbl = QLabel()
        self.image_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_lbl.setAlignment(Qt.AlignCenter)

        self._pixmap = QPixmap(image_path) if image_path else QPixmap()
        if self._pixmap.isNull():
            self.image_lbl.setProperty("class", "secondary")
            self.image_lbl.setText("No Image")
        else:
            self._update_image()

        # Action button:
        self.button = QPushButton(button_text)
        self.button.setMinimumHeight(BUTTON_MIN_HEIGHT)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button.setObjectName("primaryButton")

        # Assemble home card:
        layout.addWidget(title_lbl, alignment=Qt.AlignLeft)
        layout.addWidget(desc_lbl)
        layout.addStretch(1)
        layout.addWidget(self.image_lbl, stretch=4)
        layout.addStretch(1)
        layout.addWidget(self.button)

        apply_shadow(self, radius=24, x_offset=0, y_offset=4, opacity=80)


    def _update_image(self):
        """
        Scale and update the displayed image to fit the label.
        """
        if self._pixmap.isNull():
            return
        
        size = self.image_lbl.size()
        # Scale image to fit label preserving its aspect ratio:
        scaled = self._pixmap.scaled(
            size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_lbl.setPixmap(scaled)


    def resizeEvent(self, event):
        """
        Handle resize events to update image scaling.
        
        Args:
            event: Resize event triggered when window size is changed.
        """
        super().resizeEvent(event)
        self._update_image()