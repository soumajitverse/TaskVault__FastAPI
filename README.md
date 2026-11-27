# TaskVault – Production-Ready FastAPI Backend

TaskVault is a modern, enterprise-grade Task Management REST API built with **Python 3.12+**, **FastAPI**, **SQLAlchemy 2.0**, and **Neon PostgreSQL**.

This repository is designed not only as a working production service but also as a **comprehensive educational blueprint** for Python developers who want to transition from basic scripting to professional backend engineering.

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Tech Stack & Library Breakdown](#2-tech-stack--library-breakdown)
3. [Database: Neon PostgreSQL](#3-database-neon-postgresql)
4. [Local Setup & Installation](#4-local-setup--installation)
5. [The FastAPI Backend Masterclass (Core Concepts)](#5-the-fastapi-backend-masterclass-core-concepts)
   - [Pydantic v2 vs. SQLAlchemy 2.0](#51-pydantic-v2-schemas-vs-sqlalchemy-20-models)
   - [Database Session Management (`yield db`)](#52-database-session-lifecycle-with-yield)
   - [Database Schema Migrations with Alembic](#53-why-alembic-instead-of-create_all)
   - [JWT Authentication & Argon2 Password Hashing](#54-how-jwt-authentication--argon2-hashing-work)
   - [Role-Based Access Control (RBAC) & Reusable Dependencies](#55-role-based-access-control-rbac-dependencies)
   - [Anti-IDOR Security Pattern (Ownership Isolation)](#56-preventing-idor-insecure-direct-object-references)
   - [Custom ASGI Middleware vs. FastAPI Dependencies](#57-custom-asgi-middleware-vs-route-dependencies)
6. [API Reference & Testing Guide](#6-api-reference--testing-guide)

---

## 1. Architecture Overview

TaskVault follows a modular, layered architecture ensuring separation of concerns:

```
                      [ Client: Swagger UI / Postman / Frontend ]
                                          │
                                          ▼
                                [ Logging Middleware ]
                       (Measures latency, logs method, path, status)
                                          │
                                          ▼
                                  [ API Routers ]
                       (/auth, /tasks, /users, /health endpoints)
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
          [ Pydantic v2 Schemas ]                     [ FastAPI Dependencies ]
     (Request validation & typing,                (Database session injection,
      response filtering & serialization)          JWT decoding, RBAC checks)
                                                                │
                                                                ▼
                                                     [ SQLAlchemy 2.0 ORM ]
                                                    (Unit of Work & queries)
                                                                │
                                                                ▼
                                                     [ Neon PostgreSQL DB ]
```

### Folder Structure
```text
FastAPI__Final/
├── app/
│   ├── core/
│   │   ├── config.py          # Pydantic BaseSettings (typed environment variables)
│   │   ├── security.py        # Argon2 hashing & PyJWT token encoding/decoding
│   │   └── dependencies.py    # get_current_user & require_role RBAC guards
│   ├── database/
│   │   ├── base.py            # SQLAlchemy 2.0 DeclarativeBase registry
│   │   └── session.py         # Engine pool & get_db per-request session generator
│   ├── models/
│   │   ├── user.py            # User database table definition & relationships
│   │   └── task.py            # Task database table definition & foreign keys
│   ├── schemas/
│   │   ├── user.py            # User Pydantic request/response validation schemas
│   │   └── task.py            # Task Pydantic request/response validation schemas
│   ├── routers/
│   │   ├── auth.py            # User registration, JSON login, profile endpoints
│   │   ├── tasks.py           # Authenticated Task CRUD endpoints with ownership check
│   │   └── users.py           # Admin-only user management & role elevation
│   ├── middleware/
│   │   └── logging.py         # Custom ASGI HTTP timing & request logger
│   ├── __init__.py
│   └── main.py                # FastAPI entrypoint application
├── alembic/                   # Database version migration scripts
├── .env.example               # Template for required environment variables
├── .gitignore                 # Protects secrets (.env) and virtual environments
├── alembic.ini                # Alembic configuration
├── plan.md                    # Step-by-step progress checklist
└── requirements.txt           # Pinned project dependencies
```

---

## 2. Tech Stack & Library Breakdown

Every dependency in TaskVault was deliberately selected to adhere to industry standards. Here is why each library is used:

| Library | Purpose in TaskVault | Why It Was Chosen |
|---|---|---|
| **`fastapi`** | Core Web Framework | High-performance asynchronous REST API framework with automatic OpenAPI/Swagger documentation generation and dependency injection. |
| **`uvicorn[standard]`** | ASGI Web Server | Lightning-fast ASGI server built on `uvloop` and `httptools` to serve FastAPI in production and development (with `--reload`). |
| **`sqlalchemy`** (v2.0+) | Object Relational Mapper (ORM) | Industry-standard database toolkit. Version 2.0 introduces full type hints (`Mapped[...]`), connection pooling, and explicit `select()` queries. |
| **`psycopg2-binary`** | PostgreSQL Driver | The most stable, battle-tested PostgreSQL adapter for Python, handling raw TCP communication between SQLAlchemy and Postgres. |
| **`alembic`** | Database Schema Migrations | "Git for your database". Tracks, generates, applies, and rolls back database schema modifications incrementally without data loss. |
| **`pydantic-settings`** | Configuration Management | Parses and validates environment variables from `.env` files into strongly typed Python objects with fail-fast validation. |
| **`pyjwt`** | JSON Web Tokens (JWT) | Encodes and verifies cryptographically signed bearer tokens using HMAC-SHA256 (`HS256`). |
| **`pwdlib[argon2]`** | Password Hashing | Modern password hashing library using **Argon2id**, the winner of the Password Hashing Competition, immune to GPU/ASIC cracking. |
| **`python-multipart`** | Form Data Parser | Required by FastAPI to support standard multipart and URL-encoded forms. |

---

## 3. Database: Neon PostgreSQL

TaskVault is configured to use **[Neon](https://neon.tech)**, a serverless, cloud-native PostgreSQL platform with autoscaling and branching capabilities.

### Connection String Format
SQLAlchemy 2.0 with the `psycopg2` driver requires the connection string to begin with `postgresql+psycopg2://`:

```text
postgresql+psycopg2://<username>:<password>@<neon-hostname>.neon.tech/<database_name>?sslmode=require
```

### Automatic Driver Normalization
In `app/core/config.py`, we included a Pydantic `field_validator` that automatically sanitizes connection strings. If you paste a URL starting with `postgres://` or plain `postgresql://`, it is automatically converted to `postgresql+psycopg2://` on startup:
```python
@field_validator("DATABASE_URL", mode="before")
@classmethod
def assemble_db_connection(cls, v: str) -> str:
    if isinstance(v, str):
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
    return v
```

---

## 4. Local Setup & Installation

Follow these steps to run TaskVault locally from scratch:

### 1. Clone the Repository
```bash
git clone https://github.com/soumajitverse/TaskVault__FastAPI.git
cd TaskVault__FastAPI
```

### 2. Create and Activate a Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to create your `.env` file:
```bash
cp .env.example .env
```
Open `.env` and set your Neon PostgreSQL URL and secrets:
```env
PROJECT_NAME="TaskVault"
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<neon-host>.neon.tech/<dbname>?sslmode=require"
SECRET_KEY="super-secret-random-key-change-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Apply Database Migrations
Run Alembic to create the tables in Neon PostgreSQL:
```bash
alembic upgrade head
```

### 6. (Optional) Seed the First Admin User
Because public registration strictly defaults to standard `USER`, seed an initial `ADMIN` user directly into PostgreSQL:
```bash
python -c "
from app.database.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy import select

db = SessionLocal()
admin = db.scalar(select(User).where(User.email == 'admin@taskvault.com'))
if not admin:
    admin = User(
        username='System Admin',
        email='admin@taskvault.com',
        hashed_password=hash_password('AdminSecure2026!'),
        role='ADMIN'
    )
    db.add(admin)
    db.commit()
    print('Admin created: admin@taskvault.com / AdminSecure2026!')
else:
    print('Admin already exists!')
db.close()
"
```

### 7. Launch the Development Server
```bash
uvicorn app.main:app --reload
```
Open your browser to:
- **Swagger UI Interactive Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Alternative Docs:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 5. The FastAPI Backend Masterclass (Core Concepts)

If you only know basic Python, this section explains the core architectural principles that turn simple scripts into enterprise web backends.

---

### 5.1. Pydantic v2 Schemas vs. SQLAlchemy 2.0 Models

A common question is: *"Why do we define User in `models/user.py` AND in `schemas/user.py`?"*

- **SQLAlchemy Models (`app/models/`)** define the **Database Structure**.
  - Maps Python classes to PostgreSQL tables.
  - Dictates primary keys, foreign keys, table indexes, and relationships.
- **Pydantic Schemas (`app/schemas/`)** define the **HTTP Contract (Data Transfer Objects)**.
  - Dictates what JSON keys a user can send and what JSON keys our server returns.
  - Performs validation (e.g., minimum string length, email regex).
  - **Security Filter:** When returning a user profile, `UserResponse` excludes `hashed_password`. Even though the database model has the hash, Pydantic strips it out so it never leaks over the internet!

#### How SQLAlchemy objects convert to Pydantic:
```python
class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```
`from_attributes = True` tells Pydantic: *"Read fields using dot notation (`user.id`, `user.email`) from SQLAlchemy ORM instances instead of expecting raw dictionary keys (`user['id']`)."*

---

### 5.2. Database Session Lifecycle with `yield`

Opening a new database connection for every single query is slow. Leaving database connections open forever causes the server to run out of connections and crash.

FastAPI solves this with generator dependencies:

```python
# app/database/session.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### How it works per request:
1. When a route has `db: Session = Depends(get_db)`, FastAPI runs `get_db()`.
2. A database session is allocated from the connection pool.
3. Execution pauses at `yield db`, and the session is handed to your router endpoint.
4. Your route queries or writes to the database.
5. **The `finally` guarantee:** Once the HTTP response is sent back—**or even if your route crashes with an unhandled exception**—FastAPI resumes execution after `yield` and runs `db.close()`. The connection is cleanly returned to the pool, preventing connection leaks.

---

### 5.3. Why Alembic Instead of `create_all()`?

In novice tutorials, you often see:
```python
Base.metadata.create_all(bind=engine)
```
#### Why this fails in production:
`create_all()` only creates tables if they **do not exist**. If you add a new column `priority` or change a relationship later, `create_all()` does **nothing** to existing tables.

**Alembic** acts as version control for database schemas:
1. `alembic revision --autogenerate -m "add priority column"`: Alembic inspects your Python models, compares them against the live PostgreSQL database, and writes an incremental migration script.
2. `alembic upgrade head`: Executes the exact `ALTER TABLE ...` SQL statements against PostgreSQL.
3. `alembic downgrade -1`: Undoes the last migration if a bug is discovered.

---

### 5.4. How JWT Authentication & Argon2 Hashing Work

#### Password Hashing (Argon2):
When a user registers:
1. Plaintext password: `"Password123!"`
2. Argon2 creates a salted, memory-hard hash:
   `$argon2id$v=19$m=65536,t=3,p=4$salt...$hash...`
3. Only this hash is saved to PostgreSQL. Even if the database is leaked, attackers cannot reverse it.
4. When logging in, `verify_password("Password123!", stored_hash)` re-hashes the input with the stored salt in constant time to verify validity.

#### JWT Token Flow:
When login succeeds, the server generates a signed string:
```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6IlVTRVIiLCJleHAiOjE3MzI3MDc0MDB9.signature
```
- **Header**: Algorithm (`HS256`).
- **Payload**: User claims (`sub`: user ID, `role`: "USER", `exp`: expiration time).
- **Signature**: `HMAC_SHA256(header + payload, SECRET_KEY)`.

The client stores this token and passes it in the HTTP header of every request:
```http
Authorization: Bearer <access_token>
```
The server verifies the signature using `SECRET_KEY`. If someone modifies `"role": "USER"` to `"role": "ADMIN"`, the signature becomes invalid and FastAPI halts the request with `401 Unauthorized`.

---

### 5.5. Role-Based Access Control (RBAC) Dependencies

Instead of writing `if current_user.role != "ADMIN"` inside dozens of route handlers, we use a **Higher-Order Dependency Factory**:

```python
# app/core/dependencies.py
def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires {required_role} role.",
            )
        return current_user
    return role_checker

require_admin = require_role("ADMIN")
```

#### In the Router:
```python
@router.get("/users")
def list_users(admin: User = Depends(require_admin)):
    ...
```
- Standard users attempting to access `/users` immediately receive **`403 Forbidden`**.
- Admins are allowed through seamlessly.

---

### 5.6. Preventing IDOR (Insecure Direct Object References)

In a multi-user application, what happens if Alice creates Task #1, and Bob sends:
`DELETE /tasks/1`?

#### Insecure Code (Vulnerable):
```python
task = db.scalar(select(Task).where(Task.id == task_id))
db.delete(task) # Bob just deleted Alice's task!
```

#### TaskVault Secure Pattern:
```python
# app/routers/tasks.py
query = select(Task).where(
    Task.id == task_id,
    Task.owner_id == current_user.id  # Strict ownership check!
)
task = db.scalar(query)
if not task:
    raise HTTPException(status_code=404, detail="Task not found")
```
Notice two critical security decisions:
1. `Task.owner_id == current_user.id` is baked into every query.
2. If Bob tries to access Task #1, we return **`404 Not Found`**, not `403`. Returning 404 prevents Bob from discovering whether Task #1 even exists.

---

### 5.7. Custom ASGI Middleware vs. Route Dependencies

FastAPI gives you two ways to intercept requests:

- **FastAPI Dependencies (`Depends`)**:
  - Bound to specific routes.
  - Has access to route parameters and yields database sessions.
  - Used for: Auth, permissions, input parsing.
- **ASGI Middleware (`BaseHTTPMiddleware`)**:
  - **Global**: Wraps every single request entering the application, before routing occurs.
  - Measures total execution duration.
  - Used for: Request timing, access logging, CORS, global error catching.

```python
# app/middleware/logging.py
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration_ms:.2f}ms")
        return response
```

---

## 6. API Reference & Testing Guide

All endpoints can be interactively tested at `http://127.0.0.1:8000/docs`.

### Authentication Endpoints (`/auth`)
| Method | Endpoint | Access | Description | Request Body |
|---|---|---|---|---|
| `POST` | `/auth/register` | Public | Register new account (forces role="USER") | `{"username": "...", "email": "...", "password": "..."}` |
| `POST` | `/auth/login` | Public | Authenticate with email & password | `{"email": "...", "password": "..."}` |
| `GET` | `/auth/me` | Authenticated | View current authenticated profile | None (Bearer token in header) |

### Task Endpoints (`/tasks`)
| Method | Endpoint | Access | Description | Request Body |
|---|---|---|---|---|
| `POST` | `/tasks` | Authenticated | Create a new task (auto-assigned to user) | `{"title": "...", "description": "...", "status": "PENDING"}` |
| `GET` | `/tasks` | Authenticated | List all tasks owned by logged-in user | None |
| `GET` | `/tasks/{id}` | Owner Only | Get task details by ID | None |
| `PUT` | `/tasks/{id}` | Owner Only | Partial/Full update task attributes | `{"status": "COMPLETED"}` (any field optional) |
| `DELETE` | `/tasks/{id}`| Owner Only | Delete task (returns 204 No Content) | None |
| `GET` | `/tasks/all` | **ADMIN Only**| List all tasks across all users | None |

### User Management Endpoints (`/users`)
| Method | Endpoint | Access | Description | Request Body |
|---|---|---|---|---|
| `GET` | `/users` | **ADMIN Only**| List all registered users | None |
| `PATCH`| `/users/{id}/role` | **ADMIN Only**| Promote user to `ADMIN` or demote to `USER` | `{"role": "ADMIN"}` |

### System
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/health` | Public | Returns `{"status": "healthy"}` |

---

## 7. License & Credits

Built as part of the **TaskVault** backend architecture project. Feel free to use this codebase as a foundational template for your production FastAPI applications.
