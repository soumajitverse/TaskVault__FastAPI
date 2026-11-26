# TaskVault – Project Development Plan

A step-by-step implementation plan for building the TaskVault FastAPI backend in 2–3 hours.

---

## Progress Overview
- [x] **Phase 1: Environment and FastAPI Setup**
- [x] **Phase 2: PostgreSQL Connection and SQLAlchemy Models**
- [x] **Phase 3: Alembic Initialization and Database Migrations**
- [x] **Phase 4: User Schemas, Password Hashing & JWT Authentication**
- [ ] **Phase 5: Task CRUD Operations (Linked to Authenticated User)** *(In Progress)*
- [ ] **Phase 6: RBAC (Role-Based Access Control) & Ownership Isolation**
- [ ] **Phase 7: Custom Logging Middleware**
- [ ] **Phase 8: End-to-End Testing via Swagger UI**

---

## Detailed Phase Breakdown

### [x] Phase 1: Environment and FastAPI Setup
- [x] Create project directory structure.
- [x] Configure `.env` and `.env.example`.
- [x] Implement centralized settings in `app/core/config.py` using `pydantic-settings`.
- [x] Implement basic FastAPI app in `app/main.py` with `/health` route.
- [x] Verify `/docs` in Swagger UI.
- **Commit:** `feat: setup project structure, pydantic settings, and health check`

---

### [x] Phase 2: PostgreSQL Connection & SQLAlchemy Models
- [x] Implement declarative base in `app/database/base.py` using SQLAlchemy 2.0 `DeclarativeBase`.
- [x] Configure database engine, `SessionLocal`, and `get_db` generator dependency in `app/database/session.py`.
- [x] Implement `User` model in `app/models/user.py` (id, username, email, hashed_password, role, created_at, relationship).
- [x] Implement `Task` model in `app/models/task.py` (id, title, description, status, owner_id foreign key, created_at, relationship).
- [x] Verify models can be imported together without circular dependency issues.
- **Commit:** `feat: configure database session and define user and task models`

---

### [x] Phase 3: Alembic Migrations
- [x] Initialize Alembic with `alembic init alembic`.
- [x] Update `alembic/env.py` to import `settings.DATABASE_URL` and `Base.metadata`.
- [x] Import all models inside `env.py` so Alembic discovers tables.
- [x] Generate initial migration: `alembic revision --autogenerate -m "create users and tasks tables"`.
- [x] Review the generated migration file.
- [x] Apply migration: `alembic upgrade head`.
- [x] Understand rollback: `alembic downgrade -1`.
- **Commit:** `feat: setup alembic and run initial migration for users and tasks`

---

### [x] Phase 4: User Schemas, Password Hashing & JWT Authentication
- [x] Define Pydantic user schemas in `app/schemas/user.py` (`UserBase`, `UserCreate`, `UserLogin`, `UserResponse`, `Token`, `TokenData`).
- [x] Implement password hashing and verification using `pwdlib` (Argon2) in `app/core/security.py`.
- [x] Implement JWT token creation and decoding using `pyjwt` in `app/core/security.py`.
- [x] Implement authentication router in `app/routers/auth.py`:
  - `POST /auth/register` (Register user with hashed password; default role USER; email unique).
  - `POST /auth/login` (Clean JSON login with email/password; issue JWT access token).
  - `GET /auth/me` (Protected profile endpoint).
- [x] Create `get_current_user` dependency in `app/core/dependencies.py` using `HTTPBearer`.
- [x] Register auth router in `app/main.py`.
- [x] Test registration, login, and token authorization in Swagger UI.
- **Commit:** `feat: implement user schemas, password hashing, and jwt authentication`

---

### [ ] Phase 5: Task CRUD Operations (Linked to Authenticated User)
- [x] Define Pydantic task schemas in `app/schemas/task.py` (`TaskBase`, `TaskCreate`, `TaskUpdate`, `TaskResponse`).
- [ ] Implement task router in `app/routers/tasks.py` with SQLAlchemy 2.0 `select()` syntax:
  - `POST /tasks` (Create task, automatically setting `owner_id = current_user.id`).
  - `GET /tasks` (List tasks owned by the authenticated user).
  - `GET /tasks/{task_id}` (Get specific task owned by user; return 404 if not found or not owned).
  - `PUT /tasks/{task_id}` (Update task owned by user).
  - `DELETE /tasks/{task_id}` (Delete task owned by user).
- [ ] Register task router in `app/main.py`.
- [ ] Test task CRUD operations with bearer token authorization in Swagger UI.
- **Commit:** `feat: implement authenticated task crud endpoints`

---

### [ ] Phase 6: RBAC (Role-Based Access Control) & Ownership Isolation
- [ ] Create reusable `require_role(required_role)` dependency in `app/core/dependencies.py`.
- [ ] Implement admin user management router in `app/routers/users.py`:
  - `GET /users` (ADMIN only — list all users).
  - `GET /tasks/all` or `GET /admin/tasks` (ADMIN only — view all tasks across all users).
  - Admin override: allow ADMIN to manage/delete any task.
- [ ] Register user router in `app/main.py`.
- [ ] Verify RBAC barriers in Swagger UI (USER gets 403 Forbidden on admin endpoints).
- **Commit:** `feat: implement rbac dependencies and admin management endpoints`

---

### [ ] Phase 7: Custom Logging Middleware
- [ ] Implement custom HTTP middleware in `app/middleware/logging.py`:
  - Log incoming HTTP method.
  - Log requested URL/path.
  - Log response status code.
  - Measure and log request processing time (ms).
- [ ] Register middleware in `app/main.py`.
- [ ] Understand differences between Middleware and FastAPI `Depends`.
- [ ] Verify console output during requests.
- **Commit:** `feat: add request timing and logging middleware`

---

### [ ] Phase 8: End-to-End Testing via Swagger UI
- [ ] Register a standard user and an admin user.
- [ ] Authenticate in Swagger UI via the `Authorize` (Lock) button using JWT Bearer token.
- [ ] Perform complete task lifecycle as standard user.
- [ ] Verify resource isolation: ensure User B cannot access User A's tasks by guessing task IDs.
- [ ] Verify admin permissions across all resources.
- [ ] Final code verification, linting, and documentation check.
- **Commit:** `docs: complete taskvault api testing and verification`
