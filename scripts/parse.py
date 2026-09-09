import json
import logging
import os
import time
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


def is_excluded(name: str, words: list[str]) -> bool:
    text = name.lower()
    return any(word in text for word in words)


def main() -> None:
    with open(ROOT / "settings.json", encoding="utf-8") as f:
        settings = json.load(f)
    load_dotenv()
    client = WTClient(os.getenv("LOGIN"), os.getenv("PASSWORD"))
    db = Database(str(ROOT / settings["db_path"]))
    while True:
        log.info("Старт прохода")
        page = 0
        total_new = 0

        while True:
            exclude = load_exclude(ROOT / "exclude.txt")
            notices = client.fetch_notices(page=str(page), per_page=settings["notices_per_page"], pub_days_back=settings["pub_days_back"])
            log.info("Страница %s, на ней заявок %s", page, len(notices))

            if not notices:
                break

            for notice in notices:

                if is_excluded(notice.name, exclude):
                    continue

                if db.exists(notice.link):
                    continue
                spec = client.parse_notice(notice)
                db.add_new_notice(notice, spec_text(spec[0], docs_text(spec[1])))
                total_new += 1
                log.info("новая %s %s", notice.number, notice.name)

            page += 1

        log.info("Готово, новых: %s", total_new)
        time.sleep(settings["parse_interval_sec"])
        with open(ROOT / "settings.json", encoding="utf-8") as f:
            settings = json.load(f)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Парсер упал")
        raise