try:
    from OCC.Core.BRepTools import breptools_ReadFromString, breptools_WriteToString
    from OCC.Core.TopoDS import TopoDS_Shape
except Exception:
    pass


class CADShapeBinarizer:
    """convert occ shape to base64 str and bac"""

    @staticmethod
    def shape_to_base64(shape: "TopoDS_Shape") -> str:
        # Serialize the shape to a binary stream
        string = breptools_WriteToString(shape)
        return string

    @staticmethod
    def base64_to_shape(base64_string: str) -> "TopoDS_Shape":
        # Decode the base64 string back to a binary stream
        return breptools_ReadFromString(base64_string)
