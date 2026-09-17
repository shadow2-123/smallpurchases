import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from db.session import Database
from wt_client.client import WTClient
from formatters.notices import spec_text, docs_text

ROOT = Path(__file__).resolve().parents[1]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(ROOT / "parse.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def load_exclude(path: Path) -> list[str]:
    if not path.exists():
        return []
    words = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            words.append(line.lower())
    return words

def is_electro(codes: str, prefixes: tuple[str, ...] = ("26", "27")) -> bool:
    return any(
        code.strip().startswith(prefixes)
        for code in codes.split(",")
        if code.strip()
    )

def is_excluded(name: str, spec: str, words: list[str], codes: str) -> bool:
    text = name.lower() + " " + spec.lower()
    if not any(word in text for word in words):
        return False
    return not is_electro(codes)


def main() -> None:
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    load_dotenv()
    client = WTClient(os.getenv("LOGIN"), os.getenv("PASSWORD"))
    db = Database(str(ROOT / settings["db_path"]))
    exclude = load_exclude(ROOT / "exclude.txt")

    log.info("Старт прохода")
    page = 0
    total_new = 0

    while True:
        notices = client.fetch_notices(
            page=str(page),
            per_page=settings["notices_per_page"],
            pub_days_back=settings["pub_days_back"],
        )
        log.info("Страница %s, на ней заявок %s", page, len(notices))
        if not notices:
            break

        for notice in notices:
            if is_excluded(notice.name, exclude, notice.okpd_code):
                log.info("пропуск exclude %s %s %s", notice.number, notice.name, notice.okpd_code)
                continue
            if db.exists(notice.link):
                continue
            spec_rows, doc_rows = client.parse_notice(notice)
            db.add_new_notice(notice, spec_text(spec_rows), docs_text(doc_rows))
            total_new += 1
            log.info("новая %s %s", notice.number, notice.name)

        page += 1

    log.info("Готово, новых: %s", total_new)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Парсер упал")
        raise