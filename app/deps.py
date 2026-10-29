from typing import Annotated
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

DbSession = Annotated[Session, Depends(get_db)]

def get_current_user(request: Request, db: DbSession) -> User:
    user_id = request.session.get("user_id")
    if type(user_id) is not int:
        raise HTTPException(401, "Необходима авторизация")
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        request.session.clear()
        raise HTTPException(401, "Сессия недействительна")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Доступ только для администратора")
    return user

AdminUser = Annotated[User, Depends(require_admin)]
