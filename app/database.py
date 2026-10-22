import ssl
from collections.abc import Generator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def normalize_database_url(url: str) -> str:
    """Turn Neon’s postgresql:// URL into a pg8000 URL.

    pg8000 is pure Python, so it does not load the native driver Windows
    Application Control blocks. libpq query params are stripped; SSL is
    attached later as an SSL context.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql+psycopg://"):
        url = "postgresql://" + url[len("postgresql+psycopg://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+pg8000://" + url[len("postgresql://") :]
    if not url.startswith("postgresql+pg8000://"):
        return url

    parsed = urlparse(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in {"sslmode", "channel_binding"}
    ]
    return urlunparse(parsed._replace(query=urlencode(query)))


def engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    if url.startswith("postgresql"):
        return {
            "connect_args": {"ssl_context": ssl.create_default_context()},
            "pool_pre_ping": True,
        }
    return {}


def migration_url() -> str:
    raw = settings.direct_database_url.strip() or settings.database_url
    return normalize_database_url(raw)


database_url = normalize_database_url(settings.database_url)
engine = create_engine(database_url, **engine_kwargs(database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
