from collections.abc import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def enable_foreign_keys(connection, record):
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
