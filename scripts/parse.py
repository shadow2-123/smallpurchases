import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from db.session import Database
from wt_client.client import WTClient
from formatters.notices import spec_text

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



OKPD_CODES = ("26",
              "27")



def is_electro(codes: str) -> bool:
    return any(
        code.strip().startswith(OKPD_CODES)
        for code in codes.split(",")
        if code.strip()
    )


def main() -> None:
    load_dotenv()
    client = WTClient(os.getenv("LOGIN"), os.getenv("PASSWORD"))
    db = Database(str(ROOT / "data.db"))
    while True:
        log.info("Старт прохода")
        page = 0
        total_new = 0

        while True:
            notices = client.fetch_notices(page=str(page), per_page=30)
            log.info("Страница %s, на ней заявок %s", page, len(notices))

            if not notices:
                break

            for notice in notices:

                if not is_electro(notice.okpd_code):
                    continue

                if db.exists(notice.link):
                    continue
                spec = client.parse_notice(notice)
                db.add_new_notice(notice, spec_text(spec))
                total_new += 1
                log.info("новая %s %s", notice.number, notice.name)

            page += 1

        log.info("Готово, новых: %s", total_new)
        time.sleep(2700)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Парсер упал")
        raise