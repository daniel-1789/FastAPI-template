# FastAPI Template

A minimal starting point for a Python backend built on **FastAPI**, **SQLAlchemy 2.x (async)**, **Alembic**, and **Pydantic v2**. Talks to **MySQL** out of the box; swap the driver/URL for Postgres/etc. when a project outgrows it.

The endpoints in `app/main.py` (`GET /items`, `GET /items/{id}`, `POST /items`) are scaffolding — delete them and replace with real domain models. The plumbing (engine, session dependency, Alembic wiring, settings) is the part worth keeping.

## Layout

| Path | Purpose |
| --- | --- |
| `app/main.py` | FastAPI app + routes. |
| `app/database.py` | Async engine, session factory, `get_session` dependency, `Base`. |
| `app/models.py` | SQLAlchemy ORM models. |
| `app/schemas.py` | Pydantic request/response models. Drives `/docs`. |
| `app/crud.py` | Async DB ops, kept separate from route handlers. |
| `app/config.py` | `pydantic-settings`, reads `.env`. |
| `alembic/` | Migration env + `versions/`. |
| `alembic.ini` | Alembic config (URL injected from `app.config`). |
| `requirements.txt` | Pinned dependencies. |
| `.env.example` | Copy to `.env` and edit. |

## Setup

### 1. Python venv

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. MySQL

Install and start a local MySQL server:

```shell
brew install mysql
brew services start mysql
```

Create the database and (optionally) a dedicated user. The defaults in `.env.example` assume the root account with password `root` — fine for local dev, change for anything real:

```shell
mysql -uroot -e "CREATE DATABASE app;"
mysql -uroot -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';"
```

Copy the env template:

```shell
cp .env.example .env
```

Edit `.env` if your MySQL user/password/port differs. The format is:

```
mysql+asyncmy://<user>:<password>@<host>:<port>/<database>
```

### 3. Run migrations

```shell
alembic upgrade head
```

This creates the `items` table. The initial migration is checked in at `alembic/versions/20260523_0001_create_items.py`.

To generate a new migration after editing models:

```shell
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

### 4. Run the API

```shell
uvicorn app.main:app --reload
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- Health: <http://127.0.0.1:8000/healthz>

## Try it

```shell
curl -X POST http://127.0.0.1:8000/items \
  -H 'Content-Type: application/json' \
  -d '{"name": "Widget", "description": "a thing", "price": 9.99}'

curl http://127.0.0.1:8000/items
curl http://127.0.0.1:8000/items/1
```

## Debugging in PyCharm Pro

PyCharm Pro ships a native FastAPI run config that disables uvicorn's reloader under the debugger so breakpoints actually fire (uvicorn's `--reload` spawns a child process the debugger can't attach to).

1. **Run → Edit Configurations → + → FastAPI**
2. Fill in:
   - **Name**: `FastAPI`
   - **Application file**: `app/main.py`
   - **Application name**: `app` (the `FastAPI(...)` instance)
   - **Uvicorn options**: leave empty (or `--host 127.0.0.1 --port 8000`)
   - **Python interpreter**: the project venv (`./venv/bin/python`)
   - **Working directory**: project root
3. Apply → OK.
4. Set a breakpoint (e.g. on the `return` of a route in `app/main.py`).
5. Hit the **Debug** button (bug icon, ⌃D).
6. Trigger the endpoint from <http://127.0.0.1:8000/docs>.

`.env` is loaded automatically by `pydantic-settings` — no EnvFile plugin needed.

Debugger tip: SQLAlchemy `Result` objects (e.g. what `session.execute(...)` returns) are cursor wrappers and hard to read in the inspector. Materialize them into a named local (`items = list(result.scalars().all())`) and break on the line that uses `items` — much nicer to inspect. Also: never call `result.scalars().all()` from PyCharm's *Evaluate Expression* — it consumes the cursor and the real `return` will give back `[]`.

## Managing dependencies

When you `pip install` something new during development, freeze the lockfile so the next clone reproduces your environment:

```shell
pip install <package>
pip freeze > requirements.txt
```

`pip freeze` writes every package in the active venv with exact versions. Make sure the venv is activated first (`source venv/bin/activate`) — otherwise you'll capture your system Python's packages instead.

To upgrade a pinned package later:

```shell
pip install --upgrade <package>
pip freeze > requirements.txt
```

## Using this as a starting point

1. Clone or copy this directory into a new repo.
2. **Rename the database** — see below. Don't leave it as `app`, or every project off this template ends up sharing one database in your local MySQL.
3. Rename the `Item` model in `app/models.py` and the matching schemas/routes to your domain.
4. Drop `alembic/versions/20260523_0001_create_items.py` and run `alembic revision --autogenerate -m "initial"` to regenerate against your new models.
5. Want Postgres instead? Replace `asyncmy` with `asyncpg` in `requirements.txt` and use `postgresql+asyncpg://...` in `DATABASE_URL`. Nothing else changes.

### Renaming the database

The template ships with a database named `app`. For a real project, pick a name that matches the repo (e.g. `widgets`, `invoicing`) so your local MySQL doesn't turn into a junk drawer.

1. **Create the new database in MySQL:**

   ```shell
   mysql -uroot -proot -e "CREATE DATABASE widgets;"
   ```

2. **Update `.env`** — change the last path segment of `DATABASE_URL`:

   ```
   DATABASE_URL=mysql+asyncmy://root:root@127.0.0.1:3306/widgets
   ```

3. **Update `.env.example`** to match, so anyone else cloning the repo gets the right default.

4. **Update the default in `app/config.py`** — the `database_url` field's default string is the fallback when `.env` is missing. Keep it consistent so the same name appears everywhere.

5. **Run migrations against the new database:**

   ```shell
   alembic upgrade head
   ```

6. **(Optional) Drop the old `app` database** once you've confirmed everything works against the new one:

   ```shell
   mysql -uroot -proot -e "DROP DATABASE app;"
   ```

That's it — three places to edit (`.env`, `.env.example`, `app/config.py`) plus the `CREATE DATABASE`. The Alembic config doesn't need touching; it reads the URL from `app.config` and follows along automatically.

## Design notes

- **Async all the way down.** The engine is `create_async_engine`, sessions are `AsyncSession`, routes are `async def`. Alembic's `env.py` uses `async_engine_from_config` + `run_sync` so migrations work against the same URL.
- **One settings object.** `app/config.py` is the single source for env-driven config; both the app and Alembic import it. Don't read env vars elsewhere.
- **Sessions per request.** `get_session` yields a fresh `AsyncSession` per request and closes it when the handler returns. Don't share sessions across requests.
- **CRUD module, not fat routes.** `app/crud.py` keeps DB logic out of route handlers so routes stay thin and testable.
