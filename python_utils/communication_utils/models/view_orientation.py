from enum import Enum


class ViewOrientation(Enum):
    """orientations to view cad object from

    views are not perfectly aligned to reduce reflection
    """

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    FRONT = "front"
    BACK = "back"
    ISO = "iso"
