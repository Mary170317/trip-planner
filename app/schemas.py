from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MONEY = dict(ge=Decimal("0"), le=Decimal("99999999.99"), max_digits=10, decimal_places=2)

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    @field_validator("username")
    @classmethod
    def username_valid(cls, value):
        value = value.strip()
        if len(value) < 3 or not all(c.isalnum() or c in "_-" for c in value):
            raise ValueError("Логин: 3–50 букв, цифр, _ или -")
        return value

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    is_admin: bool
    created_at: datetime

class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)

class MessageOut(BaseModel):
    message: str

class TripCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    start_date: date
    end_date: date
    budget: Decimal = Field(default=Decimal("0"), **MONEY)
    is_completed: bool = False
    @field_validator("title")
    @classmethod
    def title_valid(cls, value):
        if not value.strip():
            raise ValueError("Введите название")
        return value.strip()
    @model_validator(mode="after")
    def dates_valid(self):
        if self.end_date < self.start_date:
            raise ValueError("Дата окончания раньше начала")
        return self

class TripUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal | None = Field(default=None, **MONEY)
    is_completed: bool | None = None
    @field_validator("title")
    @classmethod
    def title_valid(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Введите название")
        return value.strip() if value is not None else None
    @model_validator(mode="after")
    def dates_valid(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Дата окончания раньше начала")
        return self

class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    title: str
    description: str | None
    start_date: date
    end_date: date
    budget: Decimal
    is_completed: bool
    created_at: datetime

class PlanItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    day_date: date
    time_text: str | None = Field(default=None, max_length=20)
    place: str | None = Field(default=None, max_length=200)
    estimated_cost: Decimal = Field(default=Decimal("0"), **MONEY)
    is_done: bool = False
    @field_validator("title")
    @classmethod
    def title_valid(cls, value):
        if not value.strip():
            raise ValueError("Введите название")
        return value.strip()

class PlanItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    day_date: date | None = None
    time_text: str | None = Field(default=None, max_length=20)
    place: str | None = Field(default=None, max_length=200)
    estimated_cost: Decimal | None = Field(default=None, **MONEY)
    is_done: bool | None = None
    @field_validator("title")
    @classmethod
    def title_valid(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Введите название")
        return value.strip() if value is not None else None

class PlanItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trip_id: int
    title: str
    day_date: date
    time_text: str | None
    place: str | None
    estimated_cost: Decimal
    is_done: bool

class MonthStats(BaseModel):
    month: str
    trips_count: int
    total_budget: Decimal
    avg_budget: Decimal

class TripStatsOut(BaseModel):
    total_trips: int
    total_budget: Decimal
    avg_budget: Decimal
    by_month: list[MonthStats]

class TripFilters(BaseModel):
    q: str | None = None
    status: Literal["all", "planned", "completed"] = "all"
    date_from: date | None = None
    date_to: date | None = None
    sort: Literal["start_date_asc", "start_date_desc", "title_asc", "budget_desc"] = "start_date_asc"
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    @model_validator(mode="after")
    def range_valid(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from позже date_to")
        return self
