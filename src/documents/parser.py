from pathlib import Path
from typing import List, Dict, Tuple

from documents.schemas import DocumentParseResult, ParsedDocumentText, Product


class DocumentParser:
    def parse(self, data: bytes, filename: str) -> DocumentParseResult:
        suffix = Path(filename).suffix.lower()

        if suffix == ".docx":
            paragraphs, tables = self._read_docx(data)
        elif suffix == ".doc":
            paragraphs, tables = self._read_doc(data)
        else:
            return DocumentParseResult(products_list=[], delivery_term=None)

        products_list = self._find_products(paragraphs, tables)
        delivery_term = self._find_delivery_term(paragraphs, tables)

        return DocumentParseResult(
            products_list=products_list,
            delivery_term=delivery_term,
        )

    def _read_doc(self, data: bytes) -> ParsedDocumentText:
        pass

    def _read_docx(self, data: bytes) -> ParsedDocumentText:
        pass

    def _find_products(self, document: ParsedDocumentText) -> List[Product]:
        pass

    def _find_delivery_term(self, document: ParsedDocumentText) -> str:
        pass