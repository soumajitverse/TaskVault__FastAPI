# TaskVault – Production-Grade FastAPI Backend & Engineering Guide

TaskVault is an enterprise-grade Task Management REST API built from the ground up using **Python 3.12+**, **FastAPI**, **SQLAlchemy 2.0**, and **Neon Serverless PostgreSQL**.

This repository is engineered to serve two distinct purposes:
1. **A Production-Ready Backend**: A secure, high-performance task management API with JWT authentication, granular Role-Based Access Control (RBAC), database migrations, and structured request-timing middleware.
2. **An End-to-End Educational Blueprint**: A comprehensive reference manual for Python developers looking to master modern asynchronous backend engineering, database architectures, and API security.

---

## Table of Contents
1. [Project Overview & Architectural Design](#1-project-overview--architectural-design)
2. [Complete Tech Stack & Deep Dependency Analysis](#2-complete-tech-stack--deep-dependency-analysis)
3. [Database Architecture: Neon Serverless PostgreSQL](#3-database-architecture-neon-serverless-postgresql)
4. [Comprehensive Directory & File Map](#4-comprehensive-directory--file-map)
5. [Step-by-Step Local Setup & Execution Guide](#5-step-by-step-local-setup--execution-guide)
6. [The FastAPI Backend Masterclass (Core Concepts Deep Dive)](#6-the-fastapi-backend-masterclass-core-concepts-deep-dive)
   - [6.1. Pydantic v2 Schemas vs. SQLAlchemy 2.0 ORM Models](#61-pydantic-v2-schemas-vs-sqlalchemy-20-orm-models)
   - [6.2. Modern SQLAlchemy 2.0 Syntax (`Mapped` and `select`)](#62-modern-sqlalchemy-20-syntax-mapped-and-select)
   - [6.3. Relational Modeling & Cascading Deletions](#63-relational-modeling--cascading-deletions)
   - [6.4. Database Session Lifecycles (`yield db` and Connection Leaks)](#64-database-session-lifecycles-yield-db-and-connection-leaks)
   - [6.5. Database Schema Version Control with Alembic](#65-database-schema-version-control-with-alembic)
   - [6.6. Cryptographic Security: Argon2 Hashing & JWT Authentication](#66-cryptographic-security-argon2-hashing--jwt-authentication)
   - [6.7. Role-Based Access Control (RBAC) via Dependency Factories](#67-role-based-access-control-rbac-via-dependency-factories)
   - [6.8. Mitigation of IDOR (Insecure Direct Object References)](#68-mitigation-of-idor-insecure-direct-object-references)
   - [6.9. ASGI Middleware vs. Route-Level Dependencies](#69-asgi-middleware-vs-route-level-dependencies)
7. [Automated Testing Suite (`pytest` & `TestClient`)](#7-automated-testing-suite-pytest--testclient)
8. [Comprehensive REST API Reference & Swagger UI Guide](#8-comprehensive-rest-api-reference--swagger-ui-guide)
9. [Production Deployment & Security Hardening Checklist](#9-production-deployment--security-hardening-checklist)
10. [License & Acknowledgments](#10-license--acknowledgments)

---

## 1. Project Overview & Architectural Design

TaskVault follows the **Layered Clean Architecture** pattern. This separates user-facing data validation, business logic, authorization rules, and persistent storage into distinct, loosely-coupled layers.

### Architectural Request-Response Flow
```text
[ Client (Browser / Postman / Swagger UI) ]
                     │
                     ▼
         [ Logging Middleware ]
      (Measures latency in ms, logs HTTP method, path, and response status)
                     │
                     ▼
             [ API Routers ]
      (Route dispatching: /auth, /tasks, /users)
                     │
     ┌───────────────┴───────────────────────────────┐
     ▼                                               ▼
[ Pydantic v2 Schemas ]                 [ FastAPI Dependencies ]
 • Validates incoming payload shapes     • get_db: Yields DB session
 • Rejects malformed types (422)         • get_current_user: Decodes JWT
 • Strips sensitive fields on response   • require_admin: Enforces RBAC (403)
                                                     │
                                                     ▼
                                          [ SQLAlchemy 2.0 ORM ]
                                           • select() queries
                                           • Session unit-of-work
                                           • Model relationships
                                                     │
                                                     ▼
                                          [ Neon PostgreSQL DB ]
```

### Key Architectural Tenets:
- **Strict Decoupling**: Database models (`app/models/`) are strictly separated from API transfer models (`app/schemas/`). Database internals (like password hashes) are never directly exposed over HTTP.
- **Fail-Fast Configuration**: Settings are centralized and validated on application startup. If a required secret or database URL is absent, the server refuses to start rather than failing mid-request.
- **Defensive Resource Ownership**: Standard users are isolated within their own data sandbox. Cross-tenant data tampering is rejected at the database query level.

---

## 2. Complete Tech Stack & Deep Dependency Analysis

Every package in TaskVault's `requirements.txt` was selected to fulfill a specific production requirement:

| Library | Version Category | Purpose in TaskVault | Technical Justification |
|---|---|---|---|
| **`fastapi`** | Web Framework | API routing, documentation, validation integration | Chosen for its native asynchronous capabilities, automatic OpenAPI (Swagger UI) generation, and dependency injection system (`Depends`). |
| **`uvicorn[standard]`** | ASGI Server | Production HTTP/Websocket server | Blazing fast ASGI server powered by `uvloop` (an ultra-fast C-based asyncio event loop) and `httptools` (Node.js HTTP parser ported to Python). |
| **`sqlalchemy`** | ORM (v2.0+) | Object Relational Mapping & Connection Pool | Modern SQLAlchemy 2.0 removes legacy ambiguity by introducing full Python type-hinting support (`Mapped[...]`), declarative bases, and SQL-like `select()` syntax. |
| **`psycopg2-binary`** | Database Driver | PostgreSQL TCP Socket Adapter | The most battle-tested C-extension driver for PostgreSQL in the Python ecosystem. Provides robust connection management and SSL handshake support. |
| **`alembic`** | Migrations | Schema version control | Automates database schema evolution over time. Compares Python models against database catalogs to autogenerate migration files. |
| **`pydantic-settings`** | Configuration | Environment variable loading & validation | Reads variables from `.env` files and system environments, parsing strings into typed Python booleans, integers, and URLs on boot. |
| **`pyjwt`** | Authentication | JWT signing and signature verification | Implements RFC 7519 JSON Web Tokens. Encodes user identity into a compact, cryptographically tamper-proof token using HMAC-SHA256 (`HS256`). |
| **`pwdlib[argon2]`** | Password Hashing | Cryptographic one-way password hashing | Modern successor to passlib. Uses **Argon2id**, the winner of the Password Hashing Competition. Resistant to brute-force attacks via GPUs and ASICs. |
| **`python-multipart`** | Form Parser | Parsing form data | Required by FastAPI when handling OAuth2 password flows or standard URL-encoded form submissions. |
| **`pytest`** | Testing Engine | Test execution runner | Standard Python test framework used to discover, execute, and assert automated API test suites. |
| **`httpx`** | HTTP Client | ASGI in-memory client for testing | Powers FastAPI's `TestClient`, allowing tests to simulate fast, non-network HTTP requests directly into the FastAPI ASGI interface. |

---

## 3. Database Architecture: Neon Serverless PostgreSQL

TaskVault is architected to communicate with **[Neon](https://neon.tech)**, a cloud-native, serverless PostgreSQL service.

### Neon Architectural Advantages:
1. **Separation of Compute and Storage**: Neon separates the PostgreSQL processing nodes from storage, allowing instant database scale-to-zero when idle, and millisecond cold-starts upon incoming queries.
2. **Database Branching**: Allows creating isolated instant clones of the database schema and data for staging, migrations, and CI/CD testing without affecting production.
3. **Always-On SSL**: Neon enforces SSL encrypted TCP tunnels (`sslmode=require`) to ensure credentials and payloads are encrypted in transit.

### Connection String Mechanics
SQLAlchemy 2.0 utilizes driver prefixes to determine how to connect:
```text
postgresql+psycopg2://<username>:<password>@<neon-hostname>.neon.tech/<database_name>?sslmode=require
```

### Self-Healing Connection String Parser:
Cloud providers and hosting platforms frequently supply connection strings prefixed with `postgres://` or `postgresql://`. In `app/core/config.py`, TaskVault implements a Pydantic `field_validator` that intercepts and normalizes the connection string dynamically:
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

## 4. Comprehensive Directory & File Map

```text
FastAPI__Final/
├── app/
│   ├── core/
│   │   ├── config.py          # Centralized Pydantic BaseSettings class loading .env
│   │   ├── security.py        # Argon2 hashing utilities & JWT encode/decode functions
│   │   └── dependencies.py    # get_current_user token decoder & require_role RBAC guard
│   ├── database/
│   │   ├── base.py            # DeclarativeBase defining the SQLAlchemy metadata registry
│   │   └── session.py         # SQLAlchemy engine configuration & get_db session generator
│   ├── models/
│   │   ├── __init__.py        # Exposes User and Task models to metadata registry
│   │   ├── user.py            # User ORM model (id, username, email, hashed_password, role)
│   │   └── task.py            # Task ORM model (id, title, description, status, owner_id)
│   ├── schemas/
│   │   ├── user.py            # Pydantic schemas (UserBase, UserCreate, UserLogin, UserResponse)
│   │   └── task.py            # Pydantic schemas (TaskBase, TaskCreate, TaskUpdate, TaskResponse)
│   ├── routers/
│   │   ├── auth.py            # /auth/register, /auth/login, /auth/me endpoints
│   │   ├── tasks.py           # Authenticated Task CRUD endpoints with anti-IDOR checks
│   │   └── users.py           # Admin endpoints: list users and PATCH user role
│   ├── middleware/
│   │   └── logging.py         # Starlette ASGI middleware logging method, path, status & latency
│   ├── __init__.py            # Application package marker
│   └── main.py                # FastAPI app initialization, middleware wiring & router registration
├── alembic/
│   ├── versions/              # Migration files versioning PostgreSQL table states
│   ├── env.py                 # Migration runtime environment connecting Base.metadata to Neon
│   └── script.py.mako         # Template used to generate new migration scripts
├── tests/
│   ├── __init__.py            # Tests package marker
│   └── test_main.py           # Pytest test suite (Health, Auth, Task CRUD, IDOR, RBAC)
├── .env.example               # Safe environment variable template for deployment
├── .gitignore                 # Excludes .venv, bytecode, and .env secrets from source control
├── alembic.ini                # Alembic CLI configuration file
├── plan.md                    # Verified 8-phase project implementation roadmap
├── README.md                  # Comprehensive architectural and educational documentation
└── requirements.txt           # Pinned production and development dependencies
```

---

## 5. Step-by-Step Local Setup & Execution Guide

Follow these instructions to run TaskVault locally from a clean terminal:

### 1. Clone the Codebase
```bash
git clone https://github.com/soumajitverse/TaskVault__FastAPI.git
cd TaskVault__FastAPI
```

### 2. Configure a Virtual Environment
Isolates project packages from your global operating system Python:
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

### 3. Install Required Packages
```bash
pip install -r requirements.txt
pip install pytest httpx
```

### 4. Setup Environment Secrets
Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Edit `.env` with your actual Neon PostgreSQL connection string and a secret key:
```env
PROJECT_NAME="TaskVault"
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<neon-host>.neon.tech/<dbname>?sslmode=require"
SECRET_KEY="super-secret-random-key-change-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Apply Database Migrations
Synchronize your Neon PostgreSQL cloud database with our SQLAlchemy models:
```bash
alembic upgrade head
```

### 6. Seed the Initial Admin Account
Because public registration strictly defaults to standard `USER`, run this bootstrap command to create the verified administrative user in PostgreSQL:
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

### 7. Run the Development Server
```bash
uvicorn app.main:app --reload
```
The server will boot at `http://127.0.0.1:8000`.

Interactive documentation will be available at:
- **Swagger UI Interactive Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Alternate Docs:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 6. The FastAPI Backend Masterclass (Core Concepts Deep Dive)

This section breaks down the foundational engineering paradigms that power professional Python backends.

---

### 6.1. Pydantic v2 Schemas vs. SQLAlchemy 2.0 ORM Models

Beginners frequently ask: *"Why define `User` in `models/user.py` and again in `schemas/user.py`?"*

```text
┌───────────────────────────────────────────────┐
│              HTTP Request (JSON)              │
│       {"email": "alice@test.com", ...}        │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│        Pydantic Schema (app/schemas/)         │
│  • Enforces validation rules (regex, length)  │
│  • Parses JSON into clean Python types        │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│         SQLAlchemy ORM (app/models/)          │
│  • Represents rows in PostgreSQL              │
│  • Executes SQL transactions, joins, foreign  │
│    key cascades                               │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│             PostgreSQL Database               │
│               [ users table ]                 │
└───────────────────────────────────────────────┘
```

1. **SQLAlchemy Models (`app/models/`)** represent **state at rest in the database**. They map directly to columns, foreign key constraints, and relational cascades inside PostgreSQL.
2. **Pydantic Schemas (`app/schemas/`)** represent **data contracts over the wire**. They validate incoming HTTP requests and format outgoing HTTP responses.

#### The Data Protection Boundary:
When a user registers, the database saves `hashed_password`. When returning the user profile via HTTP, `UserResponse` explicitly omits `hashed_password`. Even though the database model holds the hash, Pydantic's serialization guarantees it is never emitted in the response JSON.

#### The `from_attributes = True` Bridge:
```python
class TaskResponse(TaskBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```
In Python, dictionary access uses brackets (`task["title"]`), while ORM model instances use attributes (`task.title`). By setting `from_attributes=True` (formerly `orm_mode` in Pydantic v1), Pydantic is instructed to read attributes directly from SQLAlchemy objects and serialize them into JSON.

---

### 6.2. Modern SQLAlchemy 2.0 Syntax (`Mapped` and `select`)

In legacy SQLAlchemy 1.x, models were declared using untyped `Column()` constructs, and queries relied on `db.query()`.

SQLAlchemy 2.0 modernized this to provide full static type-checking and explicit queries:

```python
# app/models/task.py
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
```

- **`Mapped[T]`**: Type annotation recognized by IDEs (VS Code, PyCharm) and static linters (Mypy, Pyright). `task.id` is typed as an `int`, not a generic column.
- **`Mapped[str | None]`**: Explicitly documents that the column is nullable in PostgreSQL.

#### Modern 2.0 Query Style:
```python
# Legacy 1.x: db.query(Task).filter(Task.owner_id == user_id).all()
# Modern 2.0:
query = select(Task).where(Task.owner_id == user_id)
tasks = db.scalars(query).all()
```
`select()` mirrors standard SQL statements. `scalars()` unpacks row tuples directly into model instances.

---

### 6.3. Relational Modeling & Cascading Deletions

TaskVault establishes a classic **One-to-Many** relationship between `User` and `Task`:

```text
┌─────────────────────────┐             ┌─────────────────────────┐
│          users          │             │          tasks          │
├─────────────────────────┤             ├─────────────────────────┤
│ id (PK)                 │───1─────N───┤ id (PK)                 │
│ username                │             │ title                   │
│ email                   │             │ owner_id (FK -> users)  │
│ hashed_password         │             │ status                  │
└─────────────────────────┘             └─────────────────────────┘
```

#### In `app/models/user.py`:
```python
tasks: Mapped[list["Task"]] = relationship(
    "Task", back_populates="owner", cascade="all, delete-orphan"
)
```

#### In `app/models/task.py`:
```python
owner_id: Mapped[int] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
)
owner: Mapped["User"] = relationship("User", back_populates="tasks")
```

#### Dual-Layer Cascading:
1. **Database Level (`ondelete="CASCADE"`)**: PostgreSQL enforces referential integrity. If a user is deleted directly via SQL, PostgreSQL automatically deletes all tasks linked to that user's ID.
2. **Application Level (`cascade="all, delete-orphan"`)**: If a task is removed from `user.tasks` in Python memory, SQLAlchemy emits a `DELETE` statement to remove the orphan row from the database.

---

### 6.4. Database Session Lifecycles (`yield db` and Connection Leaks)

Database connections are costly to establish. Applications use a **Connection Pool** to keep open TCP sockets to PostgreSQL.

If route handlers forget to close database sessions, connections remain open indefinitely until the database connection pool is exhausted, crashing the backend (known as a **Connection Leak**).

FastAPI prevents this via Python **generator functions** and dependency injection:

```python
# app/database/session.py
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### Execution Lifecycle During a Request:
1. **Entry**: An incoming request reaches a route declaring `db: Session = Depends(get_db)`.
2. **Allocation**: `SessionLocal()` borrows a connection from the engine pool.
3. **Yield**: Execution pauses at `yield db`, passing the active session to the route logic.
4. **Endpoint Runs**: The route issues queries and commits transactions.
5. **The `finally` Guarantee**: When the route completes—**even if an unhandled exception or crash occurred**—FastAPI resumes execution after `yield` and runs `db.close()`. The connection is returned to the pool, guaranteeing zero connection leaks.

---

### 6.5. Database Schema Version Control with Alembic

In real-world applications, database tables cannot be dropped and recreated when models change, as this would erase production data.

Alembic provides a linear migration history tracking changes across revisions:

```text
[ Base Database ] ──► [ Rev 1: create users & tasks ] ──► [ Rev 2: make username non-unique ]
```

#### Core Alembic Workflow:
1. **Model Modification**: You update a model (e.g. adding a column in `app/models/task.py`).
2. **Generate Migration**:
   ```bash
   alembic revision --autogenerate -m "add task priority column"
   ```
   Alembic compares `Base.metadata` against PostgreSQL and creates a new file in `alembic/versions/`.
3. **Review Migration Script**: You inspect the generated `upgrade()` and `downgrade()` Python functions.
4. **Apply Migration**:
   ```bash
   alembic upgrade head
   ```
   Applies the SQL statements and records the new version hash in PostgreSQL's `alembic_version` table.
5. **Rollback (if needed)**:
   ```bash
   alembic downgrade -1
   ```

---

### 6.6. Cryptographic Security: Argon2 Hashing & JWT Authentication

#### Password Hashing with Argon2id
Plaintext passwords must never be stored. TaskVault uses **`pwdlib` with Argon2id**:
- Argon2 was the winner of the global Password Hashing Competition.
- Unlike legacy algorithms (MD5, SHA256, or traditional bcrypt), Argon2 is **memory-hard**. It requires significant RAM to compute, making hardware brute-force attacks via parallel GPUs or specialized ASIC chips prohibitively expensive.
- **Salt Generation**: Every hash contains a unique, cryptographically random salt to neutralize precomputed rainbow table attacks.
- **Constant-Time Verification**: `verify_password()` compares password hashes in constant CPU time to prevent timing attacks.

#### JSON Web Token (JWT) Structure
When credentials are confirmed via `POST /auth/login`, TaskVault generates a signed JWT:
```text
┌──────────────────────┬──────────────────────┬──────────────────────┐
│        Header        │       Payload        │      Signature       │
│  {"alg": "HS256"}    │ {"sub": "1",         │ HMAC-SHA256(         │
│                      │  "role": "USER",     │   header + payload,  │
│                      │  "exp": 1732707400}  │   SECRET_KEY)        │
└──────────────────────┴──────────────────────┴──────────────────────┘
```
- **Stateless Verification**: The backend does not need to query a Redis session store to verify login validity. The signature guarantees the payload was not tampered with.
- **Expiration Protection**: The `"exp"` claim enforces automatic expiration (30 minutes default). Expired tokens are rejected automatically by `jwt.decode`.

---

### 6.7. Role-Based Access Control (RBAC) via Dependency Factories

TaskVault implements role gating via a **Higher-Order Dependency Factory**:

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

#### Architectural Elegance:
- **Nested Dependency Injection**: `role_checker` depends on `get_current_user`. FastAPI automatically validates the JWT, looks up the user, and hands it to `role_checker`.
- **401 Unauthorized vs. 403 Forbidden**:
  - `401 Unauthorized`: Authentication failed (missing, invalid, or expired token). *"I do not know who you are."*
  - `403 Forbidden`: Authentication succeeded, but authorization failed. *"I know who you are, but you do not have permission to access this resource."*
- **Reusability**: New roles (`MANAGER`, `MODERATOR`) can be introduced with zero boilerplate by calling `require_role("MANAGER")`.

---

### 6.8. Mitigation of IDOR (Insecure Direct Object References)

An **IDOR** vulnerability occurs when an application exposes a database identifier (e.g. `/tasks/42`) without verifying whether the requesting user owns that object.

#### Vulnerable Code Example:
```python
# DANGEROUS: Attacker can change task_id to steal or delete any user's task
@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.scalar(select(Task).where(Task.id == task_id))
    db.delete(task)
```

#### TaskVault Secure Implementation:
```python
# app/routers/tasks.py
@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).where(
        Task.id == task_id,
        Task.owner_id == current_user.id  # Strict ownership isolation!
    )
    task = db.scalar(query)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```
- **Why Return 404 Instead of 403?** Returning `403 Forbidden` informs an attacker that Task #42 exists in the database. Returning `404 Not Found` reveals zero information: to unauthorized users, other users' tasks do not exist.

---

### 6.9. ASGI Middleware vs. Route-Level Dependencies

| Evaluation Angle | Custom Middleware (`BaseHTTPMiddleware`) | FastAPI Dependency (`Depends`) |
|---|---|---|
| **Invocation Scope** | **Global**: Executes on every single HTTP request entering the ASGI server. | **Targeted**: Executes only on routes that explicitly include the dependency. |
| **Execution Point** | Runs before routing starts and after response is generated. | Runs during route resolution after path matching. |
| **Access Level** | Intercepts raw ASGI requests, headers, and responses. | Accesses validated models, path parameters, and injected DB sessions. |
| **Typical Use Cases** | Request timing, global latency metrics, CORS, security headers. | Authentication, authorization (RBAC), database session provisioning. |

#### TaskVault Timing Middleware:
In `app/middleware/logging.py`, our middleware measures request latency:
```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {process_time_ms:.2f}ms"
        )
        return response
```

---

## 7. Automated Testing Suite (`pytest` & `TestClient`)

TaskVault includes an automated test suite in `tests/test_main.py` using **`pytest`** and FastAPI's in-memory **`TestClient`**.

### What the Test Suite Verifies:
1. **`test_health_check`**: Asserts `/health` returns `200 OK` and `{"status": "healthy"}`.
2. **`test_auth_registration_and_login`**:
   - Asserts password hashes are **not** present in outgoing registration payloads.
   - Asserts duplicate email registrations are rejected with `HTTP 400 Bad Request`.
   - Asserts valid credentials yield a signed JWT token that successfully authenticates `/auth/me`.
3. **`test_task_crud_and_isolation` (Anti-IDOR Verification)**:
   - Registers User A (Alice) and User B (Bob).
   - Alice creates a private task.
   - Asserts that Bob receives **`404 Not Found`** when attempting to read, modify, or delete Alice's task.
   - Asserts Alice can update and delete her own task successfully.
4. **`test_rbac_security_barriers`**:
   - Asserts standard users receive **`403 Forbidden`** when attempting to access `/users` or `/tasks/all`.
   - Asserts administrators receive **`200 OK`** on both administrative endpoints.

### Executing the Tests:
Ensure `pytest` and `httpx` are installed:
```bash
pip install pytest httpx
```
Run the test runner with verbose output:
```bash
pytest -v
```

Expected output:
```text
tests/test_main.py::test_health_check PASSED                    [ 25%]
tests/test_main.py::test_auth_registration_and_login PASSED     [ 50%]
tests/test_main.py::test_task_crud_and_isolation PASSED         [ 75%]
tests/test_main.py::test_rbac_security_barriers PASSED          [100%]

============================== 4 passed in 2.15s ==============================
```

---

## 8. Comprehensive REST API Reference & Swagger UI Guide

All endpoints are self-documenting and interactive at `http://127.0.0.1:8000/docs`.

### Authentication Endpoints (`/auth`)
| Method | Endpoint | Access Level | Description | Request Body | Response Codes |
|---|---|---|---|---|---|
| `POST` | `/auth/register` | Public | Register new user (defaults to role `USER`) | `{"username": "...", "email": "...", "password": "..."}` | `201`, `400`, `422` |
| `POST` | `/auth/login` | Public | Authenticate with email & password | `{"email": "...", "password": "..."}` | `200`, `401`, `422` |
| `GET` | `/auth/me` | Authenticated | Retrieve current user profile | None (Bearer Token in Header) | `200`, `401` |

### Task Endpoints (`/tasks`)
| Method | Endpoint | Access Level | Description | Request Body | Response Codes |
|---|---|---|---|---|---|
| `POST` | `/tasks` | Authenticated | Create a new task (auto-assigned to user) | `{"title": "...", "description": "...", "status": "PENDING"}` | `201`, `401`, `422` |
| `GET` | `/tasks` | Authenticated | List all tasks owned by current user | None | `200`, `401` |
| `GET` | `/tasks/all` | **ADMIN Only**| List all tasks across all users | None | `200`, `401`, `403` |
| `GET` | `/tasks/{id}` | Owner Only | Retrieve specific task by ID | None | `200`, `401`, `404` |
| `PUT` | `/tasks/{id}` | Owner Only | Partial/Full update task attributes | `{"status": "COMPLETED"}` (all fields optional) | `200`, `401`, `404`, `422` |
| `DELETE` | `/tasks/{id}`| Owner Only | Delete specific task | None | `204`, `401`, `404` |

### Administrative User Endpoints (`/users`)
| Method | Endpoint | Access Level | Description | Request Body | Response Codes |
|---|---|---|---|---|---|
| `GET` | `/users` | **ADMIN Only**| List all registered users | None | `200`, `401`, `403` |
| `PATCH`| `/users/{id}/role` | **ADMIN Only**| Promote user to `ADMIN` or demote to `USER` | `{"role": "ADMIN"}` | `200`, `401`, `403`, `404` |

### System Endpoints
| Method | Endpoint | Access Level | Description | Response Codes |
|---|---|---|---|---|
| `GET` | `/health` | Public | Returns `{"status": "healthy"}` | `200` |

---

## 9. Production Deployment & Security Hardening Checklist

When preparing TaskVault for production cloud hosting (e.g. AWS, Render, Fly.io, Railway, DigitalOcean):

- [ ] **Rotate Secret Keys**: Generate a strong cryptographic secret:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
  Set this as `SECRET_KEY` in your cloud provider environment dashboard. Never commit `.env` to Git.
- [ ] **Enforce HTTPS**: Ensure your reverse proxy (Cloudflare, NGINX, AWS ALB) terminates SSL so all tokens and credentials are encrypted in transit.
- [ ] **Configure Connection Pooling**: When deploying serverless containers (like AWS Lambda or Google Cloud Run) against Neon PostgreSQL, configure Neon's connection pooler (`-pooler` hostname) to avoid exhausting PostgreSQL connection slots.
- [ ] **Turn Off Debugging**: Ensure `echo=False` on the SQLAlchemy engine to prevent query parameters from being printed to cloud logs.
- [ ] **Containerization**: Use a multi-stage Docker build with a non-root user for security isolation.

---

## 10. License & Acknowledgments

TaskVault is licensed under the **MIT License**. Built as an open architectural reference for production FastAPI backend systems.
