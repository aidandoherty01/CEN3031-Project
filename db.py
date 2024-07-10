import bson
import datetime
import string

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

def create_collections():
    if 'tickets' not in db.list_collection_names():
        db.create_collection('tickets')
    if 'accounts' not in db.list_collection_names():
        db.create_collection('accounts')

def create_indexes():
    db.tickets.create_index ({'ticketID' : 1, 'userID' : 1, 'category' : 1, 'description' : 1, 'assignedEmpID' : 1, 'status' : 1, 'eta' : 1, 'startTime' : 1}) # status can either be: 'unassigned' 'assigned' or 'closed'
    db.accounts.create_index ({'accID' : 1,'username' : 1, 'password' : 1, 'fName' : 1, 'lName' : 1})

def init_app(app):
    with app.app_context():
        create_collections()
        create_indexes()

## Ticket Fucntions
def new_ticket(ticketID, userID, category, description):
    ticket_doc = {'ticketID' : int(ticketID), 'userID' : int(userID), 'category' : category, 'description' : description, 'status' : "unassigned"}
    return db.tickets.insert_one(ticket_doc)

def get_ticket_count():
    return db.tickets.count_documents({})

def get_ticket_by_id(ticketID):
    return db.tickets.find_one({'ticketID' : int(ticketID)}) # returns the ticket associated with the ID

def get_tickets_by_acc(accID): # returns a cursor that points to the first element in the list of tickets associated with a given account
    tickets = db.tickets.find({'userID' : int(accID)})
    if (len(list(tickets)) == 0):
        tickets = db.tickets.find({'assignedEmpID' : int(accID)})
    return tickets
     
def assign_ticket_emp(ticketID, empID):
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'assignedEmpID' : int(empID), 'status' : "assigned"}})
    return response

def assign_ticket_eta(ticketID, eta):
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)},  {'$set' : {'eta' : string(eta)}})
    return response

def assign_ticket_start_time(ticketID, startTime):
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'startTime' : string(startTime)}})

def close_ticket(ticketID):
    print(ticketID)
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'status' : "closed"}})

## Account Functions