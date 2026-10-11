"""
the only file in this project allowed to contain SQL.

Every function here opens its own connection, does one job, 
and close that connection before returningthis keeps every other fie in the project completely 
unaware of SQL syntax.
"""

import os
import psycopg2 
import psycopg2.extras 
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """ 
    Opens and returns a brand new connection to PostgreSql, using the values stored in .env.
    
    Reasoning for opening a fresh connection every time this function
    is called, rather than opening one single connection when the
    application starts and reusing it forever: a web application can
    receive several requests from different visitors at the exact
    same moment. If every request shared one single connection, two
    visitors' queries could interfere with each other's in-progress
    work. Opening a new connection per request keeps every visitor's
    work fully isolated from every other visitor's. The documented
    next step for a real production system is connection pooling
    (psycopg2's SimpleConnectionPool), which reuses a small set of
    already-open connections instead of opening a fresh one every
    single time — faster, but more complex, and deliberately left
    out of this project's current scope.

    """
    connection = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        cursor_factory=psycopg2.extras.RealDictCursor,  
        
        # by default, psycopg2 returns each db row as a plain tuple, 
        # and if column order in the table ever changed, every one of the indexing becomes wrong w/o any error being raised.
        # RealDictCursor returns each row as a dictionary, so we access the exact same valy=ue by name.
    )
    
    return connection

# Fetching movies for the public list and admin dashboard

def fetch_movies(search, limit, offset):
        """ 
        Returns one page of movies, each with its average rating and total 
        number of ratings attached, optionally filtered by a search term typed into the title.
        """
        connection = get_connection()
        cursor = connection.cursor()

        if search:
            cursor.execute(
                """  SELECT 
                m.movie_id, m.title, m.genres,
                ROUND(AVG(r.rating),4) AS avg_rating, 
                COALESCE(COUNT(r.rating),0) AS rating_count 
                FROM movies m
                LEFT JOIN ratings r ON m.movie_id = r.movie_id
                WHERE m.title ILIKE %s      
                GROUP BY m.movie_id, m.title, m.genres
                ORDER BY m.movie_id
                LIMIT %s OFFSET %s
                """,
                (f"%{search}%", limit, offset)

            )
        else:
            cursor.execute(
                """  SELECT 
                m.movie_id, m.title, m.genres,
                ROUND(AVG(r.rating),4) AS avg_rating,
                COALESCE(COUNT(r.rating),0) AS rating_count 
                FROM movies m
                LEFT JOIN ratings r ON m.movie_id = r.movie_id
                GROUP BY m.movie_id, m.title, m.genres
                ORDER BY m.movie_id 
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
        rows = cursor.fetchall()    # retrieves every matching row as a list
        cursor.close()
        connection.close()
        return rows

def count_movies(search):
    """ 
    Returns the total number of movies matching the search term or all movies, if search is empty, 
    used to calculate how many pages of results exist. 23 movies, 10 movies per page, total 3(2.3)pages not 2. 
    """ 
    connection = get_connection()
    cursor = connection.cursor()
    if search:
            cursor.execute (
            "SELECT COUNT(*) AS total FROM movies WHERE title ILIKE %s", (f"%{search}%",) # ILIKE is postgres case-insensitive version
            )
    else:
            cursor.execute (
            "SELECT COUNT(*) AS total FROM movies"
            )
            
    result = cursor.fetchone()      # retrives exactly one row
    cursor.close()
    connection.close()
    return result ["total"]
    
         
# %s: placeholder syntax for a parameterized query.
# Using this eliminates the entire category of attack - SQL IJECTION where anyone could type anything 
# like Drop table or Update into a search box and have it executed as an actual command instead of search term.


# Fetching one movie's full detail
# (movie_id,  ) = it is a tuple containing one item. (movie_id) is just the value wrapped in ordinary parentheses.

def fetch_movie_by_id(movie_id):
    """
    Returns one movie's core details, or None if no movie exists
    with that id. Returning None here, rather than raising an
    error, lets the calling route decide how to handle a missing
    movie (in this project, by showing a proper 404 page).
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT movie_id, title, genres FROM movies WHERE movie_id = %s", (movie_id,))
    row = cursor.fetchone()
    cursor.close()
    connection.close()
    return row


def fetch_ratings_for_movie(movie_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT user_id, rating FROM ratings WHERE movie_id = %s ORDER BY user_id",
        (movie_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows


def fetch_tags_for_movie(movie_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT user_id, tag FROM tags WHERE movie_id = %s ORDER BY user_id",
        (movie_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows

# Checking existence, before insert

# SELECT 1, here, does not ask for any actual column - the query only cares whether any row matched at all.
# So, asking the databsae to also gather and return a column is waste of time.

def movie_id_exists(movie_id):
    """
    Returns True if a movie with this id already exists, False
    otherwise. Used before inserting a new movie, so the admin
    gets a clear "already exists" message instead of a raw
    database error.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM movies WHERE movie_id = %s", (movie_id,))
    exists = cursor.fetchone() is not None      # It retireves exactly one row. Here, it convert "did any row come back?" to plain True/False
    cursor.close()
    connection.close()
    return exists

# Insertin, Updating and Deleting

# connection.commit()- opening a connection with psycopg2 starts an implicit trxn, and none of our
# [Insert, Update, Delete] become permanent in the database until .COMMIT() IS CALLED.

# Update query never updates primary key column - stays fixed.

# try / finally: in DELETE query, it is the one place where a function's shape differ from the simple pattern used everywhere ("OPEN, EXECUTE, COMMIT, CLOSE.").
# In this one [TRY/FINALLY], query is capable of raising an exception under a normal, expected condition like DELETING A MOVIE THAT STILL HAS RATINGS.
# AND, the only way to guarantee the connection still closes properly whether that exception happens or not.

def insert_movie(movie_id, title, genres):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO movies (movie_id, title, genres) VALUES (%s, %s, %s)",
        (movie_id, title, genres),
    )
    connection.commit()
    cursor.close()
    connection.close()


def update_movie(movie_id, title, genres):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE movies SET title = %s, genres = %s WHERE movie_id = %s",
        (title, genres, movie_id),
    )
    connection.commit()
    cursor.close()
    connection.close()


def delete_movie(movie_id):
    """
    Deletes a movie. If ratings, tags, or links still reference this
    movie_id, PostgreSQL raises a ForeignKeyViolation, since no
    ON DELETE rule was set on those foreign keys (the default
    behavior is to block the delete rather than silently allow it).

    Reasoning for the try/finally here specifically: if execute()
    raises that exception, we still must not skip closing the
    cursor and connection — otherwise this function would leak a
    connection every single time someone tries to delete a
    referenced movie, which, over time, could exhaust the
    database's connection limit. Finally guarantees the cleanup
    code runs whether or not an exception occurred, while still
    allowing the exception itself to continue upward to whichever
    code called this function - admin.py, so it can be handled
    there with a proper, user-facing message.
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM movies WHERE movie_id = %s", (movie_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# to check whether the file is free of syntax error w/o actually executing anything inside it
# python -m py_compile <database.py> where py_compile checks the file structure w/o running any of the code