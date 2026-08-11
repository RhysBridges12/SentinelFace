"""
home_page.py

Defines the main home page layout of the system.
This page is displayed upon successfully logging into the system.

Displays core navigation cards alongside a notification panel,
providing quick access to key features and system events.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy

from .home_card import HomeCard
from .notification_panel import EventPanel


CARD_SPACING = 16


class HomePage(QWidget):
    """
    Main home page displaying navigation cards and user-specific notifications.
    """

    def __init__(self, main_window):
        """
        Initialises the home page layout.

        Args:
            main_window: Reference to the main application window.
        """
        super().__init__()

        self.main_window = main_window
    
        # Main layout:
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setSpacing(CARD_SPACING)

        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(CARD_SPACING)

        # Build action cards:
        self._build_cards()

        # Place cards inside container:
        cards_container = QWidget()
        cards_container.setLayout(self.cards_layout)
        cards_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_layout.addWidget(cards_container)
        
        # Build notification panel with system logs button:
        self.notif_panel = EventPanel(
            "Notifications",
            "System Logs",
            main_window=self.main_window
        )
        
        self.main_layout.addWidget(self.notif_panel)

        # Connect logs button if present:
        if self.notif_panel.action_btn:
            self.notif_panel.action_btn.clicked.connect(self.main_window.logs_clicked)


    def _build_cards(self):
        """
        Creates and configures the main navigation cards.
        """
        self.enrol_card = HomeCard(
            "Enrol Individual",
            "Add a new person to the face recognition database.",
            "Enrol",
            "images/icons/enrol.png"
        )

        self.db_card = HomeCard(
            "Access Database",
            "Browse and manage profiles inside the database.",
            "Open",
            "images/icons/database.png"
        )

        self.search_card = HomeCard(
            "Search for Matches",
            "Identify a person using a reference image.",
            "Search",
            "images/icons/search.png"
        )

        self.cards_layout.addWidget(self.enrol_card, stretch=1)
        self.cards_layout.addWidget(self.db_card, stretch=1)
        self.cards_layout.addWidget(self.search_card, stretch=1)

        # Connect card buttons to functions:
        self.enrol_card.button.clicked.connect(self.main_window.enrol_clicked)
        self.db_card.button.clicked.connect(self.main_window.db_clicked)
        self.search_card.button.clicked.connect(self.main_window.search_clicked)


    def _build_notif_panel(self):
        """
        Rebuild the notification panel while preserving existing events.
        Used when refreshing the GUI (e.g. theme changes)
        """
        old_events = [] # Stores events to restore after building a new panel.

        if hasattr(self, "notif_panel") and self.notif_panel:
            old_events = self.notif_panel.get_events()
            self.main_layout.removeWidget(self.notif_panel)
            self.notif_panel.deleteLater()

        # Create new event panel:
        self.notif_panel = EventPanel(
            "Notifications",
            "System Logs",
            main_window=self.main_window
        )
        
        self.main_layout.addWidget(self.notif_panel)
        
        if self.notif_panel.action_btn:
            self.notif_panel.action_btn.clicked.connect(
                self.main_window.logs_clicked
            )

        # Restore previous events:
        for msg, sev, ts in old_events:
            self.notif_panel.add_event(msg, sev, ts)


    def refresh_theme(self):
        """
        Refresh the home page GUI to apply updated styling.
        Used when user changes between dark and light modes.
        """
        self._build_notif_panel()