
""" 
templates_config.py -  to create one-single, shared jinja template engine, imported by both
routers/public.py and routers/admin.py.
Keeping this in its own small files, separate from main.py, avoids a circular import: 
both routers files need this object and main.py needs to import both router files,
so this object cannot live inside main.py itself w/o creating circular loop.
"""

# FastAPI's own built-in wrapper around the Jinja@ lib. 
from fastapi.templating import Jinja2Templates


# creates one such such obj and tells it that every template file it will ever be asked to render lives insaide a folder named templates
templates = Jinja2Templates(directory = "templates")
