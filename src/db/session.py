from datetime import datetime, timedelta, date
from decimal import Decimal
from pathlib import Path
from typing import List

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from db.models import Base, Notice
from wt_client.schemas import NoticeSchema


class Database:
    def __init__(self, path: str = "data.db") -> None:
        self.path = Path(path)
        self.engine = create_engine(
            f"sqlite:///{self.path}",
            connect_args={"check_same_thread": False, "timeout": 30},
        )
        self._session_factory = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def add_new_notice(self, notice: NoticeSchema, spec: str, docs: str) -> bool:
        with self._session_factory() as session:
            if session.get(Notice, notice.link) is not None:
                return False

            session.add(
                Notice(
                    link=notice.link,
                    number=notice.number,
                    name=notice.name,
                    amount=notice.amount,
                    start_date=notice.start_date,
                    end_date=notice.end_date,
                    customer_id=notice.customer_id,
                    customer_name=notice.customer_name,
                    okpd_code=notice.okpd_code,
                    spec=spec,
                    docs=docs,
                    sent=0,
                )
            )
            session.commit()
            return True

    def mark_sent(self, link: str) -> None:
        with self._session_factory() as session:
            notice = session.get(Notice, link)
            if notice is None:
                return
            notice.sent = 1
            session.commit()


    def mark_ignored(self, link: str) -> None:
        with self._session_factory() as session:
            notice = session.get(Notice, link)
            if notice is None:
                return
            notice.sent = -1
            session.commit()

    def get_all_unsent(self) -> List[Notice]:
        with self._session_factory() as session:
            return list(
            session.scalars(
                select(Notice).where(Notice.sent == 0)
            ).all()
        )

    def exists(self, link: str) -> bool:
        with self._session_factory() as session:
            notice = session.get(Notice, link)
            return notice is not None

    @staticmethod
    def _day_start(days: int = 0) -> datetime:
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return now + timedelta(days=days)

    def get_unsent_today_tomorrow(self) -> list[Notice]:
        today = date.today()
        days = [today.isoformat(), self.next_workday(today).isoformat()]
        with self._session_factory() as session:
            return list(
                session.scalars(
                    select(Notice).where(
                        Notice.sent == 0,
                        func.date(Notice.end_date).in_(days),
                    ).order_by(Notice.end_date.asc())
                ).all()
            )

    def get_unsent_big(self, min_amount: Decimal) -> list[Notice]:
        start = self._day_start(1)
        with self._session_factory() as session:
            return list(
                session.scalars(
                    select(Notice).where(
                        Notice.sent == 0,
                        Notice.end_date >= start,
                        Notice.amount >= min_amount,
                    ).order_by(Notice.end_date.asc())
                ).all()
            )
    @staticmethod
    def next_workday(d: date) -> date:
        if d.weekday() == 4:
            return d + timedelta(days=3)
        if d.weekday() == 5:
            return d + timedelta(days=2)
        return d + timedelta(days=1)