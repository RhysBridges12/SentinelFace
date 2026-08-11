"""
profile_page.py

Defines the profile page responsible for displaying an individual profile
within the system.

This page displays profile metadata (ID, timestamps, demographics), face images,
profile notes and a notification panel showing recent changes made to the profile.

Users can add and delete notes, remove images and view profile history.
"""
import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy,
    QLabel, QFrame, QTextEdit, QScrollArea, QMessageBox
)
from PySide6.QtGui import QFont, QPixmap

from database.profile import Profile
from .notification_panel import EventPanel
from .note_card import NoteCard
from .image_item import ImageItem
from utils.ui_effects import apply_shadow
from utils.notification_store import load_notifications, save_notification
from utils.system_logger import write_log


# Constants used in formatting the profile pages.
BUTTON_WIDTH = 120
BUTTON_HEIGHT = 40
MARGIN_SIZE = 16
SPACING = 8
IMAGE_PANEL_HEIGHT = 260 
IMAGE_SIZE = 220

MAX_IMAGES = 25 # Maximum number of images displayed per profile.
MAX_NOTE_CHARS = 200 # Maximum number of characters allowed in a note.


class ProfilePage(QWidget):
    """
    A GUI page for viewing and managing an individual profile.

    Displays profile metadata, images, notes, and a notification panel.
    Allows users to add/remove notes and delete images with the required
    permissions.
    """

    def __init__(self, main_window):
        """
        Initialises a profile page.
        
        Args:
            main_window: Reference to the main application window.
        """
        super().__init__()
        self.setObjectName("profilePage")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.main_window = main_window
        
        self.profile_manager = main_window.profile_manager

        self.profile = None
        
        # Main layout:
        root = QHBoxLayout(self)
        root.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        root.setSpacing(MARGIN_SIZE)

        # Area for profile metadata, images and notes:
        left_col = QVBoxLayout()
        left_col.setSpacing(MARGIN_SIZE)

        # Displays profile metadata: (ID, timestamps, demographics)
        self.header = QFrame()
        self.header.setObjectName("profileHeader")
        self.header.setAttribute(Qt.WA_StyledBackground, True)
        apply_shadow(self.header, radius=20, y_offset=2, opacity=40)

        self.header_layout = QVBoxLayout(self.header)
        self.header_layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)

        # Text labels:
        self.title_lbl = QLabel("Profile")
        title_font = QFont()
        title_font.setPointSize(MARGIN_SIZE)
        title_font.setWeight(QFont.DemiBold)
        self.title_lbl.setFont(title_font)

        self.created_label = QLabel()
        self.created_label.setProperty("class", "secondary")
        
        self.updated_label = QLabel()
        self.updated_label.setProperty("class", "secondary")
        
        self.age_label = QLabel()
        self.age_label.setProperty("class", "secondary")
        
        self.gender_label = QLabel()
        self.gender_label.setProperty("class", "secondary")

        # Assemble profile header:
        self.header_layout.addWidget(self.title_lbl)
        self.header_layout.addWidget(self.created_label)
        self.header_layout.addWidget(self.updated_label)
        self.header_layout.addWidget(self.age_label)
        self.header_layout.addWidget(self.gender_label)

        # Display profile images in a horizontal scrollable area:
        self.image_panel = QFrame()
        self.image_panel.setObjectName("profileImagePanel")
        self.image_panel.setAttribute(Qt.WA_StyledBackground, True)
        self.image_panel.setMinimumHeight(IMAGE_PANEL_HEIGHT)
        self.image_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        apply_shadow(self.image_panel, radius=24, y_offset=4, opacity=45)

        image_layout = QVBoxLayout(self.image_panel)
        image_layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)

        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.image_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_scroll.setFrameShape(QFrame.NoFrame)

        self.image_container = QWidget()
        self.image_row = QHBoxLayout(self.image_container)
        self.image_row.setSpacing(SPACING)
        self.image_row.setContentsMargins(SPACING, SPACING, SPACING, SPACING)

        self.image_scroll.setWidget(self.image_container)
        image_layout.addWidget(self.image_scroll)

        # Note area:
        self.notes_panel = QFrame()
        self.notes_panel.setObjectName("profileNotesPanel")
        self.notes_panel.setAttribute(Qt.WA_StyledBackground, True)
        self.notes_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        apply_shadow(self.notes_panel, radius=24, y_offset=4, opacity=45)
        
        notes_layout = QVBoxLayout(self.notes_panel)
        notes_layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        notes_layout.setSpacing(SPACING)

        # Notes title:
        self.notes_title = QLabel("Notes")
        notes_font = QFont()
        notes_font.setPointSize(12)
        notes_font.setWeight(QFont.DemiBold)
        self.notes_title.setFont(notes_font)

        self.notes_list = QVBoxLayout()
        self.notes_list.setSpacing(SPACING)
        self.notes_list.setContentsMargins(0, 0, 0, 0)

        # Input box for new notes:
        self.new_note_edit = QTextEdit()
        self.new_note_edit.setObjectName("noteEditor")
        self.new_note_edit.setPlaceholderText("Add a new note…")
        self.new_note_edit.setFixedHeight(80)

        # Character count label:
        self.char_count_lbl = QLabel("0 characters")
        self.char_count_lbl.setObjectName("noteCharCount")

        self.new_note_edit.textChanged.connect(self._update_char_count)

        # Button to add new note:
        self.add_note_btn = QPushButton("Add Note")
        self.add_note_btn.setObjectName("primaryButton")
        self.add_note_btn.setFixedWidth(BUTTON_WIDTH)
        self.add_note_btn.setFixedHeight(BUTTON_HEIGHT)
        self.add_note_btn.setCursor(Qt.PointingHandCursor)
        self.add_note_btn.clicked.connect(self._add_note)

        input_col = QVBoxLayout()
        input_col.setSpacing(SPACING)
        input_col.addWidget(self.new_note_edit)
        input_col.addWidget(self.char_count_lbl, alignment=Qt.AlignRight)

        input_row = QHBoxLayout()
        input_row.setSpacing(SPACING)
        input_row.addLayout(input_col)
        input_row.addWidget(self.add_note_btn)

        notes_layout.addWidget(self.notes_title)
        notes_layout.addLayout(input_row)
        notes_layout.addSpacing(SPACING)
        notes_layout.addLayout(self.notes_list)

        # Right panel for logs:
        self.log_panel = EventPanel("Change Log")
        
        # Assemble profile page:
        left_col.addWidget(self.header)
        left_col.addWidget(self.image_panel)
        left_col.addWidget(self.notes_panel)

        left_container = QWidget()
        left_container.setAttribute(Qt.WA_StyledBackground, True)
        left_container.setLayout(left_col)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setWidget(left_container)
        
        left_scroll.setObjectName("profileLeftScroll")
        left_scroll.viewport().setAttribute(Qt.WA_StyledBackground, True)
        left_scroll.viewport().setObjectName("profileLeftViewport")

        root.addWidget(left_scroll, stretch=1)
        root.addWidget(self.log_panel)
        
    
    def set_user_context(self):
        """
        Defines the current user accessing the profile page.
        """
        self.current_user = self.main_window.current_user
        self.current_role = self.main_window.current_role


    def refresh_theme(self):
        """
        Refreshes the page to apply updated styling.
        Used when user changes between dark and light modes.
        """
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

        # Redraw notification panel:
        if hasattr(self.log_panel, "refresh_theme"):
            self.log_panel.refresh_theme()

        for i in range(self.notes_list.count()):
            w = self.notes_list.itemAt(i).widget()
            if hasattr(w, "refresh_theme"):
                w.refresh_theme()

        if self.profile:
            self.set_profile(self.profile)


    def _refresh_dates(self):
        """
        Updates created and last-updated timestamps in the header.
        """
        if not self.profile:
            return

        created = self.profile.created_at
        updated = self.profile.updated_at

        self.created_label.setText(
            f"Created: {created.strftime('%d %b %Y • %H:%M')}"
        )

        self.updated_label.setText(
            f"Updated: {updated.strftime('%d %b %Y • %H:%M')}"
        )


    def set_profile(self, profile):
        """
        Loads and displays a profile within the page.

        Updates all GUI sections including metadata, images, notes, and change log.

        Args:
            profile (Profile): Profile to be displayed.
        """
        self.set_user_context()
        
        self.profile = profile

        self.title_lbl.setText(profile.person_id)
        self._refresh_dates()
        self._update_demographics()

        # Clear existing images before repopulating:
        self._clear_images()

        # Load profile images from image paths:
        if profile.image_paths:
            for img_path in profile.image_paths[:MAX_IMAGES]:
                img_lbl = ImageItem(
                    img_path,
                    delete_action=self._delete_image
                )
                self.image_row.addWidget(img_lbl)
                img_lbl.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
                img_lbl.setObjectName("profileImageThumb")
                img_lbl.setAlignment(Qt.AlignCenter)

                # Scale images keeping aspect ratio:
                pm = QPixmap(img_path)
                if not pm.isNull():
                    img_lbl.setPixmap(
                        pm.scaled(
                            img_lbl.size(),
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                    )
                else:
                    img_lbl.setText("Image not found")

                self.image_row.addWidget(img_lbl)

            self.image_row.addStretch()

        self._load_notes()

        # Clear and re populate change log:
        self.log_panel.clear()
        for notif in load_notifications(self._log_path()):
            self.log_panel.add_event(
                notif["message"],
                notif["severity"],
                notif["timestamp"],
                persist=False
            )
            

    def _load_notes(self):
        """
        Loads and displays all notes saved for the current profile.
        """
        # Clear all existing notes:
        while self.notes_list.count():
            item = self.notes_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Load notes from database and display them:
        notes = self.profile_manager.get_notes(self.profile.person_id)
        for note in reversed(notes):
            card = NoteCard(
                note,
                self.current_user,
                self.current_role,
                delete_action=self._delete_note
            )
            self.notes_list.addWidget(card)
            

    def _add_note(self):
        """
        Adds a new note to the current profile and updates the GUI.
        
        Called when the add note button is pressed.
        """
        if not self.profile:
            return
        
        # Create note metadata:
        author = self.current_user
        timestamp = datetime.now().strftime("%d %b %Y • %H:%M")

        text = self.new_note_edit.toPlainText().strip()
        if not text:
            return
        
        # Construct note entry string:
        note_entry = f"{author} , {timestamp} , {text}"

        # Add note to profile:
        self.profile_manager.add_note(
            self.profile.person_id,
            note_entry,
        )
        
        write_log(
            action="note_added",
            user=self.current_user,
            role=self.current_role,
            category="database",
            details={
                "person_id": self.profile.person_id,
                "note": text
            }
        )
        
        self._refresh_dates()
        self.main_window.database_page.display_profiles()

        # Insert new note at top of list:
        self.notes_list.insertWidget(
            0,
            NoteCard(
                note_entry,
                current_user=self.current_user,
                current_role=self.current_role,
                delete_action=self._delete_note
            )
        )

        self.new_note_edit.clear()
        self.char_count_lbl.setText(f"0/{MAX_NOTE_CHARS} characters")

        msg = f"Note added to {self.profile.person_id}"    
        save_notification(msg, "info", self._log_path())
        self.log_panel.add_event(msg, severity="info", persist=False)


    def _clear_images(self):
        """
        Removes all images from the image panel.
        Used when refreshing the profile page.
        """
        while self.image_row.count():
            item = self.image_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


    def _update_char_count(self):
        """
        Updates and enforces the character count (MAX_NOTE_CHARS) for a note input.
        """
        text = self.new_note_edit.toPlainText()

        if len(text) > MAX_NOTE_CHARS:
            cursor = self.new_note_edit.textCursor()
            pos = cursor.position()

            # Dont allow user to pass note count:
            text = text[: MAX_NOTE_CHARS]
            self.new_note_edit.blockSignals(True)
            self.new_note_edit.setPlainText(text)

            cursor.setPosition(min(pos, MAX_NOTE_CHARS))
            self.new_note_edit.setTextCursor(cursor)
            self.new_note_edit.blockSignals(False)
        
        # Update character count label:
        count = len(text)
        self.char_count_lbl.setText(
            f"{count}/{MAX_NOTE_CHARS} characters"
        )
       

    def _update_demographics(self):
        """
        Calculates and displays estimated age range and gender.
        
        Uses data from each input image to make a label for each metric.
        """
        if not self.profile:
            return

        ages = []
        genders = []

        for img in self.profile.image_paths:
            meta = self.profile.metadata.get(img)
            if not meta:
                continue
            
            # Attempt to get predicted image metadata:
            age = meta.get("age")
            gender = meta.get("gender")

            if age is not None:
                ages.append(age)

            if gender is not None:
                genders.append(gender)

        if ages:
            age_min = min(ages)
            age_max = max(ages)
            # Create age range label:
            self.age_label.setText(f"Estimated age: {age_min}–{age_max}")
        else:
            self.age_label.setText("Estimated age: Unknown")

        if genders:
            majority = max(set(genders), key=genders.count)
            # Use most commonly found gender as estimate:
            self.gender_label.setText(f"Estimated gender: {majority.capitalize()}")
        else:
            self.gender_label.setText("Estimated gender: Unknown")
            

    def _delete_image(self, img_path):
        """
        Deletes an image from the profile page, active memory and disk.
        Refreshes the profile page.
        
        This function is called upon the pressing of delete on an ImageItem object.
        """
        if not self.profile:
            return

        # Ask user for confirmation of deletion:
        reply = QMessageBox.question(
            self,
            "Delete Image",
            "Are you sure you want to delete this image?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Remove from active memory:
        self.profile_manager.remove_image(self.profile.person_id, img_path)

        # Remove from database folder:
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                print(f"Failed to delete file: {e}")
        
        # Log image deletion:
        msg = f"Image removed from {self.profile.person_id}"
        save_notification(msg, "info", self._log_path())
        self.log_panel.add_event(msg, severity="info", persist=False)

        self.profile.updated_at = datetime.now()
        self._refresh_dates()

        # Refresh profile page:
        self.set_profile(self.profile)


    def _delete_note(self, note_text: str):
        """
        Deletes a note from the profile and refreshes the profile page.
        
        This function is called upon the pressing of delete on a NoteCard object.
        """
        if not self.profile:
            return

        # Ask user for confirmation of deletion:
        reply = QMessageBox.question(
            self,
            "Delete Note",
            "Are you sure you want to delete this note?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        notes = self.profile_manager.get_notes(self.profile.person_id)
        notes = [n.strip() for n in notes]
        
        # Attempt to remove the note:
        try:
            notes.remove(note_text.strip())
        except ValueError:
            return

        self.profile_manager.replace_notes(self.profile.person_id, notes)
        
        # Log note deletion:
        msg = f"Note deleted from {self.profile.person_id}"
        save_notification(msg, "info", self._log_path())
        self.log_panel.add_event(msg, severity="info", persist=False)
        
        self.profile.updated_at = datetime.now()
        self._refresh_dates()

        self._load_notes()
        
        
    def _log_path(self):
        """
        Returns the file path for the current profile pages change log.
        """
        folder = os.path.join("database", "profile_logs")
        os.makedirs(folder, exist_ok=True)
        
        return os.path.join(folder, f"{self.profile.person_id}.json")


    def wheelEvent(self, event):
        """
        Enables horizontal scrolling when hovering over image panel.
        """
        if self.image_scroll.underMouse():
            bar = self.image_scroll.horizontalScrollBar()
            # Convert scroll wheel input to horizontal scroll:
            bar.setValue(bar.value() - event.angleDelta().y())
            event.accept()
        else:
            super().wheelEvent(event)