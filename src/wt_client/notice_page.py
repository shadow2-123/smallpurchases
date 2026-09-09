from bs4 import BeautifulSoup


def parse_spec(html: str) -> list[tuple[str, str, str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    for tr in soup.select("div.tab table.ordercard tbody tr"):
        name = tr.select_one("div.product-data")
        if name is None:
            continue
        cells = tr.find_all("td")
        unit = cells[2].get_text(strip=True)
        qty = cells[3].get_text(strip=True)
        price = cells[4].get_text(strip=True)
        rows.append((name.get_text(strip=True), unit, qty, price))

    return rows