from html import escape
from db.models import Notice
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


def format_notice_plain(notice: Notice) -> tuple[str, str]:
    subject = format_subject(notice)
    body = (
        f"https://wt.udmr.ru/smallpurchases/GzwSP/Notice?noticeLink={notice.link}\n\n"
        f"\nСпецификация\n\n{notice.spec}"
        f"{format_docs_plain(notice.docs)}"
    )
    return subject, body

def format_notice_html(notice: Notice) -> tuple[str, str]:
    subject = format_subject(notice)
    body = (
        f"https://wt.udmr.ru/smallpurchases/GzwSP/Notice?noticeLink={escape(notice.link)}<br><br>"
        f"<br><br>{format_spec_html(notice.spec)}"
        f"{format_docs_html(notice.docs)}"
    )
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