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
                delivery_terms=[],
                delivery_places=[]
            )

        document = self._read(data, suffix.lstrip("."))

        products_list = self._find_products(document)
        delivery_terms = self._find_delivery_terms(document)
        delivery_places = self._find_delivery_places(document)

        delivery_places = [
            place
            for place in delivery_places
            if place not in delivery_terms
        ]

        return DocumentParseResult(
            products_list=products_list,
            delivery_terms=delivery_terms,
            delivery_places=delivery_places,
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
                        paragraphs.extend(
                            self._split_paragraph(text)
                        )

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

    def _find_delivery_terms(
            self,
            document: ParsedDocumentText,
    ) -> List[str]:
        delivery_keywords = (
            "срок поставки",
            "сроки поставки",
            "срок передачи",
            "сроки передачи",
            "срок исполнения контракта",
            "поставка товара",
            "поставить товар",
            "поставка осуществляется",
            "поставка производится",
            "поставка должна быть",
            "доставляет товар",
            "доставка товара",
            "поставка товара силами",
            "поставка товара по адресу заказчика",
        )

        candidates = list(document.paragraphs)

        for table in document.tables:
            for row in table.rows:
                text = " ".join(cell for cell in row if cell)

                if text:
                    candidates.extend(
                        self._split_paragraph(text)
                    )

        result = []

        for text in candidates:
            normalized = self._normalize_text(text)
            lower = normalized.lower()

            if not any(
                    keyword in lower
                    for keyword in delivery_keywords
            ):
                continue

            if not self._has_time_expression(normalized):
                continue

            result.append(normalized)

        return result

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

    @staticmethod
    def _has_time_expression(text: str) -> bool:
        lower = text.lower()

        time_keywords = (
            "в течение",
            "в течении",
            "не позднее",
            "однократно до",
            "однократно, до",
            "в период с",
            "календарных дней",
            "рабочих дней",
        )

        if any(keyword in lower for keyword in time_keywords):
            return True

        return bool(
            re.search(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b", text)
        )

    def _find_delivery_places(
            self,
            document: ParsedDocumentText,
    ) -> List[str]:
        delivery_place_keywords = (
            "место поставки",
            "место доставки",
            "адрес поставки",
            "адрес доставки",
            "доставляет товар заказчику по адресу",
            "доставка товара по адресу",
            "поставка товара по адресу",
            "передача товара осуществляется по адресу",
            "передача товара по адресу",
            "поставка товара силами",
            "поставка товара по адресу заказчика",
        )

        candidates = list(document.paragraphs)

        for table in document.tables:
            for row in table.rows:
                text = " ".join(cell for cell in row if cell)

                if text:
                    candidates.extend(
                        self._split_paragraph(text)
                    )

        result = []

        for text in candidates:
            normalized = self._normalize_text(text)
            lower = normalized.lower()

            if any(
                    keyword in lower
                    for keyword in delivery_place_keywords
            ):
                result.append(normalized)

        return result

    @staticmethod
    def _split_paragraph(text: str) -> List[str]:
        parts = re.split(
            r"(?=(?<!\d)[1-9](?:\.\d{1,2})+\.\s*[А-ЯЁA-Z])",
            text,
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]