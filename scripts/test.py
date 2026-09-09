import json
from datetime import datetime

from db import Database
from mail import MailClient
from wt_client import NoticeSchema
from wt_client.client import WTClient
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

def main():
    load_dotenv()
    with open(ROOT / "settings.json", encoding="utf-8") as f:
        settings = json.load(f)
    db = Database(str(ROOT / settings["db_path"]))
    mail = MailClient(
        host=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", "465")),
        user=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASSWORD"),
        from_addr=os.getenv("MAIL_FROM"),
    )
    to = os.getenv("MAIL_TO")


if __name__ == "__main__":
    main()