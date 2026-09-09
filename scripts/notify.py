import logging
import os
import smtplib
import time
from pathlib import Path

from dotenv import load_dotenv

from db.session import Database
from formatters.notices import format_notice_html, format_notice_plain
from mail.client import MailClient

ROOT = Path(__file__).resolve().parents[1]
INTERVAL = 30 * 60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(ROOT / "notify.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def send_unsent(db: Database, mail: MailClient, to: str) -> None:
    notices = db.get_all_unsent()
    log.info("к отправке: %s", len(notices))

    for notice in notices:
        subject, body_html = format_notice_html(notice)
        _, body_plain = format_notice_plain(notice)
        try:
            mail.send(to, subject, body_html, body_plain)
        except smtplib.SMTPException:
            log.exception("не ушло %s", notice.number)
            continue
        db.mark_sent(notice.link)
        log.info("отправлено %s", notice.number)


def main() -> None:
    load_dotenv()
    db = Database(str(ROOT / "data.db"))
    mail = MailClient(
        host=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", "465")),
        user=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASSWORD"),
        from_addr=os.getenv("MAIL_FROM"),
    )
    to = os.getenv("MAIL_TO")

    while True:
        try:
            send_unsent(db, mail, to)
        except Exception:
            log.exception("проход рассылки упал")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()