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
    if 'ticketChats' not in db.list_collection_names():
        db.create_collection('ticketChats')
    if 'categories' not in db.list_collection_names():
        db.create_collection('categories')

def create_indexes():
    db.tickets.create_index ({'ticketID' : 1, 'userID' : 1, 'category' : 1, 'description' : 1, 'assignedEmpID' : 1, 'status' : 1, 'eta' : 1, 'startTime' : 1, 'hoursWorked' : 1}) # status can either be: 'unassigned' 'assigned' or 'closed'
    db.accounts.create_index ({'accID' : 1,'username' : 1, 'password' : 1, 'fName' : 1, 'lName' : 1, 'type' : 1}) # type can be 0,1,2; 0 = user, 1 = employee, 2 = admin
    db.schedules.create_index ({'accID' : 1, 'timeSlots' : 1})
    db.ticketChats.create_index({'ticketID' : 1, 'userID' : 1, 'empID' : 1, 'msgs' : 1}) # msgs is a 2D array, of size [n] * [3]. n is the msg in chronological order, [n][0] = msg contents, [n][1] = timestamp, [n][2] = accID that sent msg
    db.categories.create_index ({'category' : 1})

def init_app(app):
    with app.app_context():
        create_collections()
        create_indexes()
        # create admin account on initialization
        if(check_username_free('admin')):
            new_account(0, 'admin', 'password', 'John', 'Doe', 2)
            # accID, username, password, fName, lName, type

        # populate categories with default values
        if (db.categories.count_documents({}) == 0):
            db.categories.insert_one({'category' : "Software Problem"})
            db.categories.insert_one({'category' : "Hardware Problem"})

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

def assign_ticket_emp(ticketID, accID): # On successful assignment, returns 0, else returns 1
    if not get_account(accID):
        return 1
    flag = get_ticket_by_id(ticketID).get('assignedEmpID')  # Either None or Currently assigned emp
    if flag == accID:   # reassigning to same account
        return 1
    db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'assignedEmpID' : int(accID), 'status' : "assigned"}})
    if not flag:    # If flag is None ==> First time ticket is being assigned
        new_ticket_chat(ticketID, db.tickets.find_one({'ticketID' : int(ticketID)}).get('userID'), int(accID))
    else:   # Ticket Reassignment
        db.ticketChats.update_many({'empID' : flag}, {'$set' : {'empID' : accID}})
    return 0

def assign_ticket_eta(ticketID, eta):
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)},  {'$set' : {'eta' : eta}})
    return response

def assign_ticket_start_time(ticketID, startTime):
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'startTime' : startTime}})

def close_ticket(ticketID):
    # print(ticketID)
    response = db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'status' : "closed"}})

def update_hours_worked(ticketID, hours):
    return db.tickets.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'hoursWorked' : int(hours)}})

def get_ticket_ids_by_account(accID):
    return db.tickets.find({'assignedEmpID' : accID}, {'ticketID' : 1})

## Account Functions
def hash_password(passPlain): # hashes passwords using division by prime method
    passASCII = list(passPlain.encode('ascii')) # converts input to array of ascii values
    temp = ""
    for i in passASCII: # puts all these ascii values into one string
        temp += str(i)

    passInt = int(temp) # convert string to int

    passHash = str(int(passInt) % 137077) # hash int, store as string

    return passHash

def new_account(accID, username, password, fName, lName, type):
    passHash = hash_password(password)
    acc_doc = {'accID' : accID, 'username' : username, 'password' : passHash, 'fName' : fName, 'lName' : lName, 'type' : int(type)}
    return db.accounts.insert_one(acc_doc)

def get_account_count():
    return db.accounts.count_documents({})

def check_account(username, password):
    acc_exist = db.accounts.find_one({'username': username, 'password': hash_password(password)})
    return acc_exist

def check_username_free(username):
    acc = list(db.accounts.find({'username' : username}))
    if (len(acc) == 0):
        return True
    else:
        return False

def get_account_by_username(username):
    return db.accounts.find_one({'username' : username})

def get_account(accID):
    acc = db.accounts.find_one({'accID' : accID})
    return acc
  
def get_accounts():
    return db.accounts.find()

def get_emp_accounts():
    return db.accounts.find({'type' : 1})

def get_emp_ids():
    return db.accounts.find({'type' : 1}, {'accID' : 1})

def delete_account(accID):
    t = get_account(accID)  # check that the account exists
    if t:
        t = t.get('type')
        if t != 0:  # check the account is an employee (or admin)
            delete_acc_from_chats(accID)
            db.accounts.delete_one({'accID' : accID})
            db.schedules.delete_one({'accID' : accID})
            if get_tickets_by_acc(accID):
                db.tickets.update_many({'assignedEmpID' : accID},
                                        {'$set' : {'status' : 'unassigned'}})
        return 0
    else:
        return 1

def get_new_ID(): # returns an int = the lowest avaliable acc id
    accounts = list(db.accounts.find().sort('accID')) # gets all the accounts, sorted by ID
    
    if (len(accounts) == 0):
        return 1
    elif (len(accounts) == 1):
        return (accounts[0].get('accID') + 1)
    else:
        for i in range(1, len(accounts)):
            if ((accounts[i].get('accID') - 1) != (accounts[i-1].get('accID'))): # checks if account i's id is not one greater than the previous account
                return (accounts[i].get('accID') - 1)
        
        return (len(accounts) + 1) # if there were no gaps then return the size + 1 as new acc
    
def update_account(accID, username, password, fName, lName):
    if not check_username_free(username):
        # Username is not free, check if this username's accID == this accID
        temp = get_account_by_username(username)
        if(temp.get('accID') != accID):
            return 0    # Can't have duplicate usernames on different ids
    hashed = hash_password(password)
    response = db.accounts.find_one_and_update(
        { 'accID' : accID },
        { '$set' : { 'username' : username, 'password' : hashed , 'fName' : fName, 'lName' : lName } }
    )
    return response

## Schedule Fucntions
def new_schedule(accID, timeSlots): # takes in array of strings and an accID to create a new schedule
    schedule_doc = {'accID' : accID, 'timeSlots' : timeSlots} # format of array: [0-7 for sun-sat][0 for starttimes 1 for durations][n starttime/durations]
    return db.schedules.insert_one(schedule_doc)

def default_schedule(accID):    # Generates and stores a default 9-5
    default_startTime = "9:00:00"
    default_duration = "8:00:00"
    schedule = [[0] * 2 for _ in range(7)]  # initialize new schedule
    for i in range(7):
            for j in range(2):
                schedule[i][j] = []
    for i in range(7):
            schedule[i][0].append(default_startTime)
            schedule[i][1].append(default_duration)
    if check_if_schedule(accID):   # account already has schedule
        db.schedules.find_one_and_update({'accID' : accID}, {'$set' : {'timeSlots' : schedule}})
    else:   # account does not have a schedule assigned
        new_schedule(accID, schedule)
    return 0

def update_schedule(accID, day, startTime, duration):   # adds timeslot to account's schedule (if no overlap)
    if not db.schedules.find_one({'accID' : accID}):
        found = False
        schedule = [[0] * 2 for _ in range(7)]  # initialize new schedule
        for i in range(7):
            for j in range(2):
                schedule[i][j] = []

        new_schedule(accID, schedule)
        timedelta_schedule = get_schedule(accID)
        found = True
    else:
        found = True
        # schedule = db.schedules.find_one({'accID' : accID}).get('timeSlots')
        timedelta_schedule = get_schedule(accID)
    for i in range(len(timedelta_schedule[day][0])):
        s = timedelta_schedule[day][0][i]
        d = timedelta_schedule[day][1][i]
        if check_intersect(startTime, s, duration, d):  # check if the new timeslot intersects with any of the current schedule
            return 1    # Intersection found, return flag
    
    # startTime and duration were passed to this function as timedeltas, so convert to strings for storage
    string_schedule = db.schedules.find_one({'accID' : accID}).get('timeSlots')
    startTime = str(startTime)
    duration = str(duration)
    string_schedule[day][0].append(startTime)
    string_schedule[day][1].append(duration)

    if found:
        db.schedules.find_one_and_update({'accID' : accID}, {'$set' : {'timeSlots' : string_schedule}})
    else:
        new_schedule(accID, string_schedule)
    return 0

def check_if_schedule(accID):
    if (db.schedules.find_one({'accID' : accID}) != None):
        return True
    else:
        return False

def get_schedule(accID):  # returns an array of timedelta objects, NOT STRINGS!!!
    if not db.schedules.find_one({'accID' : accID}):
        return [] # if schedule doesn't exists, return any empty array
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

def clear_schedule(accID):  # Removes ALL timeslots from the schedule
    if not check_if_schedule(accID):    # no schedule found
        return
    schedule = get_schedule(accID)
    for i in range(7):
        for j in range(2):
            schedule[i][j] = []
    db.schedules.find_one_and_update({'accID' : accID}, {'$set' : {'timeSlots' : schedule}})

def delete_schedule(accID, day, startTime, duration): # removes specified timeslots
    schedule = get_schedule(accID)  # timedelta schedule used for comparisons
    if not schedule:    # check employee has a schedule
        return 1
    
    indices = []    # holds indices of timeslots to be removed
    for i in range(len(schedule[day][0])):  # checking what timeslots are enveloped
        s = schedule[day][0][i]
        d = schedule[day][1][i]
        if (startTime <= s) and ((startTime + duration) >= (s + d)):
            indices.append(i)

    string_schedule = db.schedules.find_one({'accID' : accID}).get('timeSlots')  # actual schedule getting manipulated
    i = len(indices) - 1
    while i > -1:   # removing the specified timeslots
        del string_schedule[day][0][indices[i]]
        del string_schedule[day][1][indices[i]]
        i = i - 1
    if len(indices) > 0:    # if any timeslots were removed, update the schedule
        db.schedules.find_one_and_update({'accID' : accID}, {'$set' : {'timeSlots' : string_schedule}})
    else:   # else return an error
        return 1

def get_first_day_of_week(dateIn): # returns a datetime that holds the first day of the week that the given date is in
    dayIn = date_to_weekday(dateIn)
    delta = timedelta(days=dayIn)

    dateIn = dateIn - delta

    dateOut = datetime(dateIn.year, dateIn.month, dateIn.day, 0, 0, 0, 0)

    return dateOut

def convert_schedule_to_minutes(scheduleRaw): # converts an input schedule array to ints representing the time deltas as minutes (ex. 12:00 = 720)
        scheduleOut = [[0] * 2 for _ in range(7)]

        for i in range(7): # initalize empty array
            for j in range(2):
                scheduleOut[i][j] = []

        for i in range(7): # loop thru array and convery time deltas to int representing minutes
            for j in range(len(scheduleRaw[i][0])): 
                tempStart = int(scheduleRaw[i][0][j].total_seconds() / 60) # converts start time to minutes

                tempDur = int(scheduleRaw[i][1][j].total_seconds() / 60) # converts dur to minutes
                tempFinish = tempStart + tempDur

                scheduleOut[i][0].append(tempStart)
                scheduleOut[i][1].append(tempFinish)

        return scheduleOut

def convert_tickets_to_minutes(ticketsRaw): # converts a list of tickets to a 3d array formatted the same as the schedules but with an aditional catagory for ticket id(tickets[day][0=start, 1=finish, 2=ticketID0][n])

    ticketsOut = [[0] * 3 for _ in range(7)]

    for i in range(7): # initalize empty array
         for j in range(3):
            ticketsOut[i][j] = []

    firstOfWeek = get_first_day_of_week(datetime.now())

    for x in ticketsRaw:
        if (x.get("startTime") > firstOfWeek and x.get("startTime") < (firstOfWeek + timedelta(days=7,hours=23,minutes=59))): # ensures that only tickets within the desired week are added
            day = date_to_weekday(x.get('startTime'))

            tempStart = (x.get("startTime").hour * 60) # converts start time to minutes
            tempStart += (x.get("startTime").minute)

            tempDur = x.get("eta").split(":") # converts eta to minutes
            dur = int(tempDur[0]) * 60
            dur += int(tempDur[1]) 

            finish = tempStart + dur

            ticketsOut[day][0].append(tempStart)
            ticketsOut[day][1].append(finish)
            ticketsOut[day][2].append(x.get("ticketID"))

    return ticketsOut

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

def get_day_array(date): # creates an array of the days for the next week
    out = []
    for i in range(7):
        out.append(date.day)
        date += timedelta(days=1)

    return out

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
    account = get_account(accID)
    if not account:
        return datetime.max
    schedule = get_schedule(accID)
    if not schedule:
        return datetime.max
    ticket = get_ticket_by_id(ticketID)
    if not ticket:
        return datetime.max

    ticketEta = get_ticket_eta(ticket)
    tickets = list(get_tickets_by_acc(accID))

    currentDate = datetime.now()
    currentDay = date_to_weekday(currentDate)

    startTime = currentDate # holds the tentative start time and date of the ticket, will be incremented as times are checked
    startDay = currentDay # hold the same as above but the int day of the week

    found = False
    loops = 0 # prevents looping forever when the ticket does not fit in any time slot

    while(found == False and loops <= 100):
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
                            
## Ticket Chat Functions

def new_ticket_chat(ticketID, userID, empID):
    newArr = []
    chatDoc = {'ticketID' : int(ticketID), 'userID' : int(userID), 'empID' : int(empID), 'msgs' : newArr}
    return db.ticketChats.insert_one(chatDoc)

def send_msg(ticketID, accID, msg):
    chat = db.ticketChats.find_one({'ticketID' : int(ticketID)})
    msgs = chat.get('msgs')

    newMsg = [msg, datetime.now(), int(accID)]
    msgs.append(newMsg)

    return db.ticketChats.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'msgs' : msgs}})

def get_ticket_chat(ticketID):
    return db.ticketChats.find_one({'ticketID' : ticketID})

def manual_reassign(day, startTime, eta, schedule, tickets):
    # Conversions
    ed = datetime.strptime(eta, '%H:%M:%S')
    ed = timedelta(hours=ed.hour, minutes=ed.minute, seconds=ed.second)
    ret = datetime.strptime(startTime, '%H:%M')
    sd = timedelta(hours=ret.hour, minutes=ret.minute, seconds=ret.second)
    beggining_of_week = (datetime.today() - timedelta(days=datetime.today().isoweekday() % 7)).date()    # Converting to sunday of current week
    target_date = beggining_of_week + timedelta(days=day)    # Finding target day
    # Checking for valid timeslot
    found = 0
    intersections = 0
    for i in range(len(schedule[day][0])):
        if (sd >= schedule[day][0][i]) and ((sd + ed) <= (schedule[day][0][i] + schedule[day][1][i])):
            # Found valid timeslot ==> Now check if any tickets occupy this slot
            for j in tickets:
                if (j.get('startTime').date() != target_date) or (j.get('status') == 'closed'):  # Ignore tickets not occupying the target day or closed tickets
                    continue
                # Convert for comparisons
                jsd = j.get('startTime')
                jsd = timedelta(hours=jsd.hour, minutes=jsd.minute, seconds=jsd.second)
                jed = j.get('eta')
                jed = datetime.strptime(jed, '%H:%M:%S')
                jed = timedelta(hours=jed.hour, minutes=jed.minute, seconds=jed.second)

                if (jsd >= schedule[day][0][i]) and ((jsd + jed) <= (schedule[day][0][i] + schedule[day][1][i])):
                    # Found ticket that exists in timeslot ==> Check if intersects with given ticket
                    if check_intersect(sd, jsd, ed, jed):
                        intersections += 1

            # Update found after checking all valid tickets
            found = 1
            if intersections > 0:
                found = 0

    if intersections == 0 and found == 1:   # Found a valid timeslot with no intersections
        return datetime.combine(target_date, ret.time())
    return -1

## Ticket Chat Functions

def new_ticket_chat(ticketID, userID, empID):
    newArr = []
    chatDoc = {'ticketID' : int(ticketID), 'userID' : int(userID), 'empID' : int(empID), 'msgs' : newArr}
    return db.ticketChats.insert_one(chatDoc)

def send_msg(ticketID, accID, msg):
    chat = db.ticketChats.find_one({'ticketID' : int(ticketID)})
    msgs = chat.get('msgs')

    newMsg = [msg, datetime.now(), int(accID)]
    msgs.append(newMsg)

    return db.ticketChats.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'msgs' : msgs}})

def get_ticket_chat(ticketID):
    return db.ticketChats.find_one({'ticketID' : ticketID})

def update_ticket_chat_emp(ticketID, accID):
    return db.ticketChats.find_one_and_update({'ticketID' : int(ticketID)}, {'$set' : {'empID' : accID}})

def delete_acc_from_chats(accID): # sets the id for all msgs sent by this acc to -1
    chats = list(db.ticketChats.find({'empID' : accID}))
    if (len(chats) == 0):
        chats = list(db.ticketChats.find({'userID' : accID}))

    if (len(chats) == 0):
        return False
    
    for chat in chats:
        if (chat.get('userID') == accID):
            db.ticketChats.find_one_and_update({'ticketID' : int(chat.get('ticketID'))}, {'$set' : {'userID' : -1}})
        else:
            db.ticketChats.find_one_and_update({'ticketID' : int(chat.get('ticketID'))}, {'$set' : {'empID' : -1}})

        msgs = chat.get('msgs')

        for msg in msgs:
            if (msg[2] == accID):
                msg[2] = -1

        db.ticketChats.find_one_and_update({'ticketID' : int(chat.get('ticketID'))}, {'$set' : {'msgs' : msgs}})

    return True

## Categories functions
def new_category(cat):
    return db.catagories.insert_one({"category" : str(cat)})

def get_categories_array():
    cats = list(db.categories.find())
    catsArr = []
    for i in cats:
        catsArr.append(i.get('category'))
    return catsArr

def delete_category(cat):
    return db.categories.delete_one({'category' : str(cat)})