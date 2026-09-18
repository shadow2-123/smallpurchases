import argparse
import json
import logging
import os
import smtplib
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from db.session import Database
from db.models import Notice
from formatters.notices import format_notice_html, format_notice_plain
from mail.client import MailClient
from filters import ExcludeFilter

ROOT = Path(__file__).resolve().parents[1]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(ROOT / "notify.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def parse_args() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["morning", "afternoon", "big"])
    return parser.parse_args().mode


def send_list(db: Database, mail: MailClient, to: str, notices: list[Notice]) -> None:
    log.info("Начало рассылки")
    filter_ = ExcludeFilter(ROOT / "exclude.txt")
    for notice in notices:
        if filter_.is_excluded(notice.name, notice.spec, notice.okpd_code):
            log.info("Пропущено: %s, окпд %s", notice.name, notice.okpd_code)
            continue
        subject, body_html = format_notice_html(notice)
        _, body_plain = format_notice_plain(notice)
        try:
            mail.send(to, subject, body_html, body_plain)
        except smtplib.SMTPException:
            log.exception("не ушло %s", notice.number)
            continue
        db.mark_sent(notice.link)
        log.info("отправлено %s, на почту %s", notice.number, to)


def main() -> None:
    mode = parse_args()
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    load_dotenv()

    db = Database(str(ROOT / settings["db_path"]))
    mail = MailClient(
        host=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", "465")),
        user=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASSWORD"),
        from_addr=os.getenv("MAIL_FROM"),
    )
    to = os.getenv("MAIL_TO")

    if mode == "big":
        notices = db.get_unsent_big(Decimal(str(settings["big_notice_sum"])))
    else:
        notices = db.get_unsent_today_tomorrow()

    log.info("режим %s", mode)
    send_list(db, mail, to, notices)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("рассылка упала")
        raise