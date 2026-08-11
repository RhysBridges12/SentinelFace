"""
enrol_processor.py

Handles the enrolment of images into the database, including permission checks, 
image loading, image processing, and decision logic for adding faces to the database.

This file coordinates interactions between the GUI, the face processing pipeline,
and the profile management system. It determines whether a face should be added to
an existing profile, flagged for review, or enrolled as a new individual.
"""

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from processing.face_processor import process_image
from gui.enrol_match_page import EnrolMatchPage
from utils.system_logger import write_log


# Thresholds used to determine which matching behaviour is applied:
DUPLICATE_THRESHOLD = 0.95
MATCH_RANGE_HIGH = 0.4
MATCH_RANGE_LOW = 0.25

MARGIN_THRESHOLD = 0.05 # Ensures clear separation between top matches


def check_enrol_permission(window):
    """
    Checks whether the current user has permission to enrol individuals.

    Auditors are restricted from performing enrolment actions.
    Logs all unauthorized access attempts for auditing purposes and
    notifies the user that they lack permissions for enrolment.
    """
    if window.current_role == "auditor":
        write_log(
            action="unauthorized_access",
            user=window.current_user,
            role=window.current_role,
            category="security",
            details={"target": "enrol"}
        )

        window.notify("Auditors cannot enrol individuals.", "warning")
        return False

    return True


def select_enrol_images(window):
    """
    Opens a file dialog for selecting one or more image files.

    Returns:
        list: A list of the selected file paths.
    """
    file_paths, _ = QFileDialog.getOpenFileNames(
        window,
        "Select Image(s)",
        "",
        "Images (*.png *.jpg *.jpeg)"
    )
    return file_paths


def process_enrol_image(file_path):
    """
    Processes a single image for enrolment, returning the image data.

    Wraps the face processing pipeline and converts results into a
    simplified structure for downstream handling.

    Args:
        file_path (str): The file path to the input image.

    Returns:
        dict: Success flag, image metadata and processed face data.
    """
    filename = Path(file_path).name

    result = process_image(file_path)

    # Handle processing failure:
    if not result["success"]:
        return {
            "status": "error",
            "message": f"{filename}: {result['message']}"
        }

    # Return a structured success response:
    return {
        "status": "ok",
        "filename": filename,
        "embedding": result["embedding"],
        "face_img": result["aligned_face"],
        "metrics": result["metrics"],
        "metadata": {
            "age": result.get("age"),
            "gender": result.get("gender")
        }
    }
    
    
def _add_to_profile(window, data, match, score):
    """
    Adds a face image to an existing profile.

    This function is used when a strong or user confirmed match is identified.
    It stores the face image, embedding, and associated metrics in the
    matched profile and logs the action, notifying the user of success.

    Args:
        window: Reference to the main application window.
        data (dict): Enrolment data containing face image and metadata.
        match (Profile): The profile with the closest match to input image.
        score (float): Similarity score between database image and input image.
    """
    # Add face image and embedding to the profile:
    stored_path = window.profile_manager.add_face_to_profile(
        match,
        data["face_img"],
        data["embedding"],
        data["metrics"]
    )
    # Store metadata (age and gender):
    _store_metadata(match, data["metadata"], stored_path)

    write_log(
        action="image_added",
        user=window.current_user,
        role=window.current_role,
        category="database",
        details={"person_id": match.person_id}
    )

    window.notify(
        f"Added to {match.person_id} (Score: {score:.2f})",
        "success"
    )
    return

    
def _prompt_user(window, data, matches):
    """
    Prompts the user for a decision to resolve a potential match.

    This function is triggered when a match with a moderate similarity score 
    is detected. The system pauses processing and presents a GUI page prompting
    whether to add the face to an existing profile, create a new profile,
    or cancel the enrolment entirely.
    
    Args:
        window: Reference to the main application window.
        data (dict): Enrolment data containing face images and metadata.
        matches (list): List of (profile, score) tuples.    
    """
    window.threader.pause()

    enrol_page = EnrolMatchPage(
        new_face=data["face_img"],
        match_profiles=matches,
        similarity_score=matches[0][1] if matches else 0
    )

    decision = enrol_page.get_decision()

    window.threader.resume()

    if isinstance(decision, tuple) and decision[0] == "yes":
        selected_profile = decision[1]

        # find correct score for selected profile
        selected_score = next(
            score for profile, score in matches
            if profile.person_id == selected_profile.person_id
        )

        _add_to_profile(window, data, selected_profile, selected_score)

    elif decision == "create":
        _create_new_profile(window, data)

    elif decision == "cancel":
        write_log(
            action="enrol_cancelled",
            user=window.current_user,
            role=window.current_role,
            category="database",
            details={"source": data["filename"]}
        )    
        

def _create_new_profile(window, data):
    """
    Creates a new profile for an unmatched face.

    This function is used when no suitable match is found or the user
    chooses to enrol a new individual. It optionally prompts for confirmation,
    then creates and stores a new profile with associated metadata.

    Args:
        window: Reference to the main application window.
        data (dict): Enrolment data containing face image and metadata.
    """
    # Show enrolment confirmation and wait if setting is enabled:
    if window.settings["confirm_on_enrol"]:
        window.threader.pause()

        reply = QMessageBox.question(
            window,
            "New Individual",
            f"Enrol {data['filename']} as a new person?",
            QMessageBox.Yes | QMessageBox.No
        )

        window.threader.resume()
    else:
        reply = QMessageBox.Yes # Automatically yes if no confirmation shown.

    if reply != QMessageBox.Yes:
        return

    # Create a new profile:
    profile, _ = window.profile_manager.register_face(
        data["face_img"],
        data["embedding"],
        data["metrics"]
    )

    image_path = profile.image_paths[-1] # Image that was just added.

    _store_metadata(profile, data["metadata"], image_path)

    window.profile_manager.save_profile(profile)

    write_log(
        action="profile_enrolled",
        user=window.current_user,
        role=window.current_role,
        category="database",
        details={
            "person_id": profile.person_id,
            "source": data["filename"],
        },
    )

    window.notify(f"New individual: {profile.person_id}", "success")


def handle_enrol_result(window, data):
    """
    Processes enrolment results and determines the appropriate action.

    Using the similarity score between the closest and second-closest matches in 
    the database, it determines whether the input image is a duplicate, belongs to
    an existing profile, requires user decision or should be enrolled as a new
    individual.
    
    A margin is used to prevent adding an image to a profile which is marginally
    better than another as both are potential match candidates.

    Args:
        window: Reference to the main application window.
        data (dict): Enrolment data containing face image and metadata.
    """
    # Check if detection was successful:
    if data["status"] == "error":
        window.notify(data["message"], "error")
        return

    matches = window.profile_manager.find_top_matches(
        data["embedding"],
        k=3
    )

    if not matches:
        _create_new_profile(window, data)
        return

    match, score = matches[0]
    second_score = matches[1][1] if len(matches) > 1 else -1.0

    if score >= DUPLICATE_THRESHOLD:
        write_log(
            action="duplicate_image_detected",
            user=window.current_user,
            role=window.current_role,
            category="database",
            details={
                "file": data["filename"],
                "person_id": match.person_id
            }
        )
        window.notify(f"{data['filename']} already exists", "warning")
        return

    elif score >= MATCH_RANGE_HIGH and (score - second_score) >= MARGIN_THRESHOLD:
        _add_to_profile(window, data, match, score)
        return

    elif score >= MATCH_RANGE_LOW:
        _prompt_user(window, data, matches)
        return

    else:
        _create_new_profile(window, data)
        

def _store_metadata(profile, meta, image_path):
    """
    Stores optional predicted metadata (age and gender) associated with a
    face in an image.
    
    Args:
        profile (Profile): Profile of the user containing the image.
        meta (dict): Contains image metadata about predicted gender and age.
        image_path (str): The file path to the input image.
    """
    profile.metadata.setdefault(image_path, {})

    if meta["age"] is not None:
        profile.metadata[image_path]["age"] = int(meta["age"])

    if meta["gender"] is not None:
        profile.metadata[image_path]["gender"] = (
            "male" if meta["gender"] == 1 else "female"
        )