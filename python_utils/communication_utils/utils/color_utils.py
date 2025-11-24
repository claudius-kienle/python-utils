import json
from pathlib import Path
from typing import List

import distinctipy
import numpy as np
import webcolors


def closest_color(requested_color):
    """get closest color name given `requested_color`

    :param requested_color: color
    :return: color name
    """
    if isinstance(requested_color[0], float):
        requested_color = [int(c * 255) for c in requested_color]
    min_colors = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    return min_colors[min(min_colors.keys())]


def get_color_name(rgb_color):
    """get closest color name

    :param rgb_color: rgb color
    :return: color name
    """
    if isinstance(rgb_color[0], float):
        rgb_color = [int(c * 255) for c in rgb_color]
    try:
        color_name = webcolors.rgb_to_name(rgb_color)
    except ValueError:
        color_name = closest_color(rgb_color)
    return color_name


def get_unique_colors(n_colors: int) -> List[List[float]]:
    # rng defines seed
    colors_file = Path(__file__).parent / "colors.json"
    if not colors_file.is_file():
        colors = distinctipy.get_colors(100, exclude_colors=[[0, 0, 0], [1, 1, 1]], rng=0)
        with colors_file.open("w") as f:
            json.dump(colors, f)
    else:
        with colors_file.open("r") as f:
            colors = json.load(f)
    assert isinstance(colors, list), "colors.json should contain a list of colors"
    if n_colors > len(colors):
        np.random.seed(0)
        rest_colors = (np.random.choice(range(256), size=(n_colors - len(colors), 3)) / 255).tolist()
        return colors + rest_colors
    else:
        return colors[:n_colors]
