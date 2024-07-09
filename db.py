import bson

from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId


def get_db():
    db = getattr(g, "_database", None)

    if db is None:
        mongo = PyMongo(current_app)
        db = g._database = mongo.db

    return db

db = LocalProxy(get_db)

def create_indexes():
    db.tickets.create_index ({'ticketID' : 1, 'userID' : 1, 'category' : 1, 'description' : 1})

def init_app(app):
    with app.app_context():
        create_indexes()

## Ticket Fucntions
def new_ticket(ticketID, userID, category, description):
    ticket_doc = {'ticketID' : ticketID, 'userID' : userID, 'category' : category, 'description' : description}
    return db.tickets.insert_one(ticket_doc)

def get_ticket_count():
    return db.tickets.count_documents({})

## Account Functions