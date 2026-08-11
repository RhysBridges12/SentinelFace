"""
settings_page.py

Defines the settings pop-up for configuring system preferences.

Allows users to update the theme, compute mode as well as batch size 
and confirmation when enrolling individuals. 

There are also buttons to log out and to add new users (for admins only).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QMessageBox, QComboBox, 
    QCheckBox, QPushButton, QFrame,
)

from processing.face_processor import reset_detector
from gui.enrol_user import EnrolUser
from utils.compute import set_compute_mode
from utils.settings_store import save_settings
from utils.ui_effects import apply_shadow


# Constants used in formatting the settings page:
PAGE_WIDTH = 560
PAGE_HEIGHT = 640
MARGIN_SIZE = 20
SPACING = 14
BUTTON_HEIGHT = 36


class SettingsPage(QDialog):
    """
    A pop-up for viewing and modifying the systems settings.

    Facilitates switching between light and dark mode, CPU and GPU mode,
    batch size during enrolment and confirmation upon enrolling a new individual.
    """

    def __init__(self, main_window):
        """
        Initialises the settings page.

        Args:
            main_window: Reference to the main application window.
        """
        super().__init__(main_window)
        
        self.main_window = main_window

        self.setWindowTitle("Settings")
        self.setModal(True)

        # Set dialog size relative to main window:
        self.setFixedSize(PAGE_WIDTH, PAGE_HEIGHT)

        root = QVBoxLayout(self)
        root.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        root.setSpacing(SPACING)

        # Main card container:
        card = QFrame()
        card.setObjectName("settingsCard")
        apply_shadow(card, radius=20, y_offset=4, opacity=50)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        card_layout.setSpacing(SPACING)

        # Title:
        title = QLabel("Settings")
        title.setObjectName("settingsTitle")

        # Theme:
        theme_lbl = QLabel("Theme")
        theme_lbl.setProperty("class", "section")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(
            self.main_window.settings["theme"]
        )

        # Compute mode:
        compute_lbl = QLabel("Compute Mode")
        compute_lbl.setProperty("class", "section")
        self.compute_combo = QComboBox()
        self.compute_combo.addItems(["auto", "cpu", "gpu"])
        self.compute_combo.setCurrentText(
            self.main_window.settings["compute_mode"]
        )

        # Confirmation on enrol:
        confirm_lbl = QLabel("Confirmation on Enrolment")
        confirm_lbl.setProperty("class", "section")
        self.confirm_enrol = QCheckBox("Enable confirmation")
        self.confirm_enrol.setChecked(
            self.main_window.settings["confirm_on_enrol"]
        )

        # Enrolment batch size:
        batch_lbl = QLabel("Batch Size")
        batch_lbl.setProperty("class", "section")
        self.batch_combo = QComboBox()
        self.batch_combo.addItems(["5", "10", "15", "20"])

        current_batch = str(self.main_window.settings["batch_size"])
        idx = self.batch_combo.findText(current_batch)
        if idx >= 0:
            self.batch_combo.setCurrentIndex(idx)

        btn_row = QHBoxLayout()
        
        # Logout button:
        logout_btn = QPushButton("Log Out")
        logout_btn.setObjectName("primaryButton")
        logout_btn.setFixedHeight(BUTTON_HEIGHT)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_clicked)
        
        # Add user button:
        self.add_user_btn = QPushButton("Add User")
        self.add_user_btn.setObjectName("primaryButton")
        self.add_user_btn.clicked.connect(self.add_user_clicked)
        
        # Apply settings button:
        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("primaryButton")
        apply_btn.setFixedHeight(BUTTON_HEIGHT)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.clicked.connect(self.apply_settings)

        # Assemble button row:
        btn_row.addWidget(logout_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.add_user_btn)
        btn_row.addStretch()
        btn_row.addWidget(apply_btn)

        # Assemble settings page:
        card_layout.addWidget(title)
        card_layout.addWidget(theme_lbl)
        card_layout.addWidget(self.theme_combo)
        card_layout.addWidget(compute_lbl)
        card_layout.addWidget(self.compute_combo)
        card_layout.addWidget(confirm_lbl)
        card_layout.addWidget(self.confirm_enrol)
        card_layout.addWidget(batch_lbl)
        card_layout.addWidget(self.batch_combo)
        card_layout.addLayout(btn_row)

        # Only show add user option for admin users:
        if self.main_window.current_role != "admin":
            self.add_user_btn.hide()
            
        root.addWidget(card)


    def logout_clicked(self):
        """
        Handles user logout after confirmation.
        """
        reply = QMessageBox.question(
            self,
            "Log Out",
            "Are you sure you want to log out?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.main_window.logout()
            self.accept()


    def apply_settings(self):
        """
        Applies selected settings and persists them to storage.
        """
        # Update theme:
        theme = self.theme_combo.currentText()
        self.main_window.settings["theme"] = theme
        self.main_window.toggle_theme(theme)

        # Update compute mode:
        mode = self.compute_combo.currentText()
        self.main_window.settings["compute_mode"] = mode
        set_compute_mode(mode)
        reset_detector()

        # Update confirmation on enrolment:
        self.main_window.settings["confirm_on_enrol"] = (
            self.confirm_enrol.isChecked()
        )
        
        # Update batch size on enrolment:
        self.main_window.settings["batch_size"] = int(
            self.batch_combo.currentText()
        )

        # Persist settings:
        save_settings(self.main_window.settings)
        self.accept()


    def add_user_clicked(self):
        """
        Opens the enrol user page for creating a new user.
        """
        dialog = EnrolUser(
            self.main_window.user_manager,
            self.main_window.current_user
        )
        dialog.exec()