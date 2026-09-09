from datetime import datetime

from wt_client import NoticeSchema
from wt_client.client import WTClient
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    client = WTClient(os.getenv("LOGIN"), os.getenv("PASSWORD"))
    print(client.parse_notice("20979689"))


if __name__ == "__main__":
    main()