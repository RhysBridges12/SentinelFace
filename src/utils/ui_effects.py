"""
ui_effects.py

Provides reusable Qt visual shadow effect for UI components.
"""

from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor


def apply_shadow(widget, radius=24, x_offset=0, y_offset=4, opacity=80):
    """
    Apply a drop shadow effect to a Qt widget.
    
    Args:
        widget: Target UI component.
        radius (int, optional): The shadow blur radius.
        x_offset (int, optional): The horizontal shadow offset.
        y_offset (int, optional): The vertical shadow offset.
        opacity (int, optional): The shadow opacity value.
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(radius)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)
    shadow.setColor(QColor(0, 0, 0, opacity))
    widget.setGraphicsEffect(shadow)
