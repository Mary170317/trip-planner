from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select, insert, update, delete
from app.deps import CurrentUser, DbSession
from app.models import Trip, PlanItem
from app.schemas import PlanItemCreate, PlanItemUpdate, PlanItemOut

router = APIRouter(tags=["План по дням"])

def own_trip(db, user_id, trip_id):
    trip = db.scalar(select(Trip).where(Trip.id == trip_id, Trip.owner_id == user_id))
    if trip is None:
        raise HTTPException(404, "Поездка не найдена")
    return trip

def own_item(db, user_id, item_id):
    item = db.scalar(select(PlanItem).join(Trip).where(PlanItem.id == item_id, Trip.owner_id == user_id))
    if item is None:
        raise HTTPException(404, "Пункт плана не найден")
    return item

@router.get("/api/trips/{trip_id}/plan-items", response_model=list[PlanItemOut])
def list_items(trip_id: int, user: CurrentUser, db: DbSession):
    own_trip(db, user.id, trip_id)
    return db.scalars(select(PlanItem).join(Trip).where(PlanItem.trip_id == trip_id, Trip.owner_id == user.id)
                      .order_by(PlanItem.day_date, PlanItem.time_text, PlanItem.id)).all()

@router.post("/api/trips/{trip_id}/plan-items", response_model=PlanItemOut, status_code=201)
def create_item(trip_id: int, data: PlanItemCreate, user: CurrentUser, db: DbSession):
    trip = own_trip(db, user.id, trip_id)
    if not trip.start_date <= data.day_date <= trip.end_date:
        raise HTTPException(422, "Дата пункта вне поездки")
    result = db.execute(insert(PlanItem).values(**data.model_dump(), trip_id=trip_id))
    db.commit()
    return own_item(db, user.id, result.inserted_primary_key[0])

@router.patch("/api/plan-items/{item_id}", response_model=PlanItemOut)
def patch_item(item_id: int, data: PlanItemUpdate, user: CurrentUser, db: DbSession):
    item = own_item(db, user.id, item_id)
    changes = data.model_dump(exclude_unset=True)
    for field in ("title", "day_date", "estimated_cost", "is_done"):
        if field in changes and changes[field] is None:
            raise HTTPException(422, f"{field} не может быть null")
    trip = own_trip(db, user.id, item.trip_id)
    day = changes.get("day_date", item.day_date)
    if not trip.start_date <= day <= trip.end_date:
        raise HTTPException(422, "Дата пункта вне поездки")
    if changes:
        # Подзапрос ограничивает изменение владельцем через JOIN с Trip.
        owned = select(PlanItem.id).join(Trip).where(PlanItem.id == item_id, Trip.owner_id == user.id)
        db.execute(update(PlanItem).where(PlanItem.id.in_(owned)).values(**changes))
        db.commit()
    return own_item(db, user.id, item_id)

@router.delete("/api/plan-items/{item_id}", status_code=204)
def remove_item(item_id: int, user: CurrentUser, db: DbSession):
    own_item(db, user.id, item_id)
    owned = select(PlanItem.id).join(Trip).where(PlanItem.id == item_id, Trip.owner_id == user.id)
    db.execute(delete(PlanItem).where(PlanItem.id.in_(owned)))
    db.commit()
    return Response(status_code=204)
