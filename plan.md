# TaskVault – Project Development Plan

A step-by-step implementation plan for building the TaskVault FastAPI backend in 2–3 hours.

---

## Progress Overview
- [x] **Phase 1: Environment and FastAPI Setup**
- [x] **Phase 2: PostgreSQL Connection and SQLAlchemy Models**
- [x] **Phase 3: Alembic Initialization and Database Migrations**
- [ ] **Phase 4: Task CRUD Operations** *(In Progress)*
- [ ] **Phase 5: JWT Authentication and Password Hashing**
- [ ] **Phase 6: RBAC and Resource Ownership Authorization**
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

### [ ] Phase 4: Task CRUD Operations
- [ ] Define Pydantic v2 schemas in `app/schemas/task.py`:
  - `TaskBase`, `TaskCreate`, `TaskUpdate`, `TaskResponse`.
- [ ] Implement task router in `app/routers/tasks.py` with SQLAlchemy 2.0 `select()` syntax:
  - `POST /tasks` (Create task)
  - `GET /tasks` (List tasks)
  - `GET /tasks/{task_id}` (Get task by ID)
  - `PUT /tasks/{task_id}` (Update task)
  - `DELETE /tasks/{task_id}` (Delete task)
- [ ] Register task router in `app/main.py`.
- [ ] Test task CRUD operations in Swagger UI.
- **Commit:** `feat: implement task CRUD schemas and router`

---

### [ ] Phase 5: JWT Authentication & Password Hashing
- [ ] Create security helpers in `app/core/security.py`:
  - Password hashing & verification using `pwdlib` (Argon2).
  - JWT token generation & decoding using `pyjwt`.
- [ ] Define user schemas in `app/schemas/user.py`:
  - `UserRegister`, `UserLogin`, `UserResponse`, `TokenResponse`.
- [ ] Implement authentication router in `app/routers/auth.py`:
  - `POST /auth/register` (Register user with hashed password; default role USER).
  - `POST /auth/login` (Verify credentials and issue JWT access token).
- [ ] Register auth router in `app/main.py`.
- [ ] Test user registration and token generation.
- **Commit:** `feat: implement password hashing and jwt authentication`

---

### [ ] Phase 6: RBAC & Resource Ownership Authorization
- [ ] Create authentication and authorization dependencies in `app/core/dependencies.py`:
  - `get_current_user` (extract and decode JWT bearer token).
  - `require_role(role)` (reusable dependency enforcing ADMIN or USER).
- [ ] Protect task endpoints with `get_current_user`:
  - Automatically assign `owner_id = current_user.id` on task creation.
  - Standard users can only view, update, and delete their own tasks.
  - 403 Forbidden / 404 Not Found if accessing another user's task.
- [ ] Implement admin user router in `app/routers/users.py`:
  - `GET /users` (ADMIN only).
  - `GET /tasks/all` (ADMIN only - view all users' tasks).
- [ ] Test role-based barriers in Swagger UI.
- **Commit:** `feat: add rbac dependencies and task ownership isolation`

---

### [ ] Phase 7: Custom Logging Middleware
- [ ] Implement custom middleware in `app/middleware/logging.py`:
  - Capture HTTP method, request URL/path, response status code, and execution time in ms.
- [ ] Register middleware in `app/main.py`.
- [ ] Understand differences between Middleware and FastAPI `Depends`.
- [ ] Verify console output during requests.
- **Commit:** `feat: add request timing and logging middleware`

---

### [ ] Phase 8: End-to-End Testing via Swagger UI
- [ ] Register regular user and login to get JWT.
- [ ] Authorize via Swagger UI "Authorize" button (`Bearer <token>`).
- [ ] Create, read, update, delete tasks as regular user.
- [ ] Verify non-owner cannot touch tasks.
- [ ] Test admin capabilities.
- [ ] Final code cleanup and documentation review.
- **Commit:** `docs: complete taskvault api testing and verification`
