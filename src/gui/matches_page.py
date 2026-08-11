"""
matches_page.py

Defines the matches page, responsible for displaying face match results.

Matches are displayed as a responsive grid of database cards, each showing
a detected match along with its similarity score. The layout dynamically
adjusts based on available screen width.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel,
    QScrollArea, QGridLayout
)

from .database_card import DatabaseCard


# Constants used in formatting the matches page.
CARD_WIDTH = 220
CARD_HEIGHT = 280
CARD_MARGIN = 16


class MatchesPage(QWidget):
    """
    A page for displaying matched profiles once a search has been performed.

    Presents matches as a grid of cards, where each card represents a matched 
    profile and its associated similarity score. The grid layout adapts
    dynamically when the window resizes.
    """

    def __init__(self, main_window):
        """
        Initialises a matches page to represent a search action.
        
        Args:
            main_window: Reference to the main application window.
        """
        super().__init__()
        
        self.main_window = main_window

        self.matches = []

        # Main layout:
        layout = QVBoxLayout(self)
        layout.setSpacing(CARD_MARGIN)

        # Scroll area for DatabaseCards:
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        # Container for grid of DatabaseCards:
        self.cards_container = QWidget()
        self.grid = QGridLayout(self.cards_container)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.grid.setSpacing(CARD_MARGIN)
        self.grid.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)

        # Tracks current number of columns to prevent unnecessary redraws:
        self.current_columns = 0

        self.scroll.setWidget(self.cards_container)
        layout.addWidget(self.scroll)


    def display_matches(self, matches):
        """
        Displays match results in the grid layout.

        Args:
            matches (list of tuples): [(profile, similarity_score), ...]
        """
        self.matches = [
            (profile, score)
            for profile, score in matches
            if score >= 0.40
        ]

        # Clear existing grid items:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # In the case of no matches:
        if not self.matches:
            label = QLabel("No matches found")
            label.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(label, 0, 0)
            return

        # Calculate available width inside scroll area:
        grid_rect = self.scroll.viewport().contentsRect()
        margins = self.grid.contentsMargins()

        usable_width = (
            grid_rect.width()
            - margins.left()
            - margins.right()
        )

        # Determine maximum number of columns that fit within available width:
        columns = max(1, usable_width // (CARD_WIDTH + self.grid.spacing()))

        self.current_columns = columns

        row = col = 0
        
        for profile, score in matches:
            card = DatabaseCard(profile, similarity_score=score)
            card.load_image()

            # Connect view button on card to profile page:
            card.request_view.connect(self.view_profile)

            card.setFixedSize(CARD_WIDTH, CARD_HEIGHT)

            self.grid.addWidget(card, row, col)

            col += 1
            if col >= columns:
                col = 0 # Reset columns each time row is finished.
                row += 1


    def resizeEvent(self, event):
        """
        Handles window resize events by recalculating the layout.
        
        Args:
            event: Resize event triggered when window size is changed.
        """
        super().resizeEvent(event)
        QTimer.singleShot(0, lambda: self.display_matches(self.matches))


    def view_profile(self, profile):
        """
        Navigates to the profile page for the selected match.
        
        Args:
            profile (Profile): The profile the user wishes to display.
        """
        self.main_window.show_profile_page(profile)