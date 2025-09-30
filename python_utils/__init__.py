"""Python Utilities Package

A collection of utility functions and classes for common Python tasks in the Digital Engineering Agent project.
"""

__version__ = "1.0.1"

# Data utilities
from .data_utils import (
    asdict,
    fromdict,
    base64_to_image,
    dict_similar,
)

# String utilities
from .string_utils import (
    remove_comments,
    parse_timedelta,
    wrap_code,
    get_markup_from_text,
    snake_to_camel,
    camel_to_snake,
    remove_docstrings,
    xml_escape,
    extract_first_skill_list,
)

# Point utilities
from .point_utils import Point

# Transformation utilities
from .transformations import (
    # Matrix operations
    is_4_by_4_matrix,
    quaternion_to_rotation_matrix,
    normalize_quaternions,
    rotation_matrix_to_quaternion,
    
    # Euler angle conversions
    euler_zyx_to_quaternion,
    quaternion_to_euler_zyx,
    quaternion_to_euler,
    euler_to_quaternion,
    matrix_to_euler_angles,
    
    # Pose transformations
    pose_to_affine,
    affine_to_pose,
    pose_inverse,
    affine_inverse,
    affine_transform,
    
    # Relative/absolute conversions
    absolute_to_relative,
    relative_to_absolute,
    compute_relative_offset,
    
    # Pose format conversions
    pose_euler_zyx_to_affine,
    affine_to_pose_euler_zyx,
    pose_quaternion_to_euler_zyx,
    pose_quaternion_to_euler,
    pose_euler_zyx_to_quaternion,
    pose_euler_to_quaternion,
    
    # Utility functions
    map_rad_rotations,
    quaternion_distance,
    rotation_from_axis_angle,
    axis_angle_from_quaternion,
    quaternion_from_axis_angle,
    axis_angle_from_rotation,
    translation_to_affine,
    get_cross_prod_mat,
    calculate_align_mat,
)

# Deprecation utilities
from .deprecated import deprecated

__all__ = [
    # Data utilities
    "asdict",
    "fromdict", 
    "base64_to_image",
    "dict_similar",
    
    # String utilities
    "remove_comments",
    "parse_timedelta", 
    "wrap_code",
    "get_markup_from_text",
    "snake_to_camel",
    "camel_to_snake",
    "remove_docstrings",
    "xml_escape",
    "extract_first_skill_list",
    
    # Point utilities
    "Point",
    
    # Transformation utilities
    "is_4_by_4_matrix",
    "quaternion_to_rotation_matrix",
    "normalize_quaternions", 
    "rotation_matrix_to_quaternion",
    "euler_zyx_to_quaternion",
    "quaternion_to_euler_zyx",
    "quaternion_to_euler",
    "euler_to_quaternion",
    "matrix_to_euler_angles",
    "pose_to_affine",
    "affine_to_pose",
    "pose_inverse",
    "affine_inverse",
    "affine_transform",
    "absolute_to_relative",
    "relative_to_absolute",
    "compute_relative_offset",
    "pose_euler_zyx_to_affine",
    "affine_to_pose_euler_zyx",
    "pose_quaternion_to_euler_zyx",
    "pose_quaternion_to_euler",
    "pose_euler_zyx_to_quaternion",
    "pose_euler_to_quaternion",
    "map_rad_rotations",
    "quaternion_distance",
    "rotation_from_axis_angle",
    "axis_angle_from_quaternion",
    "quaternion_from_axis_angle",
    "axis_angle_from_rotation",
    "translation_to_affine",
    "get_cross_prod_mat",
    "calculate_align_mat",
    
    # Deprecation utilities
    "deprecated",
]