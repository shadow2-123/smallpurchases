from datetime import datetime, timedelta, date
from decimal import Decimal
from pathlib import Path
from typing import List

from sqlalchemy import create_engine, select, func, update
from sqlalchemy.orm import sessionmaker

from db.models import Base, Notice, NonWorkingDays, CalendarMonth
from wt_client.schemas import NoticeSchema


class CalendarNotReadyError(Exception):
    pass


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

    def get_unsent_today_tomorrow(self, today: date) -> list[Notice]:
        next_day = self.get_next_working_day(today)
        days = [today.isoformat(), next_day.isoformat()]

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
        
    def reset_ignored(self) -> None:
        with self._session_factory() as session:
            session.execute(update(Notice).where(Notice.sent == -1).values(sent=0))
            session.commit()

    def is_non_working_day(self, day: date) -> bool:
        with self._session_factory() as session:
            stmt = select(NonWorkingDays.id).where(
                NonWorkingDays.date == day
            )
            return session.execute(stmt).scalar_one_or_none() is not None

    def is_month_ready(self, month: int) -> bool:
        with self._session_factory() as session:
            stmt = select(CalendarMonth.id).where(
                CalendarMonth.month == month,
                CalendarMonth.is_ready == True
            )
            return session.execute(stmt).scalar_one_or_none() is not None

    def get_next_working_day(self, day: date) -> date:
        candidate = day + timedelta(days=1)
        checked_month = None

        while True:
            month = int(str(day.year) + str(day.month))
            if month != checked_month:
                if not self.is_month_ready(month):
                    raise CalendarNotReadyError(f"Календарь за {candidate.month:02d}.{candidate.year} не готов")
            checked_month = month

            if not self.is_non_working_day(candidate):
                return candidate

            candidate += timedelta(days=1)

    def add_non_working_day(self,day: date,description: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            non_working_day = NonWorkingDays(
                date=day,
                description=description,
            )
            session.add(non_working_day)
            session.commit()