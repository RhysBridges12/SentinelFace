"""
enrol_match_page.py

Defines a dialog used during enrolment when a possible match is detected
and user input is needed.

One or many pop-ups display the newly detected face, with all images contained
within a candidate profile underneath. The similarity score is also displayed
indicating the confidence of the match.

Users are able to confirm (Yes) or reject (No) whether the match for all cases
within the low-match boundary. If none are a match, a new profile can be made.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QFrame, 
    QScrollArea, QWidget, QMessageBox
)
from PySide6.QtGui import QPixmap, QImage


# Constants used for layouts and sizing.
WINDOW_HEIGHT = 600
WINDOW_WIDTH = 700
MARGIN_SIZE = 24
INPUT_IMAGE_SIZE = 260
PROFILE_IMAGE_SIZE = 100


class EnrolMatchPage(QDialog):
    """
    A pop-up used to handle potential profile matches during enrolment.

    Displays the detected face alongside candidate profile images,
    allowing the user to confirm, reject, or create a new profile.
    """

    def __init__(self, new_face, match_profiles, similarity_score):
        """
        Initialises the enrol-match pop-up and populates the window with the
        specific input face, candidate profiles and `similarity` score.

        Args:
            new_face: Image array representing the detected face.
            match_profiles: A list of candidate profiles with similarity scores.
            similarity_score: Similarity score with nearest image in candidate profile.
        """
        super().__init__()

        # Apply stylesheet:
        self.setObjectName("mainWindow")
        self.setWindowTitle("Possible Match")
        self.resize(WINDOW_HEIGHT, WINDOW_WIDTH) 

        self.decision = None

        # List of candidate profiles:
        self.match_profiles = match_profiles
        self.current_index = 0
        
        if self.match_profiles:
            match_profile, similarity = self.match_profiles[self.current_index]
        else:
            match_profile, similarity = None, None

        # Main layout container
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scrollable area for candidate profile images:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        scroll_layout.setSpacing(16)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Main card container:
        card = QFrame()
        card.setObjectName("card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE, MARGIN_SIZE)
        card_layout.setSpacing(16)

        scroll_layout.addWidget(card)

        # Title displaying person ID and match similarity:
        if match_profile:
            self.title = QLabel(
                f"Possible match\nPerson: {match_profile.person_id}\nSimilarity: {similarity:.0%}"
            )
        else:
            self.title = QLabel("No matches found")

        self.title.setAlignment(Qt.AlignCenter)

        # Section title for new face:
        new_face_title = QLabel("New Face")
        new_face_title.setObjectName("settingsSectionLabel")
        new_face_title.setAlignment(Qt.AlignCenter)

        # Create an image label representing the new face image:
        new_face_label = self._create_image_label(new_face, INPUT_IMAGE_SIZE)

        # Section title for existing profile images:
        profile_images_title = QLabel("Existing Profile Images")
        profile_images_title.setObjectName("settingsSectionLabel")
        profile_images_title.setAlignment(Qt.AlignCenter)

        # Container for profile images:
        images_container = QWidget()
        self.images_layout = QHBoxLayout(images_container)
        self.images_layout.setAlignment(Qt.AlignLeft)
        self.images_layout.setSpacing(12)

        # Load images from the current match profile:
        if match_profile and match_profile.image_paths:
            for img_path in match_profile.image_paths:
                img_label = self._create_image_label(img_path, PROFILE_IMAGE_SIZE)
                self.images_layout.addWidget(img_label)

        self.images_layout.addStretch()

        # Scrollable area for profile images:
        images_scroll = QScrollArea()
        images_scroll.setWidgetResizable(True)
        images_scroll.setFixedHeight(130)
        images_scroll.setFrameShape(QFrame.NoFrame)
        images_scroll.setWidget(images_container)

        # Buttons for user decisions:
        btn_row = QHBoxLayout()

        self.yes_btn = QPushButton("Yes")
        self.yes_btn.setObjectName("primaryButton")

        self.no_btn = QPushButton("No")
        self.no_btn.setObjectName("primaryButton")

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("primaryButton")

        # Button shown only when no suitable match is found:
        self.create_btn = QPushButton("Create New Profile")
        self.create_btn.setObjectName("primaryButton")
        self.create_btn.hide()  # Hidden initially

        self.yes_btn.clicked.connect(self.yes_clicked)
        self.no_btn.clicked.connect(self.no_clicked)
        self.cancel_btn.clicked.connect(self.cancel_clicked)
        self.create_btn.clicked.connect(self.create_clicked)

        btn_row.addWidget(self.yes_btn)
        btn_row.addWidget(self.no_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.create_btn)

        # Assemble pop-up layout:
        card_layout.addWidget(self.title)
        card_layout.addWidget(new_face_title)
        card_layout.addWidget(new_face_label)
        card_layout.addWidget(profile_images_title)
        card_layout.addWidget(images_scroll)
        card_layout.addLayout(btn_row)
    
        # Load first candidate or offer user to create new profile:
        if self.match_profiles:
            self.load_candidate()
        else:
            self.yes_btn.hide()
            self.no_btn.hide()
            self.create_btn.show()
            
            
    def _create_image_label(self, image_source, image_size):
        """
        Create and return a QLabel displaying an input image.

        Supports both file paths and numpy image arrays. Images are scaled to 
        fit within the specified size, maintaining the aspect ratio.

        Args:
            image_source: File path of the image or numpy array representing the image.
            image_size: Target width and height for the displayed image.
        """
        # Create label with fixed size:
        img_label = QLabel()
        img_label.setFixedSize(image_size, image_size)
        
        if image_source is None:
            return img_label

        # If input is a file path: load directly into QPixmap:
        if isinstance(image_source, str):
            pix = QPixmap(image_source)

        # If the input is an image array: Convert to image first:
        else:
            h, w, ch = image_source.shape
            bytes_per_line = ch * w

            qimg = QImage(
                image_source.data,
                w,
                h,
                bytes_per_line,
                QImage.Format_BGR888
            )

            pix = QPixmap.fromImage(qimg)

        # Scale and display image:
        if not pix.isNull():
            pix = pix.scaled(
                image_size, image_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            img_label.setPixmap(pix)
            img_label.setAlignment(Qt.AlignCenter)

        return img_label
        
        
    def load_candidate(self):
        """
        Loads and displays the current candidate profile and its images.
        """
        profile, similarity = self.match_profiles[self.current_index]

        self.title.setText(
            f"Possible match\nPerson: {profile.person_id}\nSimilarity: {similarity:.0%}"
        )

        # Clear existing images:
        for i in reversed(range(self.images_layout.count())):
            item = self.images_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Reload images for the selected profile:
        if profile.image_paths:
            for img_path in profile.image_paths:
                img_label = self._create_image_label(img_path, PROFILE_IMAGE_SIZE)
                self.images_layout.addWidget(img_label)

        self.images_layout.addStretch()

 
    def yes_clicked(self):
        """
        Confirms the current profile as a match.
        """
        profile, _ = self.match_profiles[self.current_index]
        self.decision = ("yes", profile)    
        self.accept()


    def no_clicked(self):
        """
        Rejects current candidate and moves to next one.
        """
        self.current_index += 1

        if self.current_index >= len(self.match_profiles):
            self.yes_btn.hide()
            self.no_btn.hide()
            self.create_btn.show()
            
            self.title.setText("No suitable match found")
            
            for i in reversed(range(self.images_layout.count())):
                item = self.images_layout.takeAt(i)
                if item.widget():
                    item.widget().deleteLater()

            self.images_layout.addStretch()
            
            return

        self.load_candidate()


    def cancel_clicked(self):
        """
        Cancel the matching process.
        """
        self.decision = "cancel"
        self.reject()
        
        
    def create_clicked(self):
        """
        Confirms the creation of a new profile after warning the user that
        a potential duplicate could be added.
        If user says no to the popup, image is not enrolled.
        """
        reply = QMessageBox.warning(
            self,
            "Create New Profile",
            "No existing match was confirmed.\n\n"
            "Creating a new profile may result in duplicate identities.\n\n"
            "Are you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.Cancel
        )

        if reply == QMessageBox.Yes:
            self.decision = "create"
            self.accept()


    def get_decision(self):
        """
        Execute the dialog and return the user's decision.
        """
        self.exec()
        return self.decision