# theme.py

from . import colours_dark as dark
from . import colours_light as light


class Theme:
    current = light


def load_theme(mode: str):
    """
    mode = 'light' or 'dark'
    """
    if mode == "dark":
        Theme.current = dark
    else:
        Theme.current = light

    return Theme.current


def get_theme():
    return Theme.current