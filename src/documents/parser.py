import re
from pathlib import Path
from typing import List, Any
from office_oxide import Document
from documents.schemas import DocumentParseResult, ParsedDocumentText, Product, Table


class DocumentParser:
    def parse(self, data: bytes, filename: str) -> DocumentParseResult:
        suffix = Path(filename).suffix.lower()

        if suffix not in {".doc", ".docx"}:
            return DocumentParseResult(
                products_list=[],
                delivery_term=None,
            )

        document = self._read(data, suffix.lstrip("."))

        products_list = self._find_products(document)
        delivery_term = self._find_delivery_term(document)

        return DocumentParseResult(
            products_list=products_list,
            delivery_term=delivery_term,
        )

    def _read(self, data: bytes, format_: str) -> ParsedDocumentText:
        with Document.from_bytes(data, format_) as document:
            ir = document.to_ir()

        paragraphs = []
        tables = []

        for section in ir.get("sections", []):
            for element in section.get("elements", []):
                element_type = element.get("type")

                if element_type in {"paragraph", "heading"}:
                    text = self._extract_text(element.get("content", []))

                    if text:
                        paragraphs.append(text)

                elif element_type == "table":
                    rows = []

                    for row in element.get("rows", []):
                        cells = []

                        for cell in row.get("cells", []):
                            text = self._extract_text(
                                cell.get("content", [])
                            )
                            cells.append(text)

                        rows.append(cells)

                    tables.append(Table(rows=rows))

        return ParsedDocumentText(
            paragraphs=paragraphs,
            tables=tables,
        )

    def _find_products(self, document: ParsedDocumentText) -> List[Product]:
        pass

    def _find_delivery_term(
            self,
            document: ParsedDocumentText,
    ) -> str | None:
        delivery_keywords = (
            "срок поставки",
            "сроки поставки",
            "срок исполнения контракта",
            "поставка товара",
            "поставить товар",
            "поставка осуществляется",
            "поставка производится",
            "поставка должна быть",
            "передачи",
        )

        candidates = list(document.paragraphs)

        for table in document.tables:
            for row in table.rows:
                text = " ".join(cell for cell in row if cell)
                if text:
                    candidates.append(text)

        for text in candidates:
            normalized = self._normalize_text(text)
            lower = normalized.lower()

            if any(keyword in lower for keyword in delivery_keywords):
                return normalized

        return None

    def _extract_text(self, content: list[dict[str, Any]]) -> str:
        parts = []

        for item in content:
            if item.get("type") == "text":
                parts.append(item.get("text", ""))

            elif item.get("type") == "line_break":
                parts.append(" ")

            if "content" in item:
                parts.append(
                    self._extract_text(item["content"])
                )

        return " ".join(
            "".join(parts).split()
        )
    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()