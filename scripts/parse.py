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





def main() -> None:
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    load_dotenv()
    client = WTClient(os.getenv("LOGIN"), os.getenv("PASSWORD"))
    db = Database(str(ROOT / settings["db_path"]))

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
        page_new = 0
        for notice in notices:
            if db.exists(notice.link):
                continue
            spec_rows, doc_rows = client.parse_notice(notice)
            spec_text_str = spec_text(spec_rows)
            db.add_new_notice(notice, spec_text_str, docs_text(doc_rows))
            page_new += 1
            log.info("новая %s %s", notice.number, notice.name)
        total_new += page_new
        if page_new == 0:
            break
        page += 1

    log.info("Готово, новых: %s", total_new)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Парсер упал")
        raise