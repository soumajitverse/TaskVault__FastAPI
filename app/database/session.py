from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# echo=False: If set to True, SQLAlchemy prints every raw SQL statement it executes to the terminal. Great for debugging queries locally, but kept False in production to prevent clutter and leaking query data.
engine = create_engine(settings.DATABASE_URL, echo=False)


# A Session is your workspace for database operations (querying, inserting, updating, deleting). It acts as an in-memory transaction (Unit of Work).

"""Why autocommit=False?
We want explicit control over transactions:
You stage changes using db.add(...).
The changes are only committed to the database when you explicitly call db.commit().
If an error occurs, you can call db.rollback() so nothing corrupted is saved."""

"""Why autoflush=False?
SQLAlchemy normally "flushes" (sends pending SQL to the DB buffer) automatically before running any query. Disabling autoflush avoids unexpected intermediate flushes before you are ready to commit your transaction."""
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


"""How it works during an HTTP Request:
Request arrives: A route with db: Session = Depends(get_db) is called.
Setup: FastAPI enters get_db(), instantiates db = SessionLocal(), and hits yield db.
Execution: The execution pauses right at yield db, and FastAPI hands db over to your route function.
Endpoint executes: Your route runs queries, creates tasks, etc.
Teardown (finally block): Once the response is sent back to the user—or even if your endpoint crashes with an unhandled exception—FastAPI resumes get_db() right after yield.
Cleanup: The finally: db.close() block is guaranteed to run. It releases the database connection back into the pool so you never run out of connections (preventing connection leaks)."""

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()