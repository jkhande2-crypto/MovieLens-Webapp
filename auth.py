# the only file responsible for the admin login logic.
# checking whether a entered user name and password are correct and providing a reusable check that other files use to guard protected pages.

# WHY THIS FILE NOT IN ANY OTHER FILE?
# keeping it in one place means there is exactly one function that defines whether the log-in is correct or not. and every other file simply asks that one function rather than reimplementing the check itself.
# If we have written this with other lines of codes and say, if we have to change the hashing algo later, we have to go through with all those lines of codes. by doing this, it saves time and make our code error free.

""" 
the only file in this project responsible for authentication logic: checking login credentials,
and guarding routes that require an active admin session. """

import os
from fastapi import Request, HTTPException
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")      
 # hashing tool used in generate_password_hash.py. 
 # tool that creates a hash and tool that later checks a pssword against that hash must use the same algo and settings. 

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH") 
# reads directly from .env 


# username can be compared and don't need hashing.
# Password is never compared. Takes the typed plain password, hashes it internally using the same way that created stored hash.
# Checks whether two hashes match.

def verify_admin_credentials(username, password):
    """ Returns True only if both the username and password matches exactly and the submitted password,
    once hashed, matches the stored hash."""
    if username != ADMIN_USERNAME:
        return False
    return pwd_context.verify(password, ADMIN_PASSWORD_HASH)


# A function that's what FastAPI calls a dependency.
# a function FastAPI runs automatically before the route's own code and can inspect the request and either let the route proceed or intervene by raising an exception that redirects the browser away entirely
def require_login(request: Request):
    """
    A FastAPI dependency. Any route that includes this in its
    signature will automatically run this check first, before the
    route's own code executes at all.

    Reasoning for raising HTTPException with status_code=303 and a
    Location header, rather than simply returning some value: this
    is how FastAPI performs a redirect from inside a dependency.
    Raising this exception immediately stops the original route
    from running any further, and instead sends the browser a 303
    response pointing it to the login page. From the visitor's
    perspective, this looks identical to a normal redirect — they
    are simply sent to /admin/login, with no indication that a
    dependency, rather than the route itself, made that decision.
    """
    if not request.session.get("logged_in"):        # reads avalue out of the signed session cookie. if this kei is missing or False, the visitor is treated as not logged in.
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
        
        
        # code 303 means "SEE OTHER" - the std HTTP stauts for redirecting a browser to a different page after a request.
        # LOCATION header tells the browser exactly where to go. Raising it directly from insida a dependency rather than the route iself,
        # is what makes it possible to protect many different routes with one single line

