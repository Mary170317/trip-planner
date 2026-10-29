import csv
import io
from datetime import date
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select, insert, update, delete, func, or_
from app.deps import CurrentUser, DbSession
from app.models import Trip, PlanItem
from app.schemas import TripCreate, TripUpdate, TripOut, TripFilters, TripStatsOut, MonthStats

router = APIRouter(prefix="/api/trips", tags=["Поездки"])

def own_trip(db, user_id, trip_id):
    trip = db.scalar(select(Trip).where(Trip.id == trip_id, Trip.owner_id == user_id))
    if trip is None:
        raise HTTPException(404, "Поездка не найдена")
    return trip

@router.get("", response_model=list[TripOut])
def list_trips(user: CurrentUser, db: DbSession, filters: Annotated[TripFilters, Query()]):
    stmt = select(Trip).where(Trip.owner_id == user.id)
    if filters.q:
        term = f"%{filters.q}%"
        stmt = stmt.where(or_(Trip.title.ilike(term), Trip.description.ilike(term)))
    if filters.status != "all":
        stmt = stmt.where(Trip.is_completed == (filters.status == "completed"))
    if filters.date_from:
        stmt = stmt.where(Trip.start_date >= filters.date_from)
    if filters.date_to:
        stmt = stmt.where(Trip.start_date <= filters.date_to)
    sorting = {
        "start_date_asc": Trip.start_date.asc(),
        "start_date_desc": Trip.start_date.desc(),
        "title_asc": Trip.title.asc(),
        "budget_desc": Trip.budget.desc(),
    }
    stmt = stmt.order_by(sorting[filters.sort], Trip.id.asc()).limit(filters.limit).offset(filters.offset)
    return db.scalars(stmt).all()

@router.get("/stats", response_model=TripStatsOut)
def stats(user: CurrentUser, db: DbSession):
    total, budget, avg = db.execute(select(func.count(Trip.id), func.sum(Trip.budget), func.avg(Trip.budget)).where(Trip.owner_id == user.id)).one()
    month = func.strftime("%Y-%m", Trip.start_date)
    rows = db.execute(
        select(month.label("month"), func.count(Trip.id), func.sum(Trip.budget), func.avg(Trip.budget))
        .where(Trip.owner_id == user.id).group_by(month).order_by(month)
    ).all()
    return TripStatsOut(total_trips=total, total_budget=Decimal(str(budget or 0)), avg_budget=Decimal(str(avg or 0)),
        by_month=[MonthStats(month=m, trips_count=c, total_budget=Decimal(str(s or 0)), avg_budget=Decimal(str(a or 0))) for m,c,s,a in rows])

@router.get("/export.csv")
def export_csv(user: CurrentUser, db: DbSession):
    trips = db.scalars(select(Trip).where(Trip.owner_id == user.id).order_by(Trip.start_date, Trip.id)).all()
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow(["ID", "Название", "Описание", "Начало", "Окончание", "Бюджет", "Завершена"])
    for trip in trips:
        writer.writerow([trip.id, trip.title, trip.description or "", trip.start_date.isoformat(), trip.end_date.isoformat(), str(trip.budget), "Да" if trip.is_completed else "Нет"])
    return Response(content=output.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="trips.csv"'})

@router.get("/{trip_id}", response_model=TripOut)
def get_trip(trip_id: int, user: CurrentUser, db: DbSession):
    return own_trip(db, user.id, trip_id)

@router.post("", response_model=TripOut, status_code=201)
def create_trip(data: TripCreate, user: CurrentUser, db: DbSession):
    result = db.execute(insert(Trip).values(**data.model_dump(), owner_id=user.id))
    db.commit()
    return own_trip(db, user.id, result.inserted_primary_key[0])

@router.patch("/{trip_id}", response_model=TripOut)
def patch_trip(trip_id: int, data: TripUpdate, user: CurrentUser, db: DbSession):
    trip = own_trip(db, user.id, trip_id)
    changes = data.model_dump(exclude_unset=True)
    for field in ("title", "start_date", "end_date", "budget", "is_completed"):
        if field in changes and changes[field] is None:
            raise HTTPException(422, f"{field} не может быть null")
    start = changes.get("start_date", trip.start_date)
    end = changes.get("end_date", trip.end_date)
    if end < start:
        raise HTTPException(422, "Дата окончания раньше начала")
    if (start != trip.start_date or end != trip.end_date):
        invalid = db.scalar(select(PlanItem.id).where(PlanItem.trip_id == trip_id, or_(PlanItem.day_date < start, PlanItem.day_date > end)).limit(1))
        if invalid is not None:
            raise HTTPException(422, "Существующие пункты плана выходят за новые даты")
    if changes:
        db.execute(update(Trip).where(Trip.id == trip_id, Trip.owner_id == user.id).values(**changes))
        db.commit()
    return own_trip(db, user.id, trip_id)

@router.delete("/{trip_id}", status_code=204)
def remove_trip(trip_id: int, user: CurrentUser, db: DbSession):
    own_trip(db, user.id, trip_id)
    db.execute(delete(Trip).where(Trip.id == trip_id, Trip.owner_id == user.id))
    db.commit()
    return Response(status_code=204)
