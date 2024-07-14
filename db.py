import bson
import string

from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import time, timedelta, date, datetime



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
    if 'schedules' not in db.list_collection_names():
        db.create_collection('schedules')

def create_indexes():
    db.tickets.create_index ({'ticketID' : 1, 'userID' : 1, 'category' : 1, 'description' : 1, 'assignedEmpID' : 1, 'status' : 1, 'eta' : 1, 'startTime' : 1}) # status can either be: 'unassigned' 'assigned' or 'closed'
    db.accounts.create_index ({'accID' : 1,'username' : 1, 'password' : 1, 'fName' : 1, 'lName' : 1, 'type' : 1}) # type can be 0,1,2; 0 = user, 1 = employee, 2 = admin
    db.schedules.create_index ({'accID' : 1, 'timeSlots' : 1})

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

def get_tickets_by_account(accID): # returns a cursor that points to the first element in the list of tickets associated with a given account
    tickets = db.tickets.find({'userID' : int(accID)})

    return tickets

def get_active_tickets(accID):
    tickets = db.tickets.find({'userID' : int(accID), 'status':  {"$in":["unassigned","assigned"]}})  
    return tickets

def get_unassigned_tickets():
    tickets = db.tickets.find({'status' : "unassigned"})
    return tickets

def get_ticket_eta(ticket): # returns ticket eta as a timedelta obj
    etaStr = ticket.get('eta').split(':')
    eta = timedelta(hours=int(etaStr[0]), minutes=int(etaStr[1]))
    return eta

def get_ticket_finish_time(ticket):
    eta = get_ticket_eta(ticket)
    startTime = ticket.get('startTime')
    finishTime = startTime + eta
    return finishTime

def assign_ticket_emp(ticketID, empID):
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'assignedEmpID' : int(empID), 'status' : "assigned"}})
    return response

def assign_ticket_eta(ticketID, eta):
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)},  {'$set' : {'eta' : eta}})
    return response

def assign_ticket_start_time(ticketID, startTime):
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'startTime' : startTime}})

def close_ticket(ticketID):
    print(ticketID)
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'status' : "closed"}})

## Account Functions
def new_account(accID, username, password, fName, lName):
    acc_doc = {'accID' : accID, 'username' : username, 'password' : password, 'fName' : fName, 'lName' : lName, 'type' : 0}
    return db.accounts.insert_one(acc_doc)

def get_account_count():
    return db.accounts.count_documents({})

def check_account(username, password):
    acc_exist = db.accounts.find_one({'username': username, 'password': password})
    return acc_exist

def get_emp_accounts():
    return db.accounts.find({'type' : 1})

def get_account(accID):
    acc = db.accounts.find_one({'accID': accID})
    return acc
  
def get_accounts():
    return db.accounts.find()

## Schedule Fucntions
def new_schedule(accID, timeSlots): # takes in array of strings and an accID to create a new schedule
    schedule_doc = {'accID' : accID, 'timeSlots' : timeSlots} # format of array: [0-7 for sun-sat][0 for starttimes 1 for durations][n starttime/durations]
    return db.schedules.insert_one(schedule_doc)

def get_schedule(accID):  # returns an array of timedelta objects, NOT STRINGS!!!
    scheduleJSON = db.schedules.find_one({'accID' : accID}).get('timeSlots')
    scheduleOut = [[0] * 2 for _ in range(7)]

    for i in range(7):
        for j in range(2):
            scheduleOut[i][j] = []

    for i in range(7):
        for j in range(len(scheduleJSON[i][0])):
            startStr = scheduleJSON[i][0][j].split(':')
            durStr = scheduleJSON[i][1][j].split(':')

            startTime = timedelta(hours=int(startStr[0]), minutes=int(startStr[1]))

            durTime = timedelta(hours=int(durStr[0]), minutes=int(durStr[1]))

            scheduleOut[i][0].append(startTime)
            scheduleOut[i][1].append(durTime)
            #print(str(scheduleOut[i][0][j]) + " " + str(scheduleOut[i][1][j]))
            #print(str(i) + " " + str(j) + ": " + str(scheduleOut[i][0][j]) + "-" + str(scheduleOut[i][0][j] + scheduleOut[i][1][j]))

    return scheduleOut

def date_to_weekday(date): # gets the int value of the weekday of a given date (0 = sun, 1 = mon, ...)
    
    switch = {
        "Sunday": 0,
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6,
    }

    return switch.get(date.strftime("%A"))

def check_intersect(start1, start2, eta1, eta2): #checks if a given pair of starts and etas intersect
    if (start1 < start2):
        if ((start1 + eta1) > start2):
            return True
        else:
            return False
    else:
        if ((start2 + eta2) > start1):
            return True
        else:
            return False
        
def schedule_start_to_datetime(relativeDate, scheduleStart): # converts the starttime in the schedule to a datetime as tho the starttime was on the same day as the relativeDate, as the schedule stores its start times as durations not datetimes, as datetimes cannot be made to generically refer to any day
    out = datetime(relativeDate.year, relativeDate.month, relativeDate.day) + scheduleStart
    return out

def get_soonest_fit(accID, ticketID): # finds the soonest start time that a ticket can be fit into a given employees shechdule
    schedule = get_schedule(accID)
    ticket = get_ticket_by_id(ticketID)
    ticketEta = get_ticket_eta(ticket)
    tickets = list(get_tickets_by_acc(accID))

    currentDate = datetime.now()
    currentDay = date_to_weekday(currentDate)

    startTime = currentDate # holds the tentative start time and date of the ticket, will be incremented as times are checked
    startDay = currentDay # hold the same as above but the int day of the week

    found = False
    loops = 0 # prevents looping forever when the ticket does not fit in any time slot

    while(found == False or loops >= 100):
        if (startDay == 7): # reset start day to 0 when end of a week is reached
            startDay = 0
        
        for j in range(len(schedule[startDay][0])): # loops thru all the time slots on the given day
            startTime = schedule_start_to_datetime(startTime, schedule[startDay][0][j]) # sets the current considered start time to the start of the current considered timeslot
            if (startTime >= currentDate): # checks that the currently considered start time is after the current time
                while ((schedule_start_to_datetime(startTime, schedule[startDay][0][j]) + schedule[startDay][1][j]) >= startTime + ticketEta): # loops thru the code until the tickets finish time would be after the time slots finish time
                        passed = 0 # will count the amount of tickets that the current ticket did not intersect with
                        for i in range(len(tickets)): # loops thru all the tickets already assigned to the employee
                            if (check_intersect(startTime, tickets[i].get('startTime'), ticketEta, get_ticket_eta(tickets[i])) == False): # checks if the currently considered start time would cause the ticket to intersect with any of the employees other tickets
                                passed += 1
                            else:
                                startTime = startTime + get_ticket_eta(tickets[i]) # sets the considered start time to just after the ticket it intersected with
                                if ((schedule_start_to_datetime(startTime, schedule[startDay][0][j]) + schedule[startDay][1][j]) >= startTime + ticketEta): # checks if moving up the start time caused the ticket to go out of bound of the time slot
                                    i = len(tickets) # if it did, stop checking the rest of tickets and move onto next timeslot
                                else:
                                    passed = 0
                                    i = 0 # if the ticket was able to be moved later in the time slot, check it against all tickets again with the new time 
                                    # this recheck can be removed if the tickets are sorted by assending start time, may implement that if this function proves to be too slow
                                    # if it is sorted, just remove both lines of code here and replace with "passed += 1"
                                    
                            
                        if (passed == len(tickets)): 
                            return startTime # if it intersected with no tickets, return this start time

        startDay += 1
        startTime = startTime + timedelta(days=1) # moves start time to the next day so that the relative starttime can be set properly

        loops += 1

    return datetime.max # returns max time to show that cannot be fit into schedule
                            