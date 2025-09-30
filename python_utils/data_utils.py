import copy
import io
import base64
from dataclasses import fields
from enum import Enum
from typing import Any, Type, TypeVar, Union, Optional
from PIL import Image


def _is_dataclass_instance(obj) -> bool:
    """Returns True if obj is an instance of a dataclass."""
    return hasattr(type(obj), "__dataclass_fields__")


# extended implementation from dataclasses package


def asdict(obj, *, dict_factory=dict):
    """Return the fields of a dataclass instance as a new dictionary mapping
    field names to field values.

    Example usage::

      @dataclass
      class C:
          x: int
          y: int

      c = C(1, 2)
      assert asdict(c) == {'x': 1, 'y': 2}

    If given, 'dict_factory' will be used instead of built-in dict.
    The function applies recursively to field values that are
    dataclass instances. This will also look into built-in containers:
    tuples, lists, and dicts.
    """
    if not _is_dataclass_instance(obj):
        raise TypeError("asdict() should be called on dataclass instances")
    return _asdict_inner(obj, dict_factory)


def _asdict_inner(obj, dict_factory):
    if _is_dataclass_instance(obj):
        result = []
        for f in fields(obj):
            value = _asdict_inner(getattr(obj, f.name), dict_factory)
            result.append((f.name, value))
        return dict_factory(result)
    elif isinstance(obj, tuple) and hasattr(obj, "_fields"):
        # obj is a namedtuple.  Recurse into it, but the returned
        # object is another namedtuple of the same type.  This is
        # similar to how other list- or tuple-derived classes are
        # treated (see below), but we just need to create them
        # differently because a namedtuple's __init__ needs to be
        # called differently (see bpo-34363).

        # I'm not using namedtuple's _asdict()
        # method, because:
        # - it does not recurse in to the namedtuple fields and
        #   convert them to dicts (using dict_factory).
        # - I don't actually want to return a dict here.  The main
        #   use case here is json.dumps, and it handles converting
        #   namedtuples to lists.  Admittedly we're losing some
        #   information here when we produce a json list instead of a
        #   dict.  Note that if we returned dicts here instead of
        #   namedtuples, we could no longer call asdict() on a data
        #   structure where a namedtuple was used as a dict key.

        return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])
    elif isinstance(obj, (list, tuple)):
        # Assume we can create an object of this type by passing in a
        # generator (which is not true for namedtuples, handled
        # above).
        return type(obj)(_asdict_inner(v, dict_factory) for v in obj)
    elif isinstance(obj, dict):
        return type(obj)((_asdict_inner(k, dict_factory), _asdict_inner(v, dict_factory)) for k, v in obj.items())
    elif isinstance(obj, Enum):
        return obj.value
    else:
        return copy.deepcopy(obj)


T = TypeVar("T")


def fromdict(obj, dataclass: Type[T]) -> T:
    """map dict to `dataclass` instance

    this can load a dataclass instance from dict.
    For some variables (like custom classes that are no dataclass or subclasses),
    the variable with `variable-name_factory` can be used to define a factory for
    the variable `variable-name`

    :param obj: object as dictionary to load as `dataclass`
    :param dataclass: type of class that should be used for loading
    """
    if hasattr(dataclass, f"from_json"):
        return dataclass.from_json(obj)
    if hasattr(dataclass, "__dataclass_fields__"):  # is dataclass type
        kwargs = {}
        for f in fields(dataclass):
            value = obj[f.name]
            if hasattr(dataclass, f"{f.name}_factory"):
                datatype = getattr(dataclass, f"{f.name}_factory")(value)
            else:
                datatype = f.type
            kwargs[f.name] = fromdict(obj=value, dataclass=datatype)
        return dataclass(**kwargs)
    if dataclass == Any:
        return obj
    if getattr(dataclass, "_name", None) == "List":
        return [fromdict(obj=item, dataclass=dataclass.__args__[0]) for item in obj]
    if issubclass(dataclass, str) and isinstance(obj, bytes):
        obj = obj.decode()
    if any(issubclass(dataclass, t) for t in [str, int, float, bool]):
        return dataclass(obj)

    raise NotImplementedError()


def base64_to_image(data: str) -> Image.Image:
    image_data = base64.b64decode(data)
    return Image.open(io.BytesIO(image_data))


def dict_similar(dict1: Union[dict, list], dict2: Union[dict, list], tolerance: float = 1e-9, ignore_keys: Optional[list[str]] = None) -> bool:
    """
    Check whether two dictionaries or lists are similar.

    Similarity rules:
    - For dicts: all keys must match, and all values must be similar (recursively)
    - For lists/tuples: all elements must be similar (recursively)
    - For int/float: values must be within the specified tolerance
    - For all other types: equality is used

    Args:
        dict1: First dict or list to compare
        dict2: Second dict or list to compare
        tolerance: Tolerance for numerical comparisons (default: 1e-9)

    Returns:
        True if similar, False otherwise

    Example:
        >>> dict_similar({'a': 0.04, 'b': 1}, {'a': 0.06, 'b': 1}, tolerance=0.02)
        True
        >>> dict_similar([0.04, 1], [0.06, 1], tolerance=0.02)
        True
        >>> dict_similar({'a': [0.04, 1]}, {'a': [0.06, 1]}, tolerance=0.02)
        True
    """
    # Handle dicts
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        if set(dict1.keys()) != set(dict2.keys()):
            return False
        for key in dict1.keys():
            item_tolerance = tolerance
            if ignore_keys is not None and key in ignore_keys:
                continue

            if not dict_similar(dict1[key], dict2[key], item_tolerance, ignore_keys):
                return False
        return True
    # Handle lists/tuples
    elif isinstance(dict1, (list, tuple)) and isinstance(dict2, (list, tuple)):
        if len(dict1) != len(dict2):
            return False
        for item1, item2 in zip(dict1, dict2):
            if not dict_similar(item1, item2, tolerance, ignore_keys):
                return False
        return True
    # Handle numerical types with tolerance
    elif isinstance(dict1, (int, float)) and isinstance(dict2, (int, float)):
        return abs(dict1 - dict2) <= tolerance
    # Fallback to equality
    else:
        return dict1 == dict2