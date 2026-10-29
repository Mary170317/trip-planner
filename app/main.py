import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth, trips, plan_items, admin

secret_key = os.environ.get("SECRET_KEY")
if not secret_key or len(secret_key) < 32:
    raise RuntimeError("Установите SECRET_KEY (минимум 32 символа)")

app = FastAPI(title="Планировщик поездок — вариант №9", version="1.0.0")
app.add_middleware(SessionMiddleware, secret_key=secret_key, same_site="lax", https_only=False)
app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(plan_items.router)
app.include_router(admin.router)

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/static/index.html")

app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")
