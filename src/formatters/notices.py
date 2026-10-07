from html import escape
from db.models import Notice
from pathlib import Path
from transliterate import translit

from documents import DocumentParseResult

SEP = " | "

def spec_text(rows: list[tuple[str, str, str, str]]) -> str:
    return "\n".join(f"{name}||{units}||{qty}||{price}" for name, units, qty, price in rows)

def docs_text(rows: list[tuple[str, str]]) -> str:
    return "\n".join(f"{name}||{url}" for name, url in rows)

def format_spec_html(spec: str) -> str:
    rows_html = []
    for line in spec.splitlines():
        if not line.strip():
            continue
        name, units, qty, price = line.split("||")
        rows_html.append(
            "<tr>"
            f"<td>{escape(name.strip())}</td>"
            f"<td>{escape(units.strip())}</td>"
            f"<td>{escape(qty.strip())}</td>"
            f"<td>{escape(price.strip())}</td>"
            "</tr>"
        )

    body = "".join(rows_html)
    return (
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>Наименование</th><th>Ед.</th><th>Кол-во</th><th>Сумма</th></tr>"
        f"{body}"
        "</table>"
    )


def format_notice_plain(
    notice: Notice,
    documents: dict[str, DocumentParseResult],
) -> tuple[str, str]:
    subject = format_subject(notice)
    body = (
        f"https://wt.udmr.ru/smallpurchases/GzwSP/Notice?noticeLink={notice.link}\n\n"
        f"\nСпецификация\n\n{notice.spec}"
        f"{format_docs_plain(notice.docs)}"
        f"{format_document_info_plain(documents)}"
    )
    return subject, body

def format_notice_html(
    notice: Notice,
    documents: dict[str, DocumentParseResult],
) -> tuple[str, str]:
    subject = format_subject(notice)
    url = f"https://wt.udmr.ru/smallpurchases/GzwSP/Notice?noticeLink={notice.link}"

    body = f"""\
    <html>
      <body>
        <p><a href="{escape(url)}">Открыть извещение</a></p>
        {format_spec_html(notice.spec)}
        {format_docs_html(notice.docs)}
        {format_document_info_html(documents)}
      </body>
    </html>
    """

    return subject, body

def short_name(name: str, limit: int = 15) -> str:
    name = " ".join(name.split())
    if len(name) <= limit:
        return name
    idx = name.find(" ", limit)
    if idx == -1:
        return name
    return name[:idx]

def format_subject(notice: Notice) -> str:
    day = notice.end_date.strftime("%d/%m")
    return SEP.join([
        day,
        notice.number,
        short_name(notice.name),
        notice.customer_name,
    ])


def format_docs_html(docs: str) -> str:
    if not docs.strip():
        return ""
    items = []
    for line in docs.splitlines():
        if not line.strip() or "||" not in line:
            continue
        name, url = line.split("||", 1)
        name = escape(name.strip())
        url = escape(url.strip())
        items.append(f'<li><a href="{url}">{name}</a></li>')
    if not items:
        return ""
    return "<br><ul>" + "".join(items) + "</ul>"

def format_docs_plain(docs: str) -> str:
    if not docs.strip():
        return ""
    lines = [""]
    for line in docs.splitlines():
        if not line.strip() or "||" not in line:
            continue
        name, url = line.split("||", 1)
        lines.append(f"{name.strip()}: {url.strip()}")
    return "\n".join(lines)

def parse_docs(docs: str) -> list[tuple[str, str]]:
    rows = []
    for line in docs.splitlines():
        if not line.strip() or "||" not in line:
            continue
        name, url = line.split("||", 1)
        rows.append((name.strip(), url.strip()))
    return rows


def safe_filename(name: str) -> str:
    ext = Path(name).suffix.lower() or ".bin"
    stem = Path(name).stem
    stem = translit(stem, "ru", reversed=True)
    stem = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in stem)
    stem = stem.strip("._") or "file"
    return stem + ext

def format_document_info_html(
    documents: dict[str, DocumentParseResult],
) -> str:
    terms = []
    places = []

    for result in documents.values():
        terms.extend(result.delivery_terms)
        places.extend(result.delivery_places)

    terms = list(dict.fromkeys(terms))
    places = list(dict.fromkeys(places))

    if not terms and not places:
        return ""

    parts = [
        "<br>",
        "<div style='border:1px solid #ccc; padding:10px;'>",
        "<b>Информация из документов</b>",
    ]

    if terms:
        parts.append(
            "<ul>"
            + "".join(f"<li>{escape(term)}</li>" for term in terms)
            + "</ul>"
        )

    if places:
        parts.append(
            "<ul>"
            + "".join(f"<li>{escape(place)}</li>" for place in places)
            + "</ul>"
        )

    parts.append("</div>")

    return "".join(parts)


def format_document_info_plain(
    documents: dict[str, DocumentParseResult],
) -> str:
    terms = []
    places = []

    for result in documents.values():
        terms.extend(result.delivery_terms)
        places.extend(result.delivery_places)

    terms = list(dict.fromkeys(terms))
    places = list(dict.fromkeys(places))

    if not terms and not places:
        return ""

    lines = [
        "",
        "",
        "Информация из документов",
    ]

    if terms:
        lines.append("")
        lines.extend(f"- {term}" for term in terms)

    if places:
        lines.append("")
        lines.extend(f"- {place}" for place in places)

    return "\n".join(lines)