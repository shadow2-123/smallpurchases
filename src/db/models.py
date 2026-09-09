from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Notice(Base):
    __tablename__ = "notices"

    link: Mapped[str] = mapped_column(String(32), primary_key=True)
    number: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    customer_id: Mapped[str] = mapped_column(String(32))
    customer_name: Mapped[str] = mapped_column(Text)
    okpd_code: Mapped[str] = mapped_column(String(255))
    spec: Mapped[str] = mapped_column(Text)
    docs: Mapped[str] = mapped_column(Text)
    sent: Mapped[bool] = mapped_column(Boolean)