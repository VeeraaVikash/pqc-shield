from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./pqc_shield.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,          # wait up to 30s for locks to clear
    },
    pool_size=10,               # FIX: was 1 — caused QueuePool timeout errors
    max_overflow=20,            # allow burst connections beyond pool_size
    pool_timeout=30,            # wait 30s before giving up on getting a connection
    pool_pre_ping=True,         # auto-recover dead/stale connections
)

# Enable WAL mode: allows concurrent reads + writes without blocking each other
@event.listens_for(engine, "connect")
def set_sqlite_pragmas(dbapi_conn, connection_record):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA busy_timeout=30000")   # 30s retry on lock
    dbapi_conn.execute("PRAGMA synchronous=NORMAL")   # safe + faster than FULL

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()