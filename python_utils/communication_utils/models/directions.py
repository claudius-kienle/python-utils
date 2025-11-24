from enum import Enum


class Direction(str, Enum):
    TOP = "top"
    LEFT = "left"
    RIGHT = "right"
    BOTTOM = "bottom"
    FRONT = "front"
    BACK = "back"
    CENTER = "center"
