import logging
from enum import Enum
from typing import Dict, List, Literal, Optional, Type, TypeVar, Union, overload

import dicttoxml
import xmltodict


def to_dict(data) -> Dict:
    if data is None:
        return None
    if isinstance(data, list) or isinstance(data, tuple):
        return [to_dict(item) for item in data]
    elif isinstance(data, dict):
        return {key: to_dict(value) for key, value in data.items()}
    elif isinstance(data, Enum):
        return data.value
    elif isinstance(data, int) or isinstance(data, str) or isinstance(data, float):
        return data
    else:
        assert hasattr(data, "to_dict"), data.__module__
        return to_dict(data.to_dict())


def obj_to_xml(obj) -> Optional[str]:
    if obj is not None:
        logging.getLogger("dicttoxml").setLevel(logging.WARN)
        return dicttoxml.dicttoxml(to_dict(obj))
    else:
        None


def _parse_back(data):
    if isinstance(data, list):
        return [_parse_back(entry) for entry in data]
    elif isinstance(data, dict):
        if "@type" not in data:
            return {k: _parse_back(v) for k, v in data.items()}
        elif data["@type"] == "dict":
            return {key: _parse_back(value) for key, value in data.items() if not key.startswith("@")}
        elif data["@type"] == "list":
            if isinstance(data["item"], list):
                return [_parse_back(entry) for entry in data["item"]]
            else:
                # only one item
                return [_parse_back(data["item"])]
        elif data["@type"] == "str":
            return data["#text"]
        elif data["@type"] == "float":
            return float(data["#text"])
        elif data["@type"] == "int":
            return int(data["#text"])
        elif data["@type"] == "null":
            return None
        else:
            raise NotImplementedError(data["@type"])
    raise NotImplementedError(data)


T = TypeVar("T")


@overload
def xml_to_obj(xml: str, object_class: Type[T], many: Literal[False] = False) -> Optional[T]:
    ...


@overload
def xml_to_obj(xml: str, object_class: Type[T], many: Literal[True] = False) -> Optional[List[T]]:
    ...


def xml_to_obj(xml: str, object_class: Type[T], many: bool = False) -> Union[Optional[T], Optional[List[T]]]:
    json = xmltodict.parse(xml)

    if json["root"] is None:
        return None

    if not "item" in json["root"]:
        parsed_json = _parse_back(json["root"])
    else:
        parsed_json = _parse_back(json["root"]["item"])

    if not isinstance(parsed_json, list) and not isinstance(parsed_json, dict):
        return object_class(parsed_json)

    primitives = (bool, str, int, float, type(None))

    if isinstance(parsed_json, object_class):
        return parsed_json

    if many:
        if not isinstance(parsed_json, list):
            # will contain object directly if list only contains one element
            if object_class in primitives:
                return object_class(parsed_json)
            else:
                assert hasattr(object_class, "from_dict")
                return [object_class.from_dict(parsed_json)]
        else:
            if object_class in primitives:
                return [object_class(entry) for entry in parsed_json]
            else:
                assert hasattr(object_class, "from_dict")
                return [object_class.from_dict(entry) for entry in parsed_json]
    else:
        assert hasattr(object_class, "from_dict")
        return object_class.from_dict(parsed_json)
