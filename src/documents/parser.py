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

        products_list = []
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
        return []

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
            "доставка и разгрузка",
            "поставка производится",
            "поставка должна быть",
            "доставляет товар",
            "доставка товара",
            "поставка товара силами",
            "поставка товара по адресу заказчика",
            "продукция доставляется",
        )

        candidates = self._candidates(document)

        result = []

        for text in candidates:
            normalized = self._normalize_text(text)
            lower = normalized.lower()

            explicit_term = re.search(
                r"^(?:\d+(?:\.\d+)*\.?\s*)?срок(?:и|а|ов)?\s+(?:поставки|доставки|передачи|исполнения контракта)",
                lower,
            )
            delivery = any(keyword in lower for keyword in delivery_keywords) or re.search(
                r"\b(?:товар\w*|продукци\w*)\s+(?:поставля\w*|доставля\w*)", lower
            )
            if not explicit_term and not (delivery and self._has_time_expression(normalized)):
                continue

            result.append(normalized)

        return self._unique(result)

    def _extract_text(self, content: list[dict[str, Any]]) -> str:
        # Runs are adjacent pieces of a word; paragraphs are separate blocks.
        parts = []
        for item in content:
            kind = item.get("type")
            if kind == "text":
                parts.append(item.get("text", ""))
            elif kind == "line_break":
                parts.append("\n")
            if "content" in item:
                nested = self._extract_text(item["content"])
                if kind in {"paragraph", "heading"}:
                    parts.extend(["\n", nested, "\n"])
                else:
                    parts.append(nested)
        return "".join(parts)

    def _candidates(self, document: ParsedDocumentText) -> List[str]:
        candidates = list(document.paragraphs)
        for table in document.tables:
            for row in table.rows:
                text = " ".join(cell.strip() for cell in row if cell.strip())
                candidates.extend(self._split_paragraph(text))
        return candidates

    def _unique(self, texts: List[str]) -> List[str]:
        result = []
        seen = set()
        for text in texts:
            text = self._normalize_text(text)
            key = text.casefold().replace("ё", "е")
            if key and key not in seen:
                result.append(text)
                seen.add(key)
        return result

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _has_time_expression(text: str) -> bool:
        lower = re.sub(
            r"\bот\s+\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\s*(?:г(?:ода|\.)?\s*)?№\s*[\w-]+",
            "", text.lower(),
        )

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

        return bool(re.search(
            r"\b(?:0?[1-9]|[12]\d|3[01])[./-](?:0?[1-9]|1[0-2])[./-](?:\d{4}|\d{2})\b"
            r"|\b\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b"
            r"|\b(?:через|за)\s+\d+\s*(?:\([^)]*\)\s*)?(?:(?:рабочих|календарных)\s+)?(?:дн|день|недел|месяц|час)"
            r"|\bс\s+\d{1,2}[.:]\d{2}\s+до\s+\d{1,2}[.:]\d{2}", lower,
        ))

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
            "продукция доставляется",
        )

        candidates = self._candidates(document)

        result = []

        for text in candidates:
            normalized = self._normalize_text(text)
            lower = normalized.lower()

            if any(keyword in lower for keyword in delivery_place_keywords) or (
                re.search(r"\b(?:постав\w*|достав\w*|переда\w*|получател\w*)\b", lower)
                and re.search(r"\bпо адресу\b", lower)
            ):
                result.append(normalized)

        for table in document.tables:
            address_columns = []
            for row in table.rows:
                headers = [i for i, cell in enumerate(row) if re.search(
                    r"^(?:адрес|место)\s+(?:получателя|получателей|поставки|доставки)\s*[:.]?$",
                    self._normalize_text(cell).lower(),
                )]
                if headers:
                    address_columns = headers
                    if all(len(self._normalize_text(row[i])) < 70 for i in headers):
                        continue
                if address_columns and any(i < len(row) and row[i].strip() for i in address_columns):
                    result.append(" ".join(cell for cell in row if cell.strip()))

        return self._unique(result)

    @staticmethod
    def _split_paragraph(text: str) -> List[str]:
        parts = []
        start = 0
        pattern = r"(?<!\d)(?<!\d\.)\d{1,3}(?:\.\d{1,3})+\.\s*(?=[А-ЯЁA-Z])"
        for match in re.finditer(pattern, text):
            prefix = text[:match.start()]
            if re.search(r"(?:\bп\.|\bпп\.|\bпункт[а-я]*|\bподпункт[а-я]*)\s*$", prefix, re.I):
                continue
            if match.start() > start:
                parts.append(text[start:match.start()].strip())
            start = match.start()
        parts.append(text[start:].strip())
        return [part for part in parts if part]
