
"""
main.py — the application's entry point. This is the one file
Uvicorn is actually told to run (uvicorn main:app --reload).
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from routers import public, admin

load_dotenv()

# creates oe central application object. Every route from both routers will be attched to this single object - nothing runs w/o it existing first.
app = FastAPI(title="MovieLens Data Pipeline — Web UI & Admin Panel")

#MiddleWare is code that wraps around every request and every response passing through the application regardless of which specific route ends up handling it.
# Mechanically: on every outgoing response, SessionMiddleware takes whatever is currently stored in request.session, serializes it, and cryptographically signs it using secret_key, writing the result into a cookie sent back to the browser. On every incoming request, it reads that cookie back, verifies the signature, and repopulates request.session with its contents — or leaves it empty if the signature is missing, altered, or invalid.
# 
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")    # it tells uvicorn to serve files directly from the STATIC folder on disk, byte-for-byte, whenever a URL under '/STATIC/...' is requested

# include_router() copies every route already declared inside a given APIRouter object into the main app object.
app.include_router(public.router)
app.include_router(admin.router)