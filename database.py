import sqlite3
from flask import g


def connect_to_database():
   sql = sqlite3.connect("/home/dion/chat/coffee.db")
   sql.row_factory = sqlite3.Row
   return sql


def get_database():
    if not hasattr(g, "coffee_db"):

        g.coffee_db = connect_to_database()

    return g.coffee_db



