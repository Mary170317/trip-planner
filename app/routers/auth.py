from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import select, insert, update
from sqlalchemy.exc import IntegrityError
from app.deps import DbSession, CurrentUser
from app.models import User
from app.schemas import UserCreate, UserLogin, UserOut, ChangePassword, MessageOut
from app.security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Авторизация"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, request: Request, db: DbSession):
    try:
        result = db.execute(insert(User).values(username=data.username, password_hash=hash_password(data.password), is_admin=False))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Имя пользователя занято")
    user = db.get(User, result.inserted_primary_key[0])
    request.session.clear()
    request.session["user_id"] = user.id
    return user

@router.post("/login", response_model=UserOut)
def login(data: UserLogin, request: Request, db: DbSession):
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Неверный логин или пароль")
    request.session.clear()
    request.session["user_id"] = user.id
    return user

@router.post("/logout", status_code=204)
def logout(request: Request, response: Response):
    request.session.clear()
    response.status_code = 204

@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user

@router.post("/change-password", response_model=MessageOut)
def change_password(data: ChangePassword, user: CurrentUser, db: DbSession, request: Request):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(401, "Неверный текущий пароль")
    db.execute(update(User).where(User.id == user.id).values(password_hash=hash_password(data.new_password)))
    db.commit()
    request.session.clear()
    request.session["user_id"] = user.id
    return MessageOut(message="Пароль изменён")
