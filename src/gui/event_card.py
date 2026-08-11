"""
event_card.py

Defines a reusable GUI component for displaying system events.
Used inside the notification panels on the home and profile pages.

Each card displays a timestamp, message, and optional action button,
with multiple styling based on the severity level.
"""
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import( 
    QFrame, QLabel, QVBoxLayout, 
    QHBoxLayout, QPushButton
)


MARGIN_SIZE = 12


class EventCard(QFrame):
    """
    A GUI card representing a single system event.

    Displays a timestamp, message, and an optional action button.
    Styling is controlled via the severity property.
    """

    def __init__(self, timestamp, message, severity="info", action=None, lbl="Action"):
        """
        Initialises the event card to be placed in a notification panel.

        Args:
            timestamp (str): ISO-formatted timestamp string.
            message (str): The message to be displayed on the event card.
            severity (str): The severity level used for styling, default = "info".
            action (callable, optional): Function linked to the button, otherwise None.
            lbl (str, optional): A label for the action button, default = "Action".
        """
        super().__init__()
        
        self.setObjectName("eventCard")
        self.setProperty("severity", severity) # Defines styling via Qt stylesheet.
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        layout.setSpacing(4)

        # Parse timestamp, fallback to current time if invalid:
        try:
            event_time = datetime.fromisoformat(timestamp)
        except Exception:
            event_time = datetime.now()

        # Timestamp label:
        ts_label = QLabel(event_time.strftime("%d %b %Y • %H:%M"))
        ts_label.setObjectName("eventTimestamp")

        # User defined message:
        msg_label = QLabel(str(message))
        msg_label.setWordWrap(True)
        msg_label.setObjectName("eventMessage")

        # Assemble event card:
        layout.addWidget(ts_label)
        layout.addWidget(msg_label)
        
        self.has_action = action is not None
        
        # Add an optional action button:
        if action:
            action_row = QHBoxLayout()
            action_row.addStretch()

            self.action_btn = QPushButton(lbl)
            self.action_btn.clicked.connect(action)

            action_row.addWidget(self.action_btn)
            layout.addLayout(action_row)


    def refresh_theme(self):
        """
        Refreshes the page to apply updated styling.
        Required when dynamic properties or theme settings change.
        """
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()