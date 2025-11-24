from typing import List, Tuple

import distinctipy

Color = Tuple[float, float, float]

global unique_color_supplier
unique_color_supplier = None


class UniqueColorSupplier:
    """supplier to get unique colors

    :return: _description_
    """

    generated_colors: List[Color]

    def __init__(self) -> None:
        self.reset_used_colors()

    @staticmethod
    def get_instance() -> "UniqueColorSupplier":
        global unique_color_supplier
        if unique_color_supplier is None:
            unique_color_supplier = UniqueColorSupplier()
        return unique_color_supplier

    def reset_used_colors(self):
        self.generated_colors = [(0.5, 0.5, 0.5), (1, 1, 1)]  # fallback_color and background

    def get_color(self) -> Color:
        new_color = distinctipy.distinct_color(
            self.generated_colors, pastel_factor=0.0, n_attempts=1000, colorblind_type=None, rng=None
        )
        self.generated_colors.append(new_color)
        return new_color
