from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Product:
    name: str
    quantity: str | None
    unit: str | None

@dataclass
class DocumentParseResult:
    products_list: List[Product]
    delivery_term: str | None

@dataclass
class Table:
    rows: List[List[str]]

@dataclass
class ParsedDocumentText:
    paragraphs: List[str]
    tables: List[Table]