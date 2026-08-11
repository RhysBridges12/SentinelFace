"""
logs_page.py

Defines the logs page GUI, responsible for displaying the system logs 
stored within the system database.

This page loads logs from the system log file. Only the active log file 
is shown; archived logs are not included.

Logs are displayed in a scrollable list with filters that can be applied 
to search through them. The user can extract the current filtered logs 
using a button.
"""
import os
import json
import csv

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFileDialog,
    QHBoxLayout, QComboBox, QLineEdit, QPushButton, QFrame
)

from gui.log_card import LogCard


LOG_FILE = os.path.join("database", "system_logs.json")

# Constants used in formatting the database page:
MARGIN_SIZE = 16
SPACING = 20
FILTER_BAR_HEIGHT = 56
FILTER_HEIGHT = 38

REFRESH_TIMER = 10000 # Delay (ms) before updating GUI state.
SEARCH_TIMER = 300 # Delay (ms) before triggering search.
MAX_LOGS = 1000 # Maximum number of logs loaded into memory.
MAX_DISPLAY = 200 # Maximum number of logs displayed in the UI.


class LogsPage(QWidget):
    """
    Main GUI page for viewing, filtering, and exporting system logs.

    Provides functionality for searching, filtering, periodic updates,
    and exporting logs.
    """
    def __init__(self, main_window):
        """
        Initialises the logs page.
        
        Args:
            main_window: Reference to the main application window.
        """
        super().__init__()

        self.main_window = main_window

        # Stores all loaded logs, capped by MAX_LOGS:
        self.logs = []

        layout = QVBoxLayout(self)

        # Title:
        title = QLabel("System Logs")
        title.setProperty("class", "title")
        
        layout.addWidget(title)

        # Filter bar:
        self.filter_bar = QFrame()
        self.filter_bar.setObjectName("filterBar")
        self.filter_bar.setFixedHeight(FILTER_BAR_HEIGHT)

        filter_layout = QHBoxLayout(self.filter_bar)
        filter_layout.setContentsMargins(MARGIN_SIZE, 0, MARGIN_SIZE, 0)

        # Search input:
        self.search_box = QLineEdit()
        self.search_box.setObjectName("noteEditor")
        self.search_box.setPlaceholderText("Search logs...")
        self.search_box.textChanged.connect(self._delay_search)
        self.search_box.setFixedHeight(FILTER_HEIGHT)

        # Category filter dropdown:
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All",
            "authentication",
            "analytics",
            "database",
            "search",
            "security",
            "system"
        ])
        self.category_filter.currentIndexChanged.connect(self.display_logs)
        self.category_filter.setFixedHeight(FILTER_HEIGHT)
        
        # Timer to periodically refresh logs from database:
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_logs)
        self.refresh_timer.start(REFRESH_TIMER)

        # User filter dropdown:
        self.user_filter = QComboBox()
        self.user_filter.addItem("All")
        self.user_filter.currentIndexChanged.connect(self.display_logs)
        self.user_filter.setFixedHeight(FILTER_HEIGHT)

        # Assemble filter bar:
        filter_layout.addWidget(self.search_box)
        filter_layout.addSpacing(SPACING)
        filter_layout.addWidget(QLabel("Category"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addSpacing(SPACING)
        filter_layout.addWidget(QLabel("User"))
        filter_layout.addWidget(self.user_filter)
        filter_layout.addStretch()
        
        # Timer for updating logs page based on search box input:
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.display_logs)
        
        # Extract logs button:
        self.extract_btn = QPushButton("Extract Logs")
        self.extract_btn.setObjectName("primaryButton")
        self.extract_btn.clicked.connect(self.extract_logs)
        filter_layout.addWidget(self.extract_btn)
        filter_layout.addSpacing(SPACING)
        
        layout.addWidget(self.filter_bar)
        
        # Scrollable area for log cards:
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        # Label shown while logs are loading:
        self.loading_label = QLabel("Loading logs...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setProperty("class", "secondary")

        layout.addWidget(self.loading_label)
        
        # Container holding all log cards:
        self.container = QWidget()
        
        self.logs_layout = QVBoxLayout(self.container)
        self.logs_layout.setSpacing(SPACING)
        self.logs_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.container)

        layout.addWidget(self.scroll)
        

    def load_logs(self):
        """
        Loads logs from a JSON file and updates GUI's state.
        
        This skips loading if a widget is not visible, limits logs to MAX_LOGS, updates
        the user filter dropdown dynamically and shows/hides loading label.
        """
        if not self.isVisible():
            return

        if not os.path.exists(LOG_FILE):
            return
        
        self.loading_label.show()
        
        with open(LOG_FILE, "r") as f:
            all_logs = json.load(f)
            
        # Keep only the most recent logs:
        self.logs = all_logs[-MAX_LOGS:] 

        # Extract all unique users who appear in logs:
        users = sorted({
            log.get("user")
            for log in self.logs
            if log.get("user")
        })
        
        current_user = self.user_filter.currentText()

        # Rebuild user filter without triggering signals
        self.user_filter.blockSignals(True)
        self.user_filter.clear()
        self.user_filter.addItem("All")

        for user in users:
            self.user_filter.addItem(user)
            
        # Restore previously selected user if still available
        index = self.user_filter.findText(current_user)
        if index != -1:
            self.user_filter.setCurrentIndex(index)

        self.user_filter.blockSignals(False)
        
        self.loading_label.hide()
        self.display_logs()


    def display_logs(self):
        """
        Filters and renders logs based on the search box, categories
        and users involved in the logs.

        The existing log cards are cleared before repopulating the page.
        """
        # Clear existing log cards
        while self.logs_layout.count():
            item = self.logs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Stores logs that pass all active filters:
        self.filtered_logs = []

        search = self.search_box.text().lower()
        category = self.category_filter.currentText()
        user = self.user_filter.currentText()

        # Iterate over most recent logs first
        for log in reversed(self.logs[:MAX_DISPLAY]):
            if category != "All" and log.get("category") != category:
                continue

            if user != "All" and log.get("user") != user:
                continue

            # Combine searchable fields into one string:
            searchable = (
                f"{log.get('timestamp','')} "
                f"{log.get('category','')} "
                f"{log.get('action','')} "
                f"{log.get('user','')} "
                f"{log.get('role','')}"
            ).lower()
                           
            # Apply text search filter:
            if search and search not in searchable:
                continue

            self.filtered_logs.append(log) # Logs available for exporting.

            # Adds a log card to the page:
            card = LogCard(log)
            self.logs_layout.addWidget(card)

        self.logs_layout.addStretch()
        
        
    def extract_logs(self):
        """
        Exports currently filtered logs to a user-selected file.

        Supports extracting to a JSON for the full data, or CSV files
        for selected fields only.
        """
        if not self.filtered_logs:
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            "system_logs_export",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )

        if not file_path:
            return

        # Export as JSON:
        if file_path.endswith(".json"):

            with open(file_path, "w") as f:
                json.dump(self.filtered_logs, f, indent=2)

        # Export as CSV:
        elif file_path.endswith(".csv"):

            keys = ["timestamp", "category", "action", "user", "role"]

            with open(file_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                
                for log in self.filtered_logs:
                    writer.writerow({
                        "timestamp": log.get("timestamp"),
                        "category": log.get("category"),
                        "action": log.get("action"),
                        "user": log.get("user"),
                        "role": log.get("role")
                    })
                    
    def _delay_search(self):
        """
        Delays search execution to avoid updates each time a change
        is detected in the search box.
        
        Called every time a user types in the filter bar search box.
        """
        self.search_timer.start(SEARCH_TIMER)