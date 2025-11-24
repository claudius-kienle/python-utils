from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from llm_utils.communication_utils.models.cad_part import CADPart


@dataclass
class QueryPointsOfObjectResponse:
    parts: Optional[List[CADPart]]
    points: List[List[float]]
    to_dict = asdict

    @staticmethod
    def from_dict(data: Dict) -> "QueryPointsOfObjectResponse":
        return QueryPointsOfObjectResponse(
            parts=[CADPart.from_dict(e) for e in data["parts"]] if data["parts"] is not None else None,
            points=data["points"],
        )
