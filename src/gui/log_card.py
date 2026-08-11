"""
log_card.py

Defines a GUI component for displaying individual system logs.

Each card displays metadata such as timestamp, action, user, and
additional details, with styling based on the logs category.
"""

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
)

from utils.ui_effects import apply_shadow


# Constants used in formatting the log cards:
MIN_CARD_WIDTH = 450
MAX_CARD_WIDTH = 560
MARGIN_SIZE = 16
SPACING = 6


class LogCard(QFrame):
    """
    A GUI card representing a single system log entry.
    Each log card has a colour strip denoting its category.
    """

    def __init__(self, log):
        """
        Initialises a log card:

        Args:
            log (dict): A log entry containing category, metadata and details.
        """
        super().__init__()

        category = log.get("category", "system")

        # Outer frame styled to show a colour strip:
        self.setObjectName("logCardStrip")
        self.setProperty("category", category)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setMinimumWidth(MIN_CARD_WIDTH)
        self.setMaximumWidth(MAX_CARD_WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        outer_layout = QHBoxLayout(self)
        # Offset to expose colour strip:
        outer_layout.setContentsMargins(0, 0, MARGIN_SIZE, 0)

        # Inner frame for log card content:
        card = QFrame()
        card.setObjectName("logCard")

        outer_layout.addWidget(card)

        # Container for log card content:
        layout = QVBoxLayout(card)
        layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        layout.setSpacing(SPACING)

        # Define metadata:
        timestamp = log.get("timestamp", "")
        action = log.get("action", "")
        user = log.get("user")
        role = log.get("role")

        # Format timestamp:
        try:
            dt = datetime.fromisoformat(timestamp)
            date = dt.strftime("%d %b %Y")
            time = dt.strftime("%H:%M:%S")
        except Exception:
            date = timestamp
            time = ""

        # Displays category and timestamp labels:
        top_row = QHBoxLayout()

        category_lbl = QLabel(category.upper())
        category_lbl.setProperty("class", "logHeading")

        date_lbl = QLabel(date)
        time_lbl = QLabel(time)

        right_time = QVBoxLayout()
        right_time.addWidget(date_lbl, alignment=Qt.AlignRight)
        right_time.addWidget(time_lbl, alignment=Qt.AlignRight)

        top_row.addWidget(category_lbl)
        top_row.addStretch()
        top_row.addLayout(right_time)

        layout.addLayout(top_row)

        # Formats action label: (e.g. 'new_user' = 'New User')
        action_lbl = QLabel(action.replace("_", " ").title())
        action_lbl.setObjectName("logAction")
        action_lbl.setProperty("class", "logHeading")

        layout.addWidget(action_lbl)

        # User related to the log action:
        if user:
            user_lbl = QLabel(f"{user} ({role})" if role else user)
            layout.addWidget(user_lbl)

        # Additional log details:
        details = log.get("details", {})

        if details:
            info_title = QLabel("Info")
            info_title.setObjectName("logInfoTitle")
            layout.addWidget(info_title)

            for key, value in details.items():

                # Formatting for match results: (Displays person ID and score)
                if key == "matches":
                    for match in value:
                        pid = match.get("person_id")
                        score = match.get("score")
                        lbl = QLabel(f"{pid} ({score})")
                        layout.addWidget(lbl)

                else:
                    lbl = QLabel(f"{key}: {value}")
                    lbl.setWordWrap(True)
                    layout.addWidget(lbl)

        apply_shadow(self, radius=20, y_offset=4, opacity=45)