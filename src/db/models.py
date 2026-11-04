from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text, Boolean, Integer, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from schwarz.column_alchemy import YearMonthIntColumn

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
    sent: Mapped[int] = mapped_column(Integer)

class NonWorkingDays(Base):
    __tablename__ = "non_working_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

class CalendarMonth(Base):
    __tablename__ = "calendar_month"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[int] = mapped_column(YearMonthIntColumn, unique=True)
    is_ready: Mapped[bool] = mapped_column(Boolean)