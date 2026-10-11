
"""
routers/public.py — every page a regular visitor can reach, with no
login required anywhere in this file.
While admin pages need a session check on almost every single one. 
Keeping them in separate files means you can look at public.py and immediately know that nothing in it is protected, without having to check each route individually — the file itself communicates that guarantee.
"""

import math
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse

# To call a function already written and tested inside database.py. And renders pages using the one shared templates object from template_config.py.

import database
from templates_config import templates

router = APIRouter()        # creates a small, self-contained collection of routes

PAGE_SIZE = 10      # how many movie shows per page

# q: str | None = Query(default=None) = this is FastAPI reading a value out of the URL's query string.
# str | None = tells python this value is either text or entirely absent.
# Query(default=None) = tells fastAPI it is optional and if the visitor has not searched for anything, 'q' simply comes through as NONE.
# page:int = Query(default=1, ge=1) = reads a 'page' number from the URL, defaulting 1 if absent. 'ge=1' stands for ">= 1" - THIS IS FATSAPI PERFORMING AUTOMATIC INPUT VALIDATION.

@router.get("/", response_class=HTMLResponse)
def home(request: Request, q: str | None = Query(default=None), page: int = Query(default=1, ge=1)):
    offset = (page - 1) * PAGE_SIZE     #arithmetic converting user-facing page number into row-skipping number 'database.fetch_movies' actually needs. 

    movies = database.fetch_movies(search=q, limit=PAGE_SIZE, offset=offset)
    total_movies = database.count_movies(search=q)

    total_pages = max(1, math.ceil(total_movies / PAGE_SIZE))       # math.ceil rounds a division result upward. Wrapping the whole thing in 'max(....)' guarantees the reuslt is never 0 - search with 0 results should still report 'pg 1 of 1'.
    return templates.TemplateResponse(
        request=request,
        name="public/home.html",
        context={"movies": movies, "search": q or "", "page": page, "total_pages": total_pages},
    )


@router.get("/movies/{movie_id}", response_class=HTMLResponse)

# movie: int - it is a path parameter and the type 'int' here does the real work. 
# if a user visits '/movies/abc', FastAPI automatically rejects the request with 402 error before 'movie_details's ' own code runs at all since 'abc' cannot be converted into integer.

def movie_detail(request: Request, movie_id: int):      
    movie = database.fetch_movie_by_id(movie_id)
    if movie is None:       # this syntax followed by rendering 'not_found.html with 'status_code =404'- handling 'fetch_movie_by_id' documented "RETURNS NONE ON A MISS" from database.py and turns it into 404-styled page.
        return templates.TemplateResponse(
            request=request, name="public/not_found.html",
            context={"movie_id": movie_id}, status_code=404,
        )
    ratings = database.fetch_ratings_for_movie(movie_id)
    tags = database.fetch_tags_for_movie(movie_id)
    return templates.TemplateResponse(
        request=request, name="public/movie_detail.html",
        context={"movie": movie, "ratings": ratings, "tags": tags},
    )