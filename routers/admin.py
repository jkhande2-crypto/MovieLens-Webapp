
# WHAT? 
# every route that manages the movies table from behind a log-in, dashboard and add/edit/delete for individual movie.

# WHY?
# it covers full CRUD - Create, Read, Update, Delete + the log-in flow that guards all of it.
# every route except the log-in and log-out carries the same login-check dependency.

"""
routers/admin.py — every route here manages the movies table, and
every route except the login page itself requires an active session.
"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
import psycopg2

import database
from auth import verify_admin_credentials, require_login      # import both functions- to check a submitted log-in and to guard every protected file.
from templates_config import templates

router = APIRouter(prefix="/admin")     # created a grouped route handler named ADMIN where every URL path will automatically starts with that.

# @router.route()/ @router.get() - used to separate the application into smaller, manageable sub-modules rather than putting all URL routes inside a single main application file
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request=request, name="admin/login.html", context={"error": None})


@router.post("/login", response_class=HTMLResponse)
# FORM(...) tells FastAPI to read this value from the submitted HTML form's body specifically. 
# (...) - the field is required- no username and password field will be empty other gives error.
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    
    # one correct log-in, one single key
    if verify_admin_credentials(username, password):
        request.session["logged_in"] = True
        return RedirectResponse(url="/admin/dashboard", status_code=303) # send the browser onwars to the dashboard after a successful log-in.

    return templates.TemplateResponse(
        request=request,
        name="admin/login.html",
        context={"error": "Incorrect username or password."},
        status_code=401, # meaning unauthorized
    )


@router.get("/logout")
def logout(request: Request):
    request.session.clear()     # empties the session dictionary. 
    # sessionMiddlware reflects this by overwriting the browser's cookie on the way out.
    # log-in state lives entirely in this one signed cookie never in the database.

    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
# _ :None = Depends(require_login) - '_' as a variable name is a python convention means "THIS VALUE IS REQUIRED TO BE HERE, BUT I AM NEVER GOING TO ACTUALLY USE IT INSIDE THE FUNCTION."
# the real job is the side effect of raising a redirect if the checks fails not producing a value from the route needs to read.
def dashboard(request: Request, _: None = Depends(require_login)):
    movies = database.fetch_movies(search=None, limit=1000, offset=0)
    return templates.TemplateResponse(request=request, name="admin/dashboard.html", context={"movies": movies})


@router.get("/movies/new", response_class=HTMLResponse)
def new_movie_form(request: Request, _: None = Depends(require_login)):
    return templates.TemplateResponse(
        request=request,
        name="admin/movie_form.html",
        context={"movie": None, "error": None, "mode": "create"},
    )


@router.post("/movies/new", response_class=HTMLResponse)
def new_movie_submit(
    request: Request,
    movie_id: int = Form(...),
    title: str = Form(...),
    genres: str = Form(""),   # defaults to an empty string rather than being required- matching the real db columnallowing movies to have no genres listed at all.
    _: None = Depends(require_login),
):
    if database.movie_id_exists(movie_id):  # is checked before the insert
        return templates.TemplateResponse(
            request=request,
            name="admin/movie_form.html",
            context={
                "movie": {"movie_id": movie_id, "title": title, "genres": genres},
                "error": f"movie_id {movie_id} already exists. Choose a different id, or edit the existing movie instead.",
                "mode": "create",
            },
            status_code=409,
        )

    database.insert_movie(movie_id, title, genres)
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.get("/movies/{movie_id}/edit", response_class=HTMLResponse)
def edit_movie_form(request: Request, movie_id: int, _: None = Depends(require_login)):
    movie = database.fetch_movie_by_id(movie_id)
    if movie is None:
        return templates.TemplateResponse(
            request=request,
            name="admin/dashboard.html",
            context={"movies": database.fetch_movies(None, 1000, 0), "flash": f"No movie with id {movie_id}."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request=request,
        name="admin/movie_form.html",
        context={"movie": movie, "error": None, "mode": "edit"},
    )


@router.post("/movies/{movie_id}/edit", response_class=HTMLResponse)
def edit_movie_submit(
    request: Request,
    movie_id: int,      # edit routes never accept movie_id from the submitted form at all-only from the URL path which is fixed the moment the edit page was opened.
    title: str = Form(...),
    genres: str = Form(""),
    _: None = Depends(require_login),
):
    database.update_movie(movie_id, title, genres)
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.post("/movies/{movie_id}/delete")
def delete_movie_submit(request: Request, movie_id: int, _: None = Depends(require_login)):
    try:
        database.delete_movie(movie_id)
    except psycopg2.errors.ForeignKeyViolation:
        movies = database.fetch_movies(None, 1000, 0)
        return templates.TemplateResponse(
            request=request,
            name="admin/dashboard.html",
            context={
                "movies": movies,
                "flash": f"Cannot delete movie {movie_id} — it still has ratings, tags, or links pointing to it.",
            },
            status_code=409,
        )
    return RedirectResponse(url="/admin/dashboard", status_code=303)