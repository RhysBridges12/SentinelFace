"""
# main.py

The entry point and central controller for the systems GUI.

This file is responsible for managing the system during runtime, coordinating
interactions between GUI pages, handling navigation, user permissions and logging.

No logic is implemented here directly. This class delegates processing, matching
and database access to other files in the system.
"""
import os
import sys
import warnings

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, 
    QVBoxLayout, QFileDialog, QLabel,
    QPushButton, QFrame, QStackedWidget 
)

from database.profile_manager import ProfileManager
from database.user_manager import UserManager

from gui.login_page import LoginPage
from gui.home_page import HomePage
from gui.database_page import DatabasePage
from gui.profile_page import ProfilePage
from gui.matches_page import MatchesPage
from gui.help_page import HelpPage
from gui.logs_page import LogsPage
from gui.settings_page import SettingsPage

from processing.enrol_processor import (
    check_enrol_permission, select_enrol_images,
    process_enrol_image, handle_enrol_result
)
from processing.enrol_threader import EnrolThreader
from processing.face_processor import get_detector

from matching.search_processor import (
    check_search_permission, process_search, process_matches
)

from utils.compute import set_compute_mode
from utils.notification_store import load_notifications
from utils.settings_store import load_settings
from utils.stylesheet import build_global_stylesheet, make_icon_button
from utils.system_logger import write_log
from utils.theme import load_theme
from utils.ui_effects import apply_shadow


# Suppress known non-critical warnings from dependencies:
warnings.filterwarnings("ignore", category=FutureWarning)

# Constants used in formatting the main window and top bar:
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 700
MIN_WIDTH = 900
MIN_HEIGHT = 600
SPACING = 16
TOP_BAR_HEIGHT = 76
MARGIN_SIZE = 24


class MainWindow(QWidget):
    """
    The primary application window responsible for storing the session-context,
    validating user permissions and coordinating all GUI pages in the system.
    
    All activities within the system are logged for auditing.
    """
    def __init__(self):
        """
        Initialises the main window of the application.
        """
        super().__init__()
        self.setObjectName("mainWindow")
        
        # Session state: (updated on login/logout)
        self.current_user = None
        self.current_role = None
        
        # Indicates whether profile access is coming from a match result:
        # Allows non-admin users to view profiles after searching.
        self.match_context = False
        
        # Core managers for users and profiles:
        self.user_manager = UserManager()
        self.profile_manager = ProfileManager()

        # Load persisted settings and apply them:
        self.settings = load_settings()
        load_theme(self.settings["theme"])
        set_compute_mode(self.settings["compute_mode"])

        # Window configuration:
        self.setWindowTitle("SentinelFace")
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        # Main layout:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(SPACING)

        # Topbar for navigation:
        self.top_bar = self.build_top_bar()

        # Navigation history for back button functionality:
        self._page_history = []

        # Create an instance of all pages:
        self.login_page = LoginPage(self)
        self.home_page = HomePage(self)
        self.database_page = DatabasePage(self)
        self.profile_page = ProfilePage(self)
        self.matches_page = MatchesPage(self)
        self.logs_page = LogsPage(self)
        
        # Stacked widget manages all pages:
        self.stack = QStackedWidget()
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.database_page)
        self.stack.addWidget(self.profile_page)
        self.stack.addWidget(self.matches_page)
        self.stack.addWidget(self.logs_page)
        
        # Assemble the application window:
        main_layout.addWidget(self.top_bar)
        main_layout.addWidget(self.stack)

        # Upon loading, navigate to the login page:
        self.stack.setCurrentWidget(self.login_page)


    def notify(self, message, severity="info"):
        """
        Push a notification event to the home page notification panel.
        Each user has their own notifications.

        Args:
            message (str): Message to display in the notification.
            severity (str): Severity level for styling. (info, warning, error, success)
        """
        self.home_page.notif_panel.add_event(message, severity)
    
    
    def refresh_theme(self):
        """
        Re-applies styling across the application after a theme change.

        Forces Qt to re-polish widgets and rebuilds the top bar to ensure
        updated styles are applied consistently.
        """
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

        # Rebuild top bar to ensure styling is refreshed:
        self.top_bar.deleteLater()
        self.top_bar = self.build_top_bar()
        self.layout().insertWidget(0, self.top_bar)
        
        # If a user is logged in, enable the top bar:
        if self.current_user:
            self.home_btn.setEnabled(True)
            self.settings_btn.setEnabled(True)
            self.back_btn.setEnabled(True)
            self.help_btn.setEnabled(True)

        # Refresh each page:
        self.home_page.refresh_theme()
        self.database_page.refresh_theme()
        self.profile_page.refresh_theme()


    def toggle_theme(self, mode):
        """
        Switch application theme and apply updated stylesheet.

        Args:
            mode (str): The systems theme (light or dark)
        """
        load_theme(mode)
        
        # Update all colours globally:
        QApplication.instance().setStyleSheet(build_global_stylesheet())

        self.refresh_theme()


    def navigate_to(self, widget):
        """
        Navigate to a new page while maintaining navigation history, 
        needed when using the back button 

        Args:
            widget (QWidget): The page to navigate to.
        """
        current = self.stack.currentWidget()
        if current is not widget:
            if current != self.login_page: # Dont allow navigation to login page.
                self._page_history.append(current) 
            self.stack.setCurrentWidget(widget)


    def back_clicked(self):
        """
        Navigate back to the previous page if history exists.
        """
        if not self._page_history:
            return
        previous = self._page_history.pop()
        self.stack.setCurrentWidget(previous)
    
    
    def disable_topbar(self):
        """
        Disable all top bar navigation buttons.
        Used when a user logs out of the system.
        """
        self.home_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)
        self.back_btn.setEnabled(False)
        self.help_btn.setEnabled(False)
        
        
    def enable_topbar(self):
        """
        Enable all top bar navigation buttons.  
        Used when a user logs into the system.
        """
        self.home_btn.setEnabled(True)
        self.settings_btn.setEnabled(True)
        self.back_btn.setEnabled(True)
        self.help_btn.setEnabled(True)
        

    def show_home_page(self):
        """
        Display the home page and reload user-specific notifications.
        """
        self.enable_topbar()
        
        # Clear existing notifications:
        self.home_page.notif_panel.clear()

        # Load persisted notifications for current user:
        for notif in load_notifications(username=self.current_user):
            self.home_page.notif_panel.add_event(
                notif["message"],
                notif["severity"],
                notif["timestamp"],
                persist=False
            )
        
        self.match_context = False
        self.navigate_to(self.home_page)


    def show_database_page(self):
        """
        Display the database page if user has admin permissions.
        """
        self.match_context = False

        # Only admins can access the database:
        if self.current_role != "admin":
            write_log(
                action="unauthorized_access",
                user=self.current_user,
                role=self.current_role,
                category="security",
                details={"target": "database"}
            )
            
            self.notify("Only administrators can access the database.", "warning")
            return
        
        write_log(
            action="database_accessed",
            user=self.current_user,
            role=self.current_role,
            category="system"
        )
        
        self.database_page.display_profiles()
        self.navigate_to(self.database_page)


    def show_profile_page(self, profile):
        """
        Display a profile page with role-based access restrictions.

        Args:
            profile: Profile object to display
        """

        # Auditors cannot view profiles:
        if self.current_role == "auditor":
            write_log(
                action="unauthorized_access",
                user=self.current_user,
                role=self.current_role,
                category="security",
                details={"target": "profile_view"}
            )
               
            self.notify("Auditors cannot view profiles.", "warning")
            return
        
        # Operators can only view profiles if its a match result:
        if self.current_role == "user" and not self.match_context:
            write_log(
                action="unauthorized_access",
                user=self.current_user,
                role=self.current_role,
                category="security",
                details={"target": "database"}
            )
            
            self.notify("Operators can only view profiles from match results.", "warning")
            return
        
        write_log(
            action="profile_viewed",
            user=self.current_user,
            role=self.current_role,
            category="database",
            details={"person_id": profile.person_id}
        )
        
        self.profile_page.set_profile(profile)
        self.navigate_to(self.profile_page)


    def build_top_bar(self):
        """
        Constructs the top navigation bar with action buttons, logo and title.
        The top bar is visible at all times.

        Returns:
            QFrame: Configured top bar widget
        """
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setMinimumHeight(TOP_BAR_HEIGHT)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(MARGIN_SIZE, 0, MARGIN_SIZE, 0)

        title = QLabel("SentinelFace")
        title.setObjectName("topBarTitle")
        
        # Navigation button icons and connections:
        self.home_btn = make_icon_button("images/icons/home.png")
        self.home_btn.clicked.connect(self.home_clicked)

        self.settings_btn = make_icon_button("images/icons/settings.png")
        self.settings_btn.clicked.connect(self.settings_clicked)

        self.back_btn = make_icon_button("images/icons/back.png")
        self.back_btn.clicked.connect(self.back_clicked)
        
        self.help_btn = make_icon_button("images/icons/help.png")
        self.help_btn.clicked.connect(self.help_clicked)
        
        # Disable topbar until a successful login:
        self.disable_topbar()

        # Assemble topbar:
        layout.addWidget(self.home_btn)
        layout.addWidget(self.settings_btn)
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.help_btn)
        layout.addWidget(self.back_btn)

        apply_shadow(bar, radius=18, y_offset=2, opacity=40)
        return bar


    def home_clicked(self):
        """
        Handles home button clicks.
        """
        self.show_home_page()


    def settings_clicked(self):
        """
        Open settings pop-up centered on main window.
        """
        settings = SettingsPage(self)

        # Place in the centre:
        settings.move(
            self.x() + (self.width() - settings.width()) // 2,
            self.y() + (self.height() - settings.height()) // 2
        )

        # Pause main window until settings pop-up closed:
        settings.exec()
      
        
    def help_clicked(self):
        """
        Open help pop-up.
        """
        help_page = HelpPage(self)
        # Pause main window until help pop-up closed:
        help_page.exec()


    def enrol_clicked(self):
        """
        Start the enrolment pipeline for a batch of images.

        Handles permission checks, file selection, batch validation,
        and launches background processing in a thread.
        """
        if not check_enrol_permission(self):
            return

        file_paths = select_enrol_images(self)
        if not file_paths:
            return
        
        # Track progress of enrolment:
        self._enrol_total = len(file_paths)
        self._enrol_done = 0
        
        self.notify(
            f"Batch enrol started ({len(file_paths)} images)",
            "info"
        )
        
        # Prevent multiple concurrent enrolment operations:
        if hasattr(self, "threader") and self.threader.isRunning():
            self.notify("Enrol already in progress", "warning")
            return

        # Enforce batch size limit from settings:
        max_batch = self.settings["batch_size"]
        if len(file_paths) > max_batch:
            self.notify(
                f"Input limit reached, you can only process {max_batch} images at once.",
                "warning"
            )
            return

        # Create notification card with cancel action:
        self.enrol_card = self.home_page.notif_panel.add_event(
            f"Processing {len(file_paths)} image(s)",
            "info",
            action=self._cancel_enrol,
            lbl="Cancel",
        )

        # Start a thread to handle enrolment:
        self.threader = EnrolThreader(self, file_paths)
        self.threader.progress.connect(
            lambda data, _: self._handle_progress(data)
        )        

        self.threader.finished.connect(self._on_enrol_finished)
        self.threader.start()
     
        
    def _cancel_enrol(self):
        """
        Runs when cancelling enrolment before finishing.

        Stops the background thread and updates the notification panel
        to reflect cancellation.
        """
        if hasattr(self, "threader") and self.threader.isRunning():
            self.threader.cancel()
            self.notify("Cancelling batch...", "warning")

            # Disable cancel button to prevent repeated clicks:
            if hasattr(self, "enrol_card"):
                self.enrol_card.action_btn.setText("Cancelling...")
                self.enrol_card.action_btn.setEnabled(False)

    
    def _on_enrol_finished(self):
        """
        Runs on the completion of the enrolment.

        Cleans up GUI elements and logs face detector activity.
        """
        self.notify("Batch processing complete", "success")
    
        # Remove progress notification card:
        if hasattr(self, "enrol_card"):
            self.home_page.notif_panel.remove_event_card(self.enrol_card)
            del self.enrol_card
        
        # Log detector activity for this session:
        detector = get_detector()
        detector.log_stats(
            user=self.current_user,
            role=self.current_role,
        )
        
        
    def _handle_progress(self, data):
        """
        Handles progress updates from the enrolment thread.
        
        Runs upon the processing of a single image, updating processing 
        results and reflects progress in the UI.
        """
        # Process result from current image:
        handle_enrol_result(self, data)
        
        self._enrol_done += 1 # Increment counter.

        # Display progress in notification card:
        if hasattr(self, "enrol_card"):
            msg = f"Processing {self._enrol_done} / {self._enrol_total} images"
            for child in self.enrol_card.findChildren(QLabel):
                if child.objectName() == "eventMessage":
                    child.setText(msg) # Change label on notication.
                    break
        
        
    def db_clicked(self):
        """
        Handles database button click and checks if a user has sufficient permissions.
        """
        #   Only admins can access the database page:
        if self.current_role != "admin":
            write_log(
                action="unauthorized_access",
                user=self.current_user,
                role=self.current_role,
                category="security",
                details={"target": "database"}
            )
            
            self.notify("Only administrators can access the database.", "warning")
            return

        self.show_database_page()


    def search_clicked(self):
        """
        Handles search button click and checks if a user has sufficient permissions.
        
        The user is prompted to select a file, an embedding is generated from a
        detected face, the system is searched for matches and results are displayed.
        """
        if not check_search_permission(self):
            return

        # Select input media: (image or video)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image or Video for Search",
            "",
            "Media Files (*.png *.jpg *.jpeg *.mp4 *.avi *.mov)"
        )
        if not file_path:
            return

        # Generate embeddings from input:
        embeddings = process_search(self, file_path)
        if embeddings is None:
            return

        # Perform matching against database:
        matches = process_matches(self, embeddings)

        # Notify user of results:
        if not matches:
            self.notify(
                "Search complete: no matches found", "error")
        else:
            self.notify(
                f"Search complete: {len(matches)} match(es) found", "success")

            # Enable profile access from match results for operators:
            self.match_context = True
            self.matches_page.display_matches(matches)
            self.navigate_to(self.matches_page)
            
        
    def logs_clicked(self):
        """
        Display system logs page if user has sufficient permissions.
        """
        # Operators can not view the system logs:
        if self.current_role not in ["admin", "auditor"]:
            write_log(
                action="unauthorized_access",
                user=self.current_user,
                role=self.current_role,
                category="security",
                details={"target": "system_logs"}
            )
            
            self.notify("You do not have permission to view system logs.", "warning")
            return
        
        write_log(
            action="logs_viewed",
            user=self.current_user,
            role=self.current_role,
            category="system"
        )
        
        self.logs_page.load_logs()
        self.navigate_to(self.logs_page)
        
    
    def logout(self):
        """
        Log out the current user and reset application state.

        Clears session data, disables navigation and returns to login page.
        """
        user = self.current_user

        if user:
            write_log(
                action="logout",
                user=user,
                category="authentication"
            )
            self.notify(f"{user} logged out", "info")

        # Clear session state:
        self.current_user = None
        self.current_role = None

        # Reset navigation and context:
        self._page_history.clear()
        self.match_context = False
        
        # Reset GUI state on logout (disable navigation and clear inputs)
        self.disable_topbar()
        self.login_page.username_input.clear()
        self.login_page.password_input.clear()
         
        # Return to login screen:
        self.stack.setCurrentWidget(self.login_page)


if __name__ == "__main__":
    """
    Application entry point.

    Initialises QApplication, applies theme and stylesheet and 
    launches the main window.
    """
    app = QApplication(sys.argv)
    
    load_theme(load_settings()["theme"])
    app.setStyleSheet(build_global_stylesheet())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())