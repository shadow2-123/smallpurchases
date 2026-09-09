from pathlib import Path
from typing import List

from sqlalchemy import create_engine, select
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

    def add_new_notice(self, notice: NoticeSchema, spec: str) -> bool:
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
                    sent=False,
                )
            )
            session.commit()
            return True

    def mark_sent(self, link: str) -> None:
        with self._session_factory() as session:
            notice = session.get(Notice, link)
            if notice is None:
                return
            notice.sent = True
            session.commit()

    def get_all_unsent(self) -> List[Notice]:
        with self._session_factory() as session:
            return list(
            session.scalars(
                select(Notice).where(Notice.sent == False)
            ).all()
        )

    def exists(self, link: str) -> bool:
        with self._session_factory() as session:
            notice = session.get(Notice, link)
            return notice is not None