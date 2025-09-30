import math

import numpy as np
import torch

import python_utils.external.pytorch3d_transformations as py3dtransforms


def is_4_by_4_matrix(t: torch.Tensor):
    return t.size(-1) == 4 and t.size(-2) == 4


def quaternion_to_rotation_matrix(quaternions: torch.Tensor) -> torch.Tensor:
    return py3dtransforms.quaternion_to_matrix(normalize_quaternions(quaternions))


def normalize_quaternions(quat: torch.Tensor) -> torch.Tensor:
    assert quat.shape[-1] == 4
    sign = torch.sign(quat[..., 0]).unsqueeze(-1)
    sign = torch.where(sign == 0, 1, sign)
    return sign * quat / torch.norm(quat, dim=-1).unsqueeze(-1)


def rotation_matrix_to_quaternion(mat: torch.Tensor) -> torch.Tensor:
    """
    https://pytorch3d.readthedocs.io/en/latest/_modules/pytorch3d/transforms/rotation_conversions.html#matrix_to_quaternion
    :param mat: 3x3 rotation matrix
    :return: Unit quaternion
    """
    quat = py3dtransforms.matrix_to_quaternion(mat)
    return normalize_quaternions(quat)


def euler_zyx_to_quaternion(euler_zyx: torch.Tensor, degrees=False) -> torch.Tensor:
    """
    https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Euler_Angles_to_Quaternion_Conversion
    tensor contains floats (unit: rad) representing an orientation in Euler angles with ZYX rotation order (Tait-Bryan)
    :return:
    """
    # the old code was too inaccurate, leading to rounding errors of 2-3 degrees
    euler_zyx = torch.deg2rad(euler_zyx) if degrees else euler_zyx
    mat = py3dtransforms.euler_angles_to_matrix(euler_zyx.flip(-1), convention="ZYX")
    return rotation_matrix_to_quaternion(mat)


def quaternion_to_euler(q: torch.Tensor, convention: str) -> torch.Tensor:
    return matrix_to_euler_angles(quaternion_to_rotation_matrix(q), convention=convention)


def euler_to_quaternion(q: torch.Tensor, convention: str) -> torch.Tensor:
    return rotation_matrix_to_quaternion(py3dtransforms.euler_angles_to_matrix(q, convention))


def map_rad_rotations(rot: torch.Tensor) -> torch.Tensor:
    """Map the rotations to [-pi, pi]

    :param rot: tensor with rotations in radian
    :return: mapped tensor
    """
    return (rot + torch.pi) % (2 * torch.pi) - torch.pi


def quaternion_to_euler_zyx(q: torch.Tensor) -> torch.Tensor:
    """
    Convert q quaternion (w,x,y,z) to Euler angles (ZYX convention, in radians, normalized to [-pi, pi])
    https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Quaternion_to_Euler_Angles_Conversion
    :param q: Quaternion (w,x,y,z)
    :return Euler angles (ZYX convention, in radians, normalized to [-pi, pi])
    """
    rotations = matrix_to_euler_angles(quaternion_to_rotation_matrix(q), convention="ZYX").flip(-1)
    return rotations


def pose_inverse(pose: torch.Tensor) -> torch.Tensor:
    return affine_to_pose(affine_inverse(pose_to_affine(pose)))


def translation_to_affine(translation: torch.Tensor) -> torch.Tensor:
    quat = torch.zeros((*translation.shape[:-1], 4))
    quat[..., 0] = 1
    return pose_to_affine(torch.concat((translation, quat), dim=-1))


def pose_to_affine(pose: torch.Tensor) -> torch.Tensor:
    assert pose.shape[-1] == 7
    rot = quaternion_to_rotation_matrix(pose[..., 3:])
    trans = pose[..., :3].unsqueeze(-1)
    # torch.eye doesn't work as it does not retain grads
    affine = torch.as_tensor([0, 0, 0, 1], dtype=pose.dtype, device=pose.device).repeat((*pose.shape[:-1], 1, 1))
    affine = torch.concat((torch.concat((rot, trans), dim=-1), affine), dim=-2)
    return affine


def affine_to_pose(affine: torch.Tensor) -> torch.Tensor:
    quat = rotation_matrix_to_quaternion(affine[..., :3, :3])
    return torch.cat((affine[..., :3, 3], quat), dim=-1)


def affine_inverse(affine: torch.Tensor) -> torch.Tensor:
    affine = affine.clone()
    rot_inv = affine[..., :3, :3].transpose(-1, -2).clone()  # clone required since slice will not copy data
    trans_inv = -torch.bmm(rot_inv.view(-1, 3, 3), affine[..., :3, 3].view(-1, 3, 1)).view(*affine.shape[:-2], 3)
    affine[..., :3, :3] = rot_inv
    affine[..., :3, 3] = trans_inv
    return affine


def pose_euler_zyx_to_affine(pose_euler_zyx: torch.Tensor, degrees=False) -> torch.Tensor:
    quaternions = euler_zyx_to_quaternion(pose_euler_zyx[..., 3:6], degrees)
    return pose_to_affine(torch.cat((pose_euler_zyx[..., :3], quaternions), dim=-1))


def affine_to_pose_euler_zyx(affine: torch.Tensor) -> torch.Tensor:
    poses = affine_to_pose(affine)
    euler_zyx = quaternion_to_euler_zyx(poses[..., 3:7])
    return torch.cat((poses[..., :3], euler_zyx), dim=-1)


def affine_transform(pose_left: torch.Tensor, pose_right: torch.Tensor):
    """
    :param pose_left: Transform in world coordinates, else pose
    :param pose_right: Transform in local coordinates, else pose
    """
    tf_left = pose_left if len(pose_left.size()) >= 3 and is_4_by_4_matrix(pose_left) else pose_to_affine(pose_left)
    tf_right = (
        pose_right if len(pose_right.size()) >= 3 and is_4_by_4_matrix(pose_right) else pose_to_affine(pose_right)
    )
    transformed = tf_left.matmul(tf_right)
    return affine_to_pose(transformed)


def absolute_to_relative(pose: torch.Tensor, reference: torch.Tensor) -> torch.Tensor:
    pose_affine = pose_to_affine(pose)
    reference_affine = pose_to_affine(reference)
    relative_affine = reference_affine.inverse().matmul(pose_affine)
    return affine_to_pose(relative_affine)


def relative_to_absolute(relative_pose: torch.Tensor, reference: torch.Tensor) -> torch.Tensor:
    relative_pose_affine = pose_to_affine(relative_pose)
    reference_affine = pose_to_affine(reference)
    absolute_affine = torch.matmul(reference_affine, relative_pose_affine)
    return affine_to_pose(absolute_affine)


def rotation_from_axis_angle(axis: torch.Tensor, angle: torch.Tensor) -> torch.Tensor:
    return py3dtransforms.axis_angle_to_matrix(axis * angle)


def axis_angle_from_quaternion(quat: torch.Tensor) -> torch.Tensor:
    return py3dtransforms.quaternion_to_axis_angle(quat)


def quaternion_from_axis_angle(axis_angle: torch.Tensor) -> torch.Tensor:
    return py3dtransforms.axis_angle_to_quaternion(axis_angle)


def axis_angle_from_rotation(m: torch.Tensor, eps=0.000001) -> tuple:
    epsilon = eps  # Margin to allow for rounding errors
    epsilon2 = eps * 10  # Margin to distinguish between 0 and 180 degrees
    if abs(m[0, 1] - m[1, 0]) < epsilon and abs(m[0, 2] - m[2, 0]) < epsilon and abs(m[1, 2] - m[2, 1]) < epsilon:
        # singularity found
        # first check for identity matrix which must have +1 for all terms
        # in leading diagonal and zero in other terms
        if (
            abs(m[0, 1] + m[1, 0]) < epsilon2
            and abs(m[0, 2] + m[2, 0]) < epsilon2
            and abs(m[1, 2] + m[2, 1]) < epsilon2
            and abs(m[0, 0] + m[1, 1] + m[2, 2] - 3) < epsilon2
        ):
            # this singularity is identity matrix so angle = 0
            return torch.tensor([1, 0, 0], device=m.device), 0
        # otherwise this singularity is angle = 180
        angle = math.pi
        xx = (m[0, 0] + 1) / 2
        yy = (m[1, 1] + 1) / 2
        zz = (m[2, 2] + 1) / 2
        xy = (m[0, 1] + m[1, 0]) / 4
        xz = (m[0, 2] + m[2, 0]) / 4
        yz = (m[1, 2] + m[2, 1]) / 4
        if xx > yy and xx > zz:
            # m[0, 0] is the largest diagonal term
            if xx < epsilon:
                x = 0
                y = 0.7071
                z = 0.7071
            else:
                x = torch.sqrt(xx)
                y = xy / x
                z = xz / x
        elif yy > zz:
            # m[1, 1] is the largest diagonal term
            if yy < epsilon:
                x = 0.7071
                y = 0
                z = 0.7071
            else:
                y = torch.sqrt(yy)
                x = xy / y
                z = yz / y
        else:
            # m[2, 2] is the largest diagonal term so base result on this
            if zz < epsilon:
                x = 0.7071
                y = 0.7071
                z = 0
            else:
                z = torch.sqrt(zz)
                x = xz / z
                y = yz / z
        return torch.stack((x, y, z)), angle  # return 180 deg rotation
    # as we have reached here there are no singularities so we can handle normally
    s = torch.sqrt(
        (m[2, 1] - m[1, 2]) * (m[2, 1] - m[1, 2])
        + (m[0, 2] - m[2, 0]) * (m[0, 2] - m[2, 0])
        + (m[1, 0] - m[0, 1]) * (m[1, 0] - m[0, 1])
    )  # used to normalise
    if abs(s) < 0.001:
        # prevent divide by zero, should not happen if matrix is orthogonal and should be caught by
        # singularity test above, but I've left it in just in case
        s = 1

    # AcosBackward returns inf/-inf when input exactly equals 1/-1
    arg = torch.clamp((m[0, 0] + m[1, 1] + m[2, 2] - 1) / 2, -1.0 + epsilon, 1.0 - epsilon)
    angle = torch.acos(arg)
    x = (m[2, 1] - m[1, 2]) / s
    y = (m[0, 2] - m[2, 0]) / s
    z = (m[1, 0] - m[0, 1]) / s
    return torch.stack((x, y, z)), angle


def quaternion_distance(q1: torch.Tensor, q2: torch.Tensor) -> torch.Tensor:
    """
    Return angle theta between quaternions q1 and q2
    https://math.stackexchange.com/a/90098
    """
    q1_normalized = q1 / torch.norm(q1, dim=-1, keepdim=True)
    q2_normalized = q2 / torch.norm(q2, dim=-1, keepdim=True)
    dot_products = torch.sum(q1_normalized * q2_normalized, -1)
    acos_arg = 2 * (dot_products**2) - torch.ones(dot_products.size(), device=dot_products.device)
    return torch.acos(torch.clamp(acos_arg, -1 + 1e-7, 1 - 1e-7))


def compute_relative_offset(pose: torch.Tensor, relative_to: torch.Tensor) -> torch.Tensor:
    relative_affine = pose_to_affine(relative_to)
    pose_affine = pose_to_affine(pose)
    pose_relative_affine = affine_inverse(relative_affine) @ pose_affine
    pose_relative = affine_to_pose(pose_relative_affine)
    return pose_relative


def get_cross_prod_mat(pVec_Arr):
    # pVec_Arr shape (3)
    qCross_prod_mat = np.array(
        [
            [0, -pVec_Arr[2], pVec_Arr[1]],
            [pVec_Arr[2], 0, -pVec_Arr[0]],
            [-pVec_Arr[1], pVec_Arr[0], 0],
        ]
    )
    return qCross_prod_mat


def calculate_align_mat(pVec_Arr):
    scale = np.linalg.norm(pVec_Arr)
    pVec_Arr = pVec_Arr / scale
    # must ensure pVec_Arr is also a unit vec.
    z_unit_Arr = np.array([0, 0, 1])
    z_mat = get_cross_prod_mat(z_unit_Arr)

    z_c_vec = np.matmul(z_mat, pVec_Arr)
    z_c_vec_mat = get_cross_prod_mat(z_c_vec)

    if np.dot(z_unit_Arr, pVec_Arr) == -1:
        qTrans_Mat = -np.eye(3, 3)
    elif np.dot(z_unit_Arr, pVec_Arr) == 1:
        qTrans_Mat = np.eye(3, 3)
    else:
        qTrans_Mat = (
            np.eye(3, 3) + z_c_vec_mat + np.matmul(z_c_vec_mat, z_c_vec_mat) / (1 + np.dot(z_unit_Arr, pVec_Arr))
        )

    qTrans_Mat *= scale
    return qTrans_Mat


def matrix_to_euler_angles(matrix: torch.Tensor, convention: str) -> torch.Tensor:
    return py3dtransforms.matrix_to_euler_angles(matrix, convention)


def pose_quaternion_to_euler_zyx(pose: torch.Tensor) -> torch.Tensor:
    """
    Convert a pose of format (x,y,z,qw,qx,qy,qz) into a pose of format (x,y,z,rx,ry,rz)
    where the orientation is expressed in Euler angles (ZYX convention).
    :param pose: Pose of format (x,y,z,qw,qx,qy,qz)
    :return: Pose of format (x,y,z,rx,ry,rz)
    """
    return torch.concat((pose[..., :3], quaternion_to_euler_zyx(pose[..., 3:7])), dim=-1)


def pose_quaternion_to_euler(pose: torch.Tensor, convention: str) -> torch.Tensor:
    """
    Convert a pose of format (x,y,z,qw,qx,qy,qz) into a pose of format (x,y,z,rx,ry,rz)
    where the orientation is expressed in Euler angles (ZYX convention).
    :param pose: Pose of format (x,y,z,qw,qx,qy,qz)
    :return: Pose of format (x,y,z,rx,ry,rz)
    """
    return torch.concat((pose[..., :3], quaternion_to_euler(pose[..., 3:7], convention)), dim=-1)


def pose_euler_zyx_to_quaternion(pose: torch.Tensor) -> torch.Tensor:
    return torch.concat((pose[..., :3], euler_zyx_to_quaternion(pose[..., 3:6])), dim=-1)


def pose_euler_to_quaternion(pose: torch.Tensor, convention: str) -> torch.Tensor:
    """
    Convert a pose of format (x,y,z,rx,ry,rz) where the orientation is expressed in Euler angles (ZYX convention)
    into a pose of format (x,y,z,qw,qx,qy,qz).
    :param pose: Pose of format (x,y,z,rx,ry,rz)
    :return: Pose of format (x,y,z,qw,qx,qy,qz)
    """
    return torch.concat((pose[..., :3], euler_to_quaternion(pose[..., 3:6], convention)), dim=-1)
