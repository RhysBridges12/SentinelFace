"""
database_page.py

Defines the main database page used to display stored profiles through
the use of DatabaseCards. Profiles are retrieved from the profile manager.

Filters allow users to splice the displayed profiles based on specific criteria.

This page allows for searching by profile ID, filtering by date, image count and 
notes. There are controls for navigating the database (previous/next page).
The database is represented by a resizing grid layout of database cards.
"""
from datetime import datetime, timedelta

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QApplication, 
    QPushButton, QFrame, QScrollArea, QGridLayout, 
    QLineEdit, QComboBox, QCheckBox, QLabel
)

from database.profile import Profile
from utils.ui_effects import apply_shadow
from .database_card import DatabaseCard


# Constants used in formatting the database page.
MARGIN_SIZE = 16
FILTER_BAR_HEIGHT = 56
CARD_WIDTH = 220
CARD_HEIGHT = 280


MAX_PROFILES = 200 # Max profiles per page.
SEARCH_TIMER = 300 # Delay (ms) before triggering search.


class DatabasePage(QWidget):
    """
    A GUI page for browsing and managing profiles stored in the database.
    Accessible only by users with admin permissions.

    Provides filtering, searching, and navigation whilst displaying
    profiles as a grid of DatabaseCard widgets.
    """

    def __init__(self, main_window):
        """
        Initialises the database page and all GUI components.

        Args:
            main_window: The main application window with instance of profile manager.
        """
        super().__init__()

        self.main_window = main_window
        
        # Current page index:
        self.current_page = 0

        # Cache of created DatabaseCard widgets (keyed by profile ID).
        self.cards = {}

        # Main layout:
        layout = QVBoxLayout(self)
        layout.setSpacing(MARGIN_SIZE)

        # Filter Bar:
        self.filter_bar = QFrame()
        self.filter_bar.setObjectName("filterBar")
        self.filter_bar.setFixedHeight(FILTER_BAR_HEIGHT)

        filter_layout = QHBoxLayout(self.filter_bar)
        filter_layout.setContentsMargins(MARGIN_SIZE, 0, MARGIN_SIZE, 0)

        # Search box for inputs when filtering database cards:
        self.search_box = QLineEdit()
        self.search_box.setObjectName("noteEditor")
        self.search_box.setPlaceholderText("Search profile ID...")
        self.search_box.textChanged.connect(self._delay_search)
        
        # Select whether filtering uses creation or update date
        self.date_type = QComboBox()
        self.date_type.setObjectName("noteEditor")
        self.date_type.addItems(["Created", "Updated"])
        self.date_type.currentIndexChanged.connect(self._reset_and_display)

        # Time range filter options:
        self.date_range = QComboBox()
        self.date_range.setObjectName("noteEditor")
        self.date_range.addItems([
            "Any time",
            "Today",
            "This week",
            "This month"
        ])
        self.date_range.currentIndexChanged.connect(self._reset_and_display)

        # Filter based on number of images in a profile:
        self.image_filter = QComboBox()
        self.image_filter.setObjectName("noteEditor")
        self.image_filter.addItems([
            "Any images",
            "1 image",
            "2–4 images",
            "5+ images"
        ])
        self.image_filter.currentIndexChanged.connect(self._reset_and_display)

        # Filter profiles that do or don't contain notes:
        self.has_notes = QCheckBox("Has notes")
        self.has_notes.stateChanged.connect(self._reset_and_display)

        self.no_notes = QCheckBox("No notes")
        self.no_notes.stateChanged.connect(self._reset_and_display)
        
        # Toggle reverse ordering of profiles:
        self.reverse_order = QCheckBox("Reverse order")
        self.reverse_order.stateChanged.connect(self._reset_and_display)
        
        # Assemble the filter bar:
        filter_layout.addWidget(self.search_box)
        filter_layout.addWidget(self.date_type)
        filter_layout.addWidget(self.date_range)
        filter_layout.addWidget(self.image_filter)
        filter_layout.addWidget(self.has_notes)
        filter_layout.addWidget(self.no_notes)
        filter_layout.addWidget(self.reverse_order)
        filter_layout.addStretch()
        
        # Timer to delay search updates when typing:
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.display_profiles)

        apply_shadow(self.filter_bar, radius=16, y_offset=2, opacity=40)

        layout.addWidget(self.filter_bar)
    
        # Page controls:
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.setObjectName("primaryButton")
        self.prev_btn.clicked.connect(self.prev_page)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("primaryButton")
        self.next_btn.clicked.connect(self.next_page)
        
        # Label displaying current page number:
        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setProperty("class", "secondary")

        nav = QHBoxLayout()
        nav.addStretch()
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.page_label)
        nav.addWidget(self.next_btn)
        nav.addStretch()

        layout.addLayout(nav)

        # Scroll area for displaying DatabaseCards:
        self.scroll = QScrollArea()
        self.scroll.setObjectName("dbScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        # Container for the a grid of cards:
        self.cards_container = QWidget()
        self.cards_container.setObjectName("dbCardsContainer")

        # Grid layout used to position profile cards:
        self.grid = QGridLayout(self.cards_container)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.grid.setSpacing(MARGIN_SIZE)
        self.grid.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)

        self.scroll.setWidget(self.cards_container)
        layout.addWidget(self.scroll)
        layout.addLayout(nav)
    
    
    def next_page(self):
        """
        Displays the next page of profiles if available.
        Tracks and updates the current page number.
        """
        profiles = self._get_filtered_profiles()

        # Calculate number of pages needed:
        max_page = max(0, (len(profiles) - 1) // MAX_PROFILES)

        if self.current_page < max_page:
            self.current_page += 1
            self.display_profiles()


    def prev_page(self):
        """
        Displays to the previous page of profiles if available.
        Tracks and updates the current page number.
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.display_profiles()
    
    
    def _create_cards(self, profiles):
        """
        Create DatabaseCard widgets for all profiles that do not
        have a card object attached already.
        
        Args:
            profiles (list): A list of every profile in the database.
        """
        for profile in profiles:
            if profile.person_id not in self.cards:
                card = DatabaseCard(profile)
                card.request_view.connect(self.view_profile) # Connect button.
                card.setFixedSize(CARD_WIDTH, CARD_HEIGHT)

                self.cards[profile.person_id] = card
            
            
    def _clear_grid(self):
        """
        Removes all DatabaseCard widgets from the grid layout by hiding them.
        """
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().hide() # Less computationally expensive than deleting.
                      
            
    def _show_cards(self, profiles):  
        """
        Display profile cards in the grid layout.

        The number of columns is determined dynamically based on
        available width from the window size.
        
        Args:
            profiles (list): A list of every profile in the database.
        """
        grid_rect = self.scroll.viewport().contentsRect()
        margins = self.grid.contentsMargins()

        # Calculate available space and how many cards can fit: 
        usable_width = grid_rect.width() - margins.left() - margins.right()
        columns = max(1, usable_width // (CARD_WIDTH + self.grid.spacing()))

        row = col = 0
        # Place each card in the grid row by row:
        for profile in profiles:
            card = self.cards[profile.person_id]

            self.grid.addWidget(card, row, col)
            
            card.show()
            card.load_image()

            col += 1
            if col >= columns:
                col = 0 # Reset columns each time row is finished.
                row += 1


    def _delay_search(self):
        """
        Delays search execution to avoid updates each time a change
        is detected in the search box.
        
        Called every time a user types in the filter bar search box.
        """
        self.search_timer.start(SEARCH_TIMER)


    def _filter_by_date(self, profiles):
        """
        Filters profiles based on selected date type and range.
        
        Args:
            profiles (list): A list of every profile in the database.
        """
        range_option = self.date_range.currentText()

        # All profiles:
        if range_option == "Any time":
            return profiles

        now = datetime.now()

        if range_option == "Today": 
            cutoff = now - timedelta(days=1) # 1 Day.
        elif range_option == "This week":
            cutoff = now - timedelta(days=7) # 1 Week.
        else:
            cutoff = now - timedelta(days=30) # 1 Month.

        # Use created or updated date based on user choice:        
        attr = "created_at" if self.date_type.currentText() == "Created" else "updated_at"

        return [
            p for p in profiles
            if getattr(p, attr) is not None and getattr(p, attr) >= cutoff
        ]
    
    
    def _filter_by_image_count(self, profiles):
        """
        Filters profiles based on the number of images in the profile.
        
        Args:
            profiles (list): A list of every profile in the database.
        """
        img_filter = self.image_filter.currentText()

        if img_filter == "1 image":
            return [p for p in profiles if len(p.image_paths or []) == 1] # 1 image.

        if img_filter == "2–4 images":
            return [p for p in profiles if 2 <= len(p.image_paths or []) <= 4] # 2-4 images.

        if img_filter == "5+ images":
            return [p for p in profiles if len(p.image_paths or []) >= 5] # 5+ images.

        return profiles
    
    
    def _filter_by_notes(self, profiles):
        """
        Filters profiles based on whether they contain notes or not.
        
        Args:
            profiles (list): A list of every profile in the database.
        """
        has_notes = self.has_notes.isChecked()
        no_notes = self.no_notes.isChecked()

        if has_notes and not no_notes:
            return [p for p in profiles if p.notes] # Has got notes.

        if no_notes and not has_notes:
            return [p for p in profiles if not p.notes] # Doesnt have notes.

        return profiles


    def _get_filtered_profiles(self):
        """
        Retrieves all profiles and apply active search and filter options.
        """
        profiles = list(self.main_window.profile_manager.profiles.values())

        search = self.search_box.text().strip().lower() # User input.

        if search:
            profiles = [p for p in profiles if search in p.person_id.lower()]

        profiles = self._filter_by_date(profiles)
        profiles = self._filter_by_image_count(profiles)
        profiles = self._filter_by_notes(profiles)

        return profiles
    
    
    def _update_nav_buttons(self, profiles):
        """
        Updates the page controls and display current page information.
        
        Args:
            profiles (list): A list of every profile in the database.
        """
        # Calculate number of pages needed:
        total = len(profiles)
        max_page = max(0, (len(profiles) - 1) // MAX_PROFILES)

        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < max_page)
        
        self.page_label.setText(
            f"Page {self.current_page + 1} / {max_page + 1}"
        )
    
    
    def _reset_and_display(self):
        """
        Reset to the first page and refresh displayed profiles.
        """
        self.current_page = 0
        self.display_profiles()


    def display_profiles(self):
        """
        Display profiles using current page number and filters.
        
        Gets the list of profiles to be displayed, splices the list
        based on page number, creates the DatabaseCard items, updates
        the navigation buttons and labels and then displays the cards.
        """
        profiles = self._get_filtered_profiles()

        if self.reverse_order.isChecked():
            profiles.reverse()
        
        # Splice profile based on current page number:
        start = self.current_page * MAX_PROFILES
        end = start + MAX_PROFILES
        page_profiles = profiles[start:end]

        self._create_cards(page_profiles)
        
        self._update_nav_buttons(profiles)
        
        self._clear_grid()
        self._show_cards(page_profiles)
        
        self.scroll.verticalScrollBar().setValue(0) # Start at top of page.

    
    def refresh_theme(self):
        """
        Refreshes the page to apply updated styling.
        Used when user changes between dark and light modes.
        """
        self.display_profiles()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


    def resizeEvent(self, event):
        """
        Handles window resize events by refreshing the layout.
        
        Args:
            event: Resize event triggered when window size is changed.
        """
        super().resizeEvent(event) # Ensures default resizing happens.
        QTimer.singleShot(0, self.display_profiles) # Update layout based on new window size.


    def view_profile(self, profile: Profile):
        """
        Handles a request to open a specific profile page.

        Args:
            profile (Profile): The profile the user wishes to display.
        """
        self.main_window.show_profile_page(profile)