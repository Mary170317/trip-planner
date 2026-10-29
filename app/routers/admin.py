from fastapi import APIRouter
from sqlalchemy import select
from app.deps import AdminUser, DbSession
from app.models import User, Trip
from app.schemas import UserOut, TripOut

router = APIRouter(prefix="/api/admin", tags=["Администратор"])

@router.get("/users", response_model=list[UserOut])
def users(admin: AdminUser, db: DbSession):
    return db.scalars(select(User).order_by(User.id)).all()

@router.get("/trips", response_model=list[TripOut])
def trips(admin: AdminUser, db: DbSession):
    return db.scalars(select(Trip).order_by(Trip.id)).all()
