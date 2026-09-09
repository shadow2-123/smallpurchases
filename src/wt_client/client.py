import json
from datetime import datetime, timedelta
from typing import List

import requests
import re
from wt_client.schemas import NoticeSchema
from wt_client.notice_page import parse_spec

class WTClient:
    BASE = "https://wt.udmr.ru/smallpurchases"


    def __init__(self, login: str, password: str) -> None:
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None
        self._auth()


    @staticmethod
    def _extract_token(html: str) -> str:
        for pat in (
                r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',
                r'value="([^"]+)"[^>]*name="__RequestVerificationToken"',
        ):
            m = re.search(pat, html)
            if m:
                return m.group(1)
        raise RuntimeError("Не нашёл RequestVerificationToken на странице грида")


    def _auth(self) -> None:

        self.session = requests.Session()
        self.csrf_token = None

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })

        login_resp = self.session.post(
            f"{self.BASE}/Login/CheckLogin",
            data={
                "login": self.login,
                "pass": self.password,
                "saveAuth": "true",
            },
            headers={"Referer": f"{self.BASE}/Login"},
        )
        login_resp.raise_for_status()

        page = self.session.get(f"{self.BASE}/GzwSP/NoticesGrid")
        page.raise_for_status()

        self.csrf_token = self._extract_token(page.text)


    def fetch_notices(self, page: str = "0", per_page: int = 30, pub_days_back: int = 5) -> List[NoticeSchema]:
        resp = self._request_notices(page=page, per_page=per_page, pub_days_back=pub_days_back)

        if resp.status_code in (400, 401, 403):
            self._auth()
            resp = self._request_notices(page=page, per_page=per_page, pub_days_back=pub_days_back)

        resp.raise_for_status()
        return [NoticeSchema.model_validate(item) for item in resp.json()["items"]]


    def _request_notices(self, page: str, per_page: int, pub_days_back: int) -> requests.Response:
        filter_day = (datetime.now() - timedelta(days=pub_days_back)).strftime("%d.%m.%Y")

        payload = {
            "settings": {
                "rp": per_page,
                "page": page,
                "totalRows": 0,
                "rpList": [10, 20, 30],
                "sortDir": "desc",
                "sortField": "pub_date",
                "sortList": {
                    "pub_date": "Дата публикации",
                    "number": "Рег. номер",
                    "name": "Наименование",
                    "summa": "НМЦК",
                    "uchr_sname": "Заказчик",
                    "collecting_endDate": "Дата окончания подачи заявок",
                },
                "filter": {
                    "dtDatePubBegin": {
                        "PName": "dtDatePubBegin",
                        "PValue": filter_day,
                        "PType": "Date",
                    }
                },
                "localFilter": [],
            }
        }

        return self.session.post(
            f"{self.BASE}/GzwSP/NoticesJson",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/json; charset=UTF-8",
                "Origin": "https://wt.udmr.ru",
                "Referer": f"{self.BASE}/GzwSP/NoticesGrid",
                "X-Requested-With": "XMLHttpRequest",
                "RequestVerificationToken": self.csrf_token,
            },
        )

    def parse_notice(self, notice: NoticeSchema) -> list[tuple[str, str, str, str]]:
        resp = self._request_notice(notice.link)

        if resp.status_code in (400, 401, 403):
            self._auth()
            resp = self._request_notice(notice.link)

        resp.raise_for_status()
        return parse_spec(resp.text)

    def _request_notice(self, link: str) -> requests.Response:
        return self.session.get(
            f"{self.BASE}/GzwSP/Notice",
            params={"noticeLink": link},
            headers={"Referer": f"{self.BASE}/GzwSP/NoticesGrid"},
        )