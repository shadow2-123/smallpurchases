from dataclasses import dataclass
from typing import Dict, List


@dataclass
class DocumentParseResult:
    products_list: List[Dict[str, str]] | None
    delivery_term: str | None