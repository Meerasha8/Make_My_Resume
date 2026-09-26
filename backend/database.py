import os
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

load_dotenv()


def _normalize_database_url(url: str) -> str:
    # Supabase hands out postgres:// or postgresql:// URLs; route every Postgres URL to the installed psycopg 3 driver.
    for prefix in ("postgres://", "postgresql://", "postgresql+psycopg2://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


DATABASE_URL = _normalize_database_url(
    os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or "sqlite:///./test.db"
)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Supabase's pooler drops idle connections; check them before use instead of failing mid-request.
    engine_kwargs["pool_pre_ping"] = True
    # Supabase's transaction pooler (port 6543, needed on hosts without IPv6 such as Render) can't keep server-side
    # prepared statements, which psycopg creates after a query runs 5 times -> "prepared statement already exists".
    engine_kwargs["connect_args"] = {"prepare_threshold": None}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
