"""
notification_panel.py

Defines a scrollable panel for displaying and managing system events.

Events are displayed using EventCard components, with support for
priority ordering, persistence, and dynamic updates.

Used on home and profile pages.
"""
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QScrollArea, QWidget
)

from gui.event_card import EventCard
from utils.notification_store import save_notification
from utils.ui_effects import apply_shadow


# Constants used in formatting the notification panel:
PANEL_WIDTH = 320
MARGIN_SIZE = 16
BUTTON_HEIGHT = 36
MAX_EVENTS = 150


class EventPanel(QFrame):
    """
    A scrollable panel for displaying system event cards.

    Supports priority events, with an optional action button, automatic 
    trimming and optional persistence of notifications.
    """

    def __init__(self, title_text, button_text=None, main_window=None):
        """
        Initialises the event panel with an optional button at the bottom.

        Args:
            title_text (str): Title displayed at the top of the notification panel.
            button_text (str, optional): The label for the optional action button.
            main_window: Reference to main window for current user context.
        """
        super().__init__()

        self.main_window = main_window
        self._events = []
        self._priority_count = 0 # Number of priority events kept at top of panel.

        # Apply stylesheet:
        self.setObjectName("eventPanel")
        self.setFixedWidth(PANEL_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        layout.setSpacing(MARGIN_SIZE)

        # Title:
        self.title_label = QLabel(title_text)
        self.title_label.setProperty("class", "title")

        # Create empty area in panel for notifications:
        self.event_area = QVBoxLayout()
        self.event_area.setSpacing(10)
        self.event_area.addStretch()

        container = QWidget()
        container.setLayout(self.event_area)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(container)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.scrollbar = self.scroll.verticalScrollBar()

        layout.addWidget(self.title_label)
        layout.addWidget(self.scroll, stretch=1)

        # Optional custom button at the bottom of the notification panel:
        self.action_btn = None
        if button_text:
            self.action_btn = QPushButton(button_text)
            self.action_btn.setMinimumHeight(BUTTON_HEIGHT)
            self.action_btn.setObjectName("primaryButton")
            layout.addWidget(self.action_btn)

        apply_shadow(self, radius=30, y_offset=6, opacity=60)


    def add_event(self, message, severity="info", timestamp=None, persist=True, action=None, lbl="Action"):
        """
        Add a new event to the notification panel.

        Args:
            message (str): Event message.
            severity (str): Severity level used for styling.
            timestamp (str, optional): ISO timestamp, defaults to current time.
            persist (bool): Whether to store the event, stores by default.
            action (callable, optional): Optional action for the event card button.
            lbl (str, optional): Optional label for the action button.

        Returns:
            EventCard: The created event card to be displayed.
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        self._events.append((message, severity, timestamp))

        # Trim oldest events if limit exceeded:
        if len(self._events) > MAX_EVENTS:
            self._events.pop(0) # Removes oldest event card first.

            last_index = self.event_area.count() - 2
            item = self.event_area.takeAt(last_index)

            if item and item.widget():
                widget = item.widget()

                # Decrease priority count if priority event is deleted/finished:
                if getattr(widget, "has_action", False):
                    self._priority_count = max(0, self._priority_count - 1)

                widget.deleteLater()

        stretch = None
        if self.event_area.count():
            stretch = self.event_area.takeAt(self.event_area.count() - 1)

        card = EventCard(timestamp, message, severity, action, lbl)

        # Insert event as a priority if action is present:
        if action is not None:
            self.event_area.insertWidget(0, card)
            self._priority_count += 1
        else:
            insert_index = self._priority_count
            self.event_area.insertWidget(insert_index, card)

        if stretch:
            self.event_area.addItem(stretch)

        self.scrollbar.setValue(0)

        # Persist event if enabled:
        if persist and self.main_window and self.main_window.current_user:
            save_notification(
                message,
                severity,
                username=self.main_window.current_user
            )

        return card


    def remove_event_card(self, card):
        """
        Remove a specific event card from the notification panel.
        
        Args:
            card (EventCard): The notification to be removed.
        """
        for i in range(self.event_area.count()):
            item = self.event_area.itemAt(i)
            widget = item.widget()

            if widget is card:
                self.event_area.takeAt(i)

                # Update priority count if notification has action:
                if getattr(widget, "has_action", False):
                    self._priority_count = max(0, self._priority_count - 1)

                widget.deleteLater()
                return


    def get_events(self):
        """
        Returns a copy of all stored events.
        """
        return list(self._events)


    def refresh_theme(self):
        """
        Reapply styling to the panel and all child event cards.
        Required when dynamic properties or theme settings change.
        """
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

        # Also resets all event cards:
        for i in range(self.event_area.count()):
            widget = self.event_area.itemAt(i).widget()
            if widget and hasattr(widget, "refresh_theme"):
                widget.refresh_theme()


    def clear(self):
        """
        Removes all event cards and resets the notification panel.
        """
        while self.event_area.count():
            item = self.event_area.takeAt(0)

            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._events.clear()
        self.event_area.addStretch() # So next event card added is spaced properly.