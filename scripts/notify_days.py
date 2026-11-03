import argparse
import json
import os
from datetime import date, timedelta

from dotenv import load_dotenv

from db.session import Database
from mail.client import MailClient
from wt_client import WTClient

from notify import ROOT, log, send_list


def parse_args() -> int:
    parser = argparse.ArgumentParser(
        description="Отправить извещения, заканчивающиеся через N календарных дней."
    )
    parser.add_argument("days", type=int, help="Количество дней от сегодня")
    args = parser.parse_args()

    if args.days < 0:
        parser.error("Количество дней должно быть неотрицательным.")

    return args.days


def main() -> None:
    days = parse_args()
    target_date = date.today() + timedelta(days=days)

    load_dotenv(ROOT / ".env")
    settings = json.loads(
        (ROOT / "settings.json").read_text(encoding="utf-8")
    )
    db = Database(str(ROOT / settings["db_path"]))

    notices = sorted(
        (
            notice
            for notice in db.get_all_unsent()
            if notice.end_date.date() == target_date
        ),
        key=lambda notice: notice.end_date,
    )

    log.info(
        "Рассылка на дату %s, найдено неотправленных: %s",
        target_date.strftime("%d.%m.%Y"),
        len(notices),
    )

    if not notices:
        return

    mail = MailClient(
        host=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", "465")),
        user=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASSWORD"),
        from_addr=os.getenv("MAIL_FROM"),
    )
    client = WTClient(os.getenv("LOGIN"), os.getenv("PASSWORD"))

    with mail:
        send_list(db, mail, client, os.getenv("MAIL_TO"), notices)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Рассылка на выбранную дату упала")
        raise