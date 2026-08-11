# compute.py


import onnxruntime as ort

_compute_mode = "auto"


def set_compute_mode(mode: str):
    global _compute_mode
    _compute_mode = mode.strip().lower()


def use_gpu():
    """
    Determines whether GPU execution should be used or not.

    Returns:
        bool: True if CUDA is available or GPU mode is on.
    """
    if _compute_mode == "cpu":
        return False

    if _compute_mode == "gpu":
        return True

    try:
        return "CUDAExecutionProvider" in ort.get_available_providers()
    except Exception:
        return False
