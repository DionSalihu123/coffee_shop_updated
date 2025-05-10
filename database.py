import sqlite3
from flask import g

def connect_to_database():
    sql = sqlite3.connect("/home/dion/chat/coffe-shop/coffee.db")
    sql.row_factory = sqlite3.Row
    return sql

def get_database():
    if not hasattr(g, "coffee_db"):
        g.coffee_db = connect_to_database()
    return g.coffee_db

def close_database(error=None):
    """Closes the database connection at the end of the request."""
    db = getattr(g, 'coffee_db', None)
    if db is not None:
        db.close()




