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
from formatters.notices import format_notice_html, format_notice_plain, parse_docs
from mail.client import MailClient
from filters import ExcludeFilter
from wt_client import WTClient

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


def send_list(db: Database, mail: MailClient, client: WTClient, to: str, notices: list[Notice]) -> None:
    log.info("Начало рассылки")
    filter_ = ExcludeFilter(ROOT / "exclude.txt")

    for notice in notices:
        if filter_.is_excluded(notice.name, notice.spec, notice.okpd_code):
            log.info("Пропущено: %s", notice.name)
            continue
        subject, body_html = format_notice_html(notice)
        _, body_plain = format_notice_plain(notice)

        attachments = []
        for filename, url in parse_docs(notice.docs):
            try:
                data = client.download_file(url)
            except Exception:
                log.exception("не скачал %s %s", notice.number, filename)
                continue
            if len(data) > 8 * 1024 * 1024:
                log.info("слишком большой %s %s", notice.number, filename)
                continue
            attachments.append((filename, data))
        log.info("кладу вложений: %s", [name for name, _ in attachments])

        try:
            mail.send(to, subject, body_html, body_plain, attachments)
        except smtplib.SMTPException:
            log.exception("не ушло %s", notice.number)
            continue
        db.mark_sent(notice.link)
        log.info("отправлено %s, на почту %s", notice.name, to)

    log.info("Конец рассылки")


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
    client = WTClient(os.getenv("LOGIN"), os.getenv("PASSWORD"))
    with mail:
        send_list(db, mail, client, to, notices)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Рассылка упала")
        raise