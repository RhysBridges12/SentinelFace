"""
search_processor.py

Handles database search operations by processing input media,
extracting embeddings, and querying the database for matches.

This file facilitates communication between the GUI, media processing,
and profile matching components of the system.
"""

import os

from matching.match_processor import process_search_image, process_search_video
from utils.system_logger import write_log


# Supported video file extensions for search input:
VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov")


def check_search_permission(window):
    """
    Validates whether the current user has permission to perform a search.

    Users with the 'auditor' role are restricted from searching.
    Unauthorized attempts are logged to the system logs and a 
    notification is outputted to the user's homepage.

    Args:
        window: GUI context containing user session information.

    Returns:
        bool: True if the user is permitted, False otherwise.
    """
    if window.current_role == "auditor":
        write_log(
            action="unauthorized_access",
            user=window.current_user,
            role=window.current_role,
            category="security",
            details={"target": "search"}
        )

        window.notify("Auditors cannot perform searches.", "warning")

        return False

    return True


def _process_image(window, file_path, filename):
    """
    Handles image-based search processing.

    Extracts a single embedding from the input image and validates that
    an embedding has been created. Notifies user of success or failure.

    Returns:
        list or None: A single embedding wrapped in a list, or None if failed.
    """
    result = process_search_image(file_path)

    if not result["success"]:
        window.notify(
            f"{filename}: {result['message']}",
            "error"
        )
        return None

    embedding = result["embedding"]

    if embedding is None:
        window.notify("No usable embeddings extracted.", "error")
        return None

    return [embedding]


def _process_video(window, file_path, filename):
    """
    Handles video-based search processing.

    Extracts face tracks and selects the most reliable one based
    on the number of embeddings (Track length)
    Notifies user of success or failure.

    Returns:
        list or None: A list of embeddings from the selected track, or None if failed.
    """
    result = process_search_video(file_path)

    if not result["success"]:
        window.notify(
            f"{filename}: {result['message']}",
            "error"
        )
        return None

    tracks = result["tracks"]

    if not tracks:
        window.notify(
            "Video processed: No tracks detected.",
            "error"
        )
        return None

    # Select the most reliable track (largest number of embeddings)
    selected_track = max(tracks, key=lambda t: len(t["embeddings"]))

    window.notify(
        f"Video processed: {len(tracks)} track(s) detected",
        "info"
    )

    return selected_track["embeddings"]


def process_search(window, file_path):
    """
    Processes a search request by extracting embeddings from an image or video.
    
    Verifies the user is permitted to perform searches, then determines the media
    type, calling a different function for images and videos.

    Args:
        window: GUI context containing user session information.
        file_path (str): The file path to the input media.

    Returns:
        list or None: List of embeddings if successful, otherwise None.
    """
    if not check_search_permission(window):
        return None

    filename = os.path.basename(file_path)

    write_log(
        action="search_started",
        user=window.current_user,
        role=window.current_role,
        category="search",
        details={"file": filename}
    )

    window.notify(
        f"Search started: {filename}",
        "info"
    )

    # Determine media type and pick a media processing function:
    is_video = file_path.lower().endswith(VIDEO_EXTENSIONS)

    if is_video:
        return _process_video(window, file_path, filename)
    else:
        return _process_image(window, file_path, filename)


def process_matches(window, embeddings):
    """
    Search the profile database and return a list of matches.

    Uses the provided embeddings to compute similarity scores against
    stored profiles and logs the results for auditing purposes.

    Args:
        window: GUI context containing an instance profile manager.
        embeddings (list): A list of embedding vectors to search with.

    Returns:
        list: Ranked list of (Profile, score) tuples.
    """
    all_matches = {}

    for embedding in embeddings:
        top_matches = window.profile_manager.find_top_matches(
            embedding,
            k=5
        )

        for profile, score in top_matches:

            pid = profile.person_id

            if pid not in all_matches or score > all_matches[pid][1]:
                all_matches[pid] = (profile, score)

    matches = sorted(
        all_matches.values(),
        key=lambda x: x[1],
        reverse=True
    )

    match_details = [
        {
            "person_id": profile.person_id,
            "score": round(score, 3)
        }
        for profile, score in matches
    ]

    # First value in the list is the closest match
    top_match = match_details[0] if match_details else None

    write_log(
        action="search_completed",
        user=window.current_user,
        role=window.current_role,
        category="search",
        details={
            "matches_found": len(matches),
            "top_match": top_match,
            "matches": match_details[:5]
        }
    )

    return matches