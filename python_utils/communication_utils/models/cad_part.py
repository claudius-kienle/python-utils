from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import reduce
from typing import Any, Dict, List, Optional

import numpy as np

from llm_utils.communication_utils.models.directions import Direction
from llm_utils.communication_utils.models.unique_color_supplier import Color, UniqueColorSupplier
from llm_utils.communication_utils.models.view_orientation import ViewOrientation
from llm_utils.communication_utils.utils.color_utils import get_color_name


class CADFaceType(int, Enum):
    PLANE = 1
    CYLINDER = 2
    TORUS = 3
    SPHERE = 4
    CONE = 5
    BEZIER_SURFACE = 6
    BSPLINE_SURFACE = 7
    SURFACE_OF_REVOLUTION = 8
    OFFSET_SURFACE = 9
    SURFACE_OF_EXTRUSION = 10
    OTHER_SURFACE = 11


@dataclass
class CADFaceTypeMeta:
    type: CADFaceType = field(init=False)


@dataclass
class CADFaceTypeOtherMeta:
    type: CADFaceType

    def __post_init__(self):
        self.type = CADFaceType(self.type)


@dataclass
class CADFaceTypeCylinderMeta(CADFaceTypeMeta):
    radius: float

    def __post_init__(self):
        self.type = CADFaceType.CYLINDER


class CADFaceTypeFactory:
    def from_dict(self, dict: Dict) -> "CADFaceTypeMeta":
        if dict["type"] == CADFaceType.CYLINDER:
            del dict["type"]
            return CADFaceTypeCylinderMeta(**dict)
        else:
            return CADFaceTypeOtherMeta(**dict)


@dataclass
class BoundingBox:
    min_point: List[float]
    max_point: List[float]

    @property
    def center(self) -> List[float]:
        mins = np.asarray(self.min_point)
        maxs = np.asarray(self.max_point)
        center = mins + (maxs - mins) / 2
        return center.tolist()

    @property
    def extents(self) -> List[float]:
        mins = np.asarray(self.min_point)
        maxs = np.asarray(self.max_point)
        extents = maxs - mins
        return np.round(extents, decimals=5).tolist()

    def get_point_for_direction(self, direction: Direction) -> List[float]:
        point = self.center
        if direction == Direction.TOP:
            point[2] = self.max_point[2]
        elif direction == Direction.BOTTOM:
            point[2] = self.min_point[2]
        elif direction == Direction.LEFT:
            point[0] = self.min_point[0]
        elif direction == Direction.RIGHT:
            point[0] = self.max_point[0]
        elif direction == Direction.FRONT:
            point[1] = self.min_point[1]
        elif direction == Direction.BACK:
            point[1] = self.max_point[1]
        elif direction == Direction.CENTER:
            pass
        return point

    @staticmethod
    def from_dict(data: Dict) -> "BoundingBox":
        return BoundingBox(**data)

    def unify(self, other: "BoundingBox") -> "BoundingBox":
        new_mins = [min(v1, v2) for v1, v2 in zip(self.min_point, other.min_point)]
        new_maxs = [max(v1, v2) for v1, v2 in zip(self.max_point, other.max_point)]

        return BoundingBox(min_point=new_mins, max_point=new_maxs)


@dataclass
class CADEdge:
    length: float
    center_of_mass: List[float]

    @staticmethod
    def from_dict(data: Dict) -> "CADEdge":
        return CADEdge(**data)


@dataclass
class CADFace:
    # center of mass in meters relative to cad coordinate system
    bbox: BoundingBox
    id: int
    face_type: CADFaceTypeMeta
    edges: List[CADEdge]
    color: Color

    @staticmethod
    def from_dict(data: Dict) -> "CADFace":
        return CADFace(
            id=data["id"],
            bbox=BoundingBox.from_dict(data["bbox"]),
            face_type=CADFaceTypeFactory().from_dict(data["face_type"]),
            edges=list(map(CADEdge.from_dict, data["edges"])),
            color=data["color"],
        )

    @property
    def center_of_mass(self) -> List[float]:
        return self.bbox.center

    def copy_with(self, color: Optional[Color]) -> "CADFAce":
        if color is None:
            color = self.color

        return CADFace(bbox=self.bbox, id=self.id, face_type=self.face_type, edges=self.edges, color=color)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, CADFace):
            return self.id == other.id
        return False

    def __hash__(self):
        return self.id


@dataclass
class CADPart:
    cad_faces: List[CADFace]
    bounding_box: BoundingBox
    color: Color
    to_dict = asdict
    side: List[ViewOrientation]

    @property
    def id(self) -> int:
        return hash(reduce(lambda a, b: a + b, list(map(lambda face: face.id, self.cad_faces))))

    @property
    def center_of_mass(self) -> List[float]:
        return self.bounding_box.center

    @property
    def color_name(self) -> str:
        return get_color_name(self.color)

    def get_point_for_direction(self, direction: Direction) -> List[float]:
        return self.bounding_box.get_point_for_direction(direction=direction)

    @property
    def display_name(self) -> str:
        return self.color_name

    @staticmethod
    def from_dict(data: Dict) -> "CADPart":
        return CADPart(
            bounding_box=BoundingBox.from_dict(data["bounding_box"]),
            cad_faces=[CADFace.from_dict(entry) for entry in data["cad_faces"]],
            color=data["color"],
            side=[ViewOrientation(item) for item in data["side"]],
        )

    @staticmethod
    def copy_with_new_color(part: "CADPart", color: Optional[Color] = None) -> "CADPart":
        if color is None:
            color = UniqueColorSupplier.get_instance().get_color()
        return CADPart(
            bounding_box=part.bounding_box,
            cad_faces=part.cad_faces,
            color=color,
            side=part.side,
        )

    def copy_with(self, cad_faces: Optional[List[CADFace]]) -> "CADPart":
        if cad_faces is None:
            cad_faces = self.cad_faces

        return CADPart(
            bounding_box=self.bounding_box,
            cad_faces=cad_faces,
            color=self.color,
            side=self.side,
        )

    def overlaps(self, other: "CADPart") -> bool:
        for this_face in self.cad_faces:
            for other_face in other.cad_faces:
                if this_face.id == other_face.id:
                    return True

    def unify(self, other: "CADPart") -> "CADPart":
        return CADPart(
            bounding_box=self.bounding_box.unify(other.bounding_box),
            cad_faces=list(set(self.cad_faces + other.cad_faces)),
            color=self.color,
            side=list(set(self.side + other.side)),
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, CADPart):
            return self.id == other.id
        return False
