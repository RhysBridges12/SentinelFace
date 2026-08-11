"""
image_item.py

Defines a clickable image item used for displaying stored images.

Facilitates image deletion when viewing a user profile.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMenu
from PySide6.QtGui import QPixmap


IMAGE_SIZE = 100


class ImageItem(QLabel):
    """
    A GUI component for displaying an image with optional delete functionality.
    
    Deletion is triggered via a right-click context menu.
    """
    def __init__(self, img_path, delete_action=None):
        """
        Initialises the image item.

        Args:
            img_path (str): The file path to the displayed image.
            delete_action (callable, optional): The function called upon image deletion.
        """
        super().__init__()

        self.img_path = img_path
        self.delete_action = delete_action

        self.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
        self.setAlignment(Qt.AlignCenter)

        # Scale image while preserving aspect ratio:
        pix = QPixmap(img_path)
        if not pix.isNull():
            pix = pix.scaled(
                IMAGE_SIZE, IMAGE_SIZE, 
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(pix)
        else:
            self.setText("Image not found")


    def contextMenuEvent(self, event):
        """
        Displays a menu with options for the image item.
        """
        menu = QMenu(self)
        
        # Option to delete image:
        delete = menu.addAction("Delete Image")
        action = menu.exec(event.globalPos())

        if action == delete and self.delete_action:
            self.delete_action(self.img_path)
