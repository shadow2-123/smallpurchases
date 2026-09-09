from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator, Field


class NoticeSchema(BaseModel):
    link: str
    number: str
    name: str
    amount: Decimal = Field(alias="summa")
    start_date: datetime = Field(alias="collecting_startdate")
    end_date: datetime = Field(alias="collecting_enddate")
    customer_id: str = Field(alias="uchr")
    customer_name: str = Field(alias="uchr_sname")
    okpd_code: str = Field(alias="okpd2_codes")

    @field_validator("amount", mode="before")
    @classmethod
    def parse_sum(cls, value: str) -> str:
        return str(value).replace(",", ".")

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_date(cls, value: str) -> datetime:
        return datetime.strptime(value, "%d.%m.%Y %H:%M")

    @field_validator("name", mode="before")
    @classmethod
    def parse_name(cls, value: str) -> str:
        return str(value).replace("\n", " ")