from html import escape

from db.models import Notice


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
    subject = f"Новая закупка {notice.number}"
    body = (
        f"{notice.name}\n\n"
        f"Номер: {notice.number}\n\n"
        f"Цена: {notice.amount}\n\n"
        f"Заказчик: {notice.customer_name}\n\n"
        f"Подача: {notice.start_date} — {notice.end_date}\n\n"
        f"https://wt.udmr.ru/smallpurchases/GzwSP/Notice?noticeLink={notice.link}\n\n"
        f"\nСпецификация\n{notice.spec}"
    )
    return subject, body

def format_notice_html(notice: Notice) -> tuple[str, str]:
    subject = f"Новая закупка {notice.number}"
    body = (
        f"{escape(notice.name)}<br><br>"
        f"Номер: {escape(notice.number)}<br><br>"
        f"Цена: {notice.amount}<br><br>"
        f"Заказчик: {escape(notice.customer_name)}<br><br>"
        f"Подача: {notice.start_date} — {notice.end_date}<br><br>"
        f"https://wt.udmr.ru/smallpurchases/GzwSP/Notice?noticeLink={escape(notice.link)}<br><br>"
        f"<br>Спецификация<br>{format_spec_html(notice.spec)}"
    )
    return subject, body

