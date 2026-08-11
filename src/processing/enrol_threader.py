"""
enrol_threader.py

Handles the processing of image enrolment using a worker thread.

This module defines a QThread-based class responsible for processing multiple
image files without blocking the main GUI. It facilitates accessing the database 
and settings/help pages whilst enrolling images and communicates results back 
to the system via signals.
"""

import os

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex
from processing.enrol_processor import process_enrol_image


DATABASE_DIR = "database"
IMAGES_DIR = os.path.join(DATABASE_DIR, "images")

class EnrolThreader(QThread):
    """
    A worker thread for processing images during enrolment.

    Iterates through a list of file paths, processes each image, and emits
    results back to the main window. Thread execution can be paused, resumed,
    or cancelled safely using mutexes and wait conditions.
    """

    # Signal used to send processed data or error messages back to the UI
    progress = Signal(object, str)

    def __init__(self, window, file_paths):
        super().__init__()
        self.main_window = window # Reference to main GUI window
        self.file_paths = file_paths
        
        # Flags indicating current thread states:
        self._pause = False
        self._cancel = False 
        
        self._mutex = QMutex() # A lock so only one thread uses shared data at once.
        self._wait = QWaitCondition() # Facilitates pausing the thread.
        
        os.makedirs(IMAGES_DIR, exist_ok=True)
        

    def run(self):
        """
        The face enrolment pipeline used in the worker thread.

        Processes each image sequentially while respecting pause and cancel
        states. Results are emitted back to the UI using signals.
        """
        for file_path in self.file_paths:

            # Exit early if cancellation has been requested.
            if self._cancel:
                break
        
            # Pause handling, block thread until resumed:
            self._mutex.lock()
            while self._pause:
                self._wait.wait(self._mutex)
            self._mutex.unlock()

            try:
                # Process enrolment image (face detection, embedding, etc.)
                data = process_enrol_image(file_path)

                # Check if system is paused before emitting results:
                self._mutex.lock()
                while self._pause:
                    self._wait.wait(self._mutex)
                self._mutex.unlock()
                
                if self._cancel:
                    break

                # Emit successful result back to the UI:
                self.progress.emit(data, "data")

            # Emit error information without crashing the thread:
            except Exception as e:
                self.progress.emit({"status": "error", "message": str(e)}, "error")
        
    
    def pause(self):
        """
        Pauses thread execution.

        The thread will stop and wait at the next pause checkpoint.
        """
        self._mutex.lock()
        self._pause = True
        self._mutex.unlock()


    def resume(self):
        """
        Resumes thread execution.

        A waiting thread continues processing images.
        """
        self._mutex.lock()
        self._pause = False
        self._wait.wakeAll()
        self._mutex.unlock()


    def cancel(self):
        """
        Cancels thread execution.

        Sets the cancel flag to true and resumes the thread 
        if paused, allowing it to exit cleanly.
        """
        self._cancel = True
        self.resume()