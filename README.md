# MovieLens Web Application (FastAPI + PostgreSQL)

A server-rendered web application built on the MovieLens dataset. Visitors can search and browse movies, and a password-protected admin panel provides full create, read, update and delete (CRUD) control over the movie catalogue.

The project is deliberately built without an ORM and without pandas: every database interaction is hand-written, parameterized SQL executed through `psycopg2`, and every page is rendered on the server with Jinja2.

## Features

**Public site**
- Browse the movie catalogue with title search (case-insensitive) and pagination ("Page X of Y", Previous / Next).
- Movie detail page showing every individual rating and every user tag.
- Clean 404 page for movie IDs that do not exist; non-numeric IDs are rejected by FastAPI's own type validation.

**Admin panel**
- Login-protected dashboard listing movies with their average rating.
- Add, edit and delete movies.
- Duplicate `movie_id` is detected before insert and reported with HTTP 409.
- Deleting a movie that still has ratings, tags or links is blocked by PostgreSQL's foreign keys; the application catches the violation and shows a clear message instead of a server error.

**Security**
- Admin password stored only as a bcrypt hash (via passlib); the plain password is never stored or compared directly.
- Login state kept in a cryptographically signed session cookie (Starlette `SessionMiddleware` + `itsdangerous`).
- All SQL uses `%s` placeholders, which removes SQL injection from the search box and every form.
- Secrets live in `.env`, which is excluded from version control.

**Interface**
- Dark, Netflix-inspired theme written in plain CSS using custom properties (one place to change the whole palette).
- Vanilla JavaScript used for one purpose only: a confirmation dialog before deleting a movie.

## Tech stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Server | Uvicorn (ASGI) |
| Templating | Jinja2 |
| Database | PostgreSQL |
| Database driver | psycopg2-binary (raw SQL) |
| Password hashing | passlib + bcrypt |
| Sessions | Starlette SessionMiddleware + itsdangerous |
| Form handling | python-multipart |
| Configuration | python-dotenv |

## Architecture

```
Browser
   |
Uvicorn (ASGI server)
   |
main.py  -  FastAPI app, SessionMiddleware, /static mount
   |
   +-- routers/public.py   (no login required)
   +-- routers/admin.py    (guarded by require_login from auth.py)
            |
            +-- database.py   (the only file that contains SQL)
            |        |
            |    PostgreSQL ("movielens" database)
            |
            +-- templates_config.py  ->  templates/*.html (Jinja2)
```

Key design decisions:
- `database.py` is the only module allowed to contain SQL. Routers call its functions and never see SQL.
- `auth.py` is the single definition of what a valid login is, and exposes `require_login`, a FastAPI dependency that redirects (HTTP 303) to the login page when the session is not authenticated.
- `templates_config.py` holds the shared `Jinja2Templates` object in its own module to avoid a circular import between `main.py` and the routers.
- Each database function opens and closes its own connection so concurrent visitors stay isolated. Connection pooling (`psycopg2.pool.SimpleConnectionPool`) is the documented next step.

## Project structure

```
movielens_webapp/
|-- main.py
|-- auth.py
|-- database.py
|-- generate_password_hash.py
|-- templates_config.py
|-- requirements.txt
|-- .env.example
|-- routers/
|   |-- __init__.py
|   |-- public.py
|   `-- admin.py
|-- static/
|   |-- css/style.css
|   `-- js/main.js
`-- templates/
    |-- base.html
    |-- public/   (home.html, movie_detail.html, not_found.html)
    `-- admin/    (login.html, dashboard.html, movie_form.html)
```

## Routes

| Method and path | Purpose | Login required |
|---|---|---|
| GET `/` | Search and paginated movie list (`q`, `page` query parameters) | No |
| GET `/movies/{movie_id}` | Movie detail with ratings and tags | No |
| GET, POST `/admin/login` | Admin login | No |
| GET `/admin/logout` | Clear the session | Yes |
| GET `/admin/dashboard` | Admin movie list | Yes |
| GET, POST `/admin/movies/new` | Create a movie | Yes |
| GET, POST `/admin/movies/{id}/edit` | Edit a movie | Yes |
| POST `/admin/movies/{id}/delete` | Delete a movie | Yes |

## Getting started

### 1. Prerequisites
- Python 3.11 or newer
- PostgreSQL (tested with PostgreSQL 18)
- The MovieLens dataset (see "Dataset" below)

### 2. Create the environment and install dependencies

```bash
conda create -n movielens_webapp python=3.11
conda activate movielens_webapp
pip install -r requirements.txt
```

A standard `python -m venv` environment works equally well.

### 3. Prepare the database

Create a PostgreSQL database named `movielens` and load the MovieLens CSV files into four tables: `movies`, `ratings`, `tags` and `links`.

The application reads these columns:

| Table | Columns used by the application |
|---|---|
| `movies` | `movie_id` (primary key), `title`, `genres` |
| `ratings` | `user_id`, `movie_id`, `rating` |
| `tags` | `user_id`, `movie_id`, `tag` |
| `links` | `movie_id` |

`ratings`, `tags` and `links` are expected to reference `movies.movie_id` through foreign keys. The delete-protection behaviour of the admin panel depends on those foreign keys being present.

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in every value:

1. `DB_*` - your PostgreSQL connection details.
2. `ADMIN_PASSWORD_HASH` - run `python generate_password_hash.py`, type the password you want, and paste the printed hash.
3. `SESSION_SECRET_KEY` - generate one with:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

### 5. Run

```bash
uvicorn main:app --reload
```

Open http://127.0.0.1:8000 for the public site and http://127.0.0.1:8000/admin/login for the admin panel.

## Testing

The application was verified manually against a 15-step checklist: homepage, search, pagination, movie detail, the 404 page, an invalid path parameter, unauthenticated admin access, a wrong login, a correct login, adding a movie, a duplicate `movie_id`, editing a movie, deleting an unreferenced movie, deleting a referenced movie, and logout.

## Error handling summary

| Situation | Status | Behaviour |
|---|---|---|
| Movie ID does not exist | 404 | Custom not-found page |
| Non-integer movie ID in the URL | 422 | Rejected by FastAPI validation before the route runs |
| Duplicate `movie_id` on create | 409 | Form re-shown with a clear message |
| Deleting a movie that is still referenced | 409 | Dashboard re-shown with a message |
| Admin page requested while logged out | 303 | Redirect to `/admin/login` |

## Roadmap

- Connection pooling with `psycopg2.pool.SimpleConnectionPool`.
- Real user accounts (sign-up and login) separate from the single admin account.
- URL-encode the search term when building pagination links.
- Per-user watchlists or "my ratings" once user accounts exist.

## Dataset

This project uses the MovieLens dataset published by GroupLens Research at the University of Minnesota. The dataset is **not included** in this repository because its licence does not permit redistribution. Download it from https://grouplens.org/datasets/movielens/ and load it into PostgreSQL as described above.

Citation: F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4, Article 19. https://doi.org/10.1145/2827872

## Licence

The source code in this repository is released under the MIT Licence (see `LICENSE`). The MovieLens data is subject to the GroupLens terms of use and is not covered by this licence.

## Author

Jay Khandelwal
