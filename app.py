from flask import Flask, request, redirect, render_template, current_app, g, make_response, flash
from flask_pymongo import PyMongo
from pymongo import MongoClient

from datetime import date,time,datetime,timedelta

import random
import os
import string

from db import init_app, new_ticket, get_ticket_count, assign_ticket_emp, close_ticket, get_ticket_by_id, get_tickets_by_acc, assign_ticket_start_time,\
assign_ticket_eta, new_account, get_account_count, get_unassigned_tickets, get_active_tickets, check_account, new_schedule, get_schedule, get_soonest_fit,\
get_emp_accounts, get_account, get_tickets_by_account, get_accounts, delete_account, get_new_ID, check_username_free, get_account_by_username, convert_schedule_to_minutes,\
convert_tickets_to_minutes, get_first_day_of_week, get_day_array, check_if_schedule, get_categories_array, update_hours_worked, update_account, update_schedule, delete_schedule,\
get_ticket_chat, send_msg, default_schedule, clear_schedule, get_ticket_ids_by_account, get_emp_ids, schedule_start_to_datetime, manual_reassign, update_ticket_chat_emp,\
new_category, delete_category

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb+srv://admin:j6BIXDqwhnSevMT9@group29.xghzavk.mongodb.net/finalDB"
init_app(app)

def cookieID():
    return int(request.cookies.get('accID'))
def cookieType():
    return int(request.cookies.get('type'))

def check_type(type):
    if (cookieType() != None):
        if (cookieType() == type):
            return True
        elif (cookieType() == 2): # lets admin acc view every page
            return True
    return False

def format_ticket_chat(chat, accID):
    out = []
    msgs = chat.get('msgs')
    emp = get_account(chat.get('empID'))
    user = get_account(chat.get('userID'))

    if (chat.get('empID') == -1):
        empName = "Deleted User"
        empID = -1
    else:
        empName = (emp.get('fName') + " " + emp.get('lName'))
        empID = (emp.get('accID'))

    if (chat.get('userID') == -1):
        userName = "Deleted User"
    else:
        userName = (user.get('fName') + " " + user.get('lName'))
        userID = (user.get('accID'))

    for i in range(len(msgs)):
        temp = [0] * 4

        temp[0] = msgs[i][0]
        temp[1] = msgs[i][1].strftime("%H:%M %m-%d-%Y")
        
        if (msgs[i][2] == -1):
            temp[2] = "Deleted User"
        elif (msgs[i][2] == empID):
            temp[2] = empName
        else:
            temp[2] = userName

        if (msgs[i][2] == accID):
            temp[3] = True
        else:
            temp[3] = False

        out.append(temp)

    return out


@app.route("/logout/", methods=["GET", "POST"])
def logout():
    response = make_response(redirect('/'))
    response.delete_cookie('accID')
    response.delete_cookie('type')
    return response

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template('index.html')

@app.route("/login/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if check_account(username, password): # checks if the login details are valid
            acc = get_account_by_username(username)

            if (acc.get('type') == 0): # checks the account type and redirects to the appropriate page
                response = make_response(redirect('/userview/'))
            elif (acc.get('type') == 1):
                response = make_response(redirect('/ITstaffview/'))
            else:
                response = make_response(redirect('/admin/'))

            response.set_cookie('accID', str(acc.get('accID')), secure=True) # adds the login details to the cookies so that other pages can access them
            response.set_cookie('type', str(acc.get('type')), secure=True)

            return response
        else:
            error = 'Login failed. Please check your username and password.'
            return render_template('login.html', error=error)
    else:
        return render_template("login.html")
    

# Register for a new account
@app.route("/register/", methods=["GET", "POST"])
def register():
    error = None
    if (request.method == 'POST'):
        accID = get_new_ID() # gets the lowest unused acc id
        username = request.form.get("username")
        password = request.form.get("password")
        fname = request.form.get("fname")
        lname = request.form.get('lname')

        if (check_username_free(username)): # checks if the input user name is in use
            new_account(accID, username, password, fname, lname, 0)

            return redirect("/login/")
        else:
            error = "Username is already in use. Try again!"
            return render_template("register.html", error = error)
    
    else:
        return render_template('register.html')

## New Ticket Page
@app.route("/userview/newticket/", methods=['GET', 'POST'])
def newTicket():   
    if (check_type(0) or check_type(2)):
        if (request.method == 'POST'):
            out = "" # will hold the info sumbitted by user to be sent to database as a newticket, seperated by commas
            # formatted as: "accID,category,description"
            
            accID = cookieID()
            out += str(accID)

            category = request.form['catagories']
            desc = request.form['desc']

            ticketID = get_ticket_count() + 1   # potential bug if tickets can be deleted, generating new tickets with overlapping ids

            new_ticket(ticketID, accID, category, desc) # creates a new ticket with the info given

            return redirect("/userview/")

        else:
            categoriesArray = get_categories_array() # gets an array of the categories from the database

            return render_template('newticket.html', catagoriesArray=categoriesArray)
    else:
        return "Not authorized to view this page"


## Ticket Submitted Page
@app.route("/userview/ticketsubmitted/", methods=['GET', 'POST'])
def ticketSubmitted():
    if (request.method == 'POST'):
        return redirect("/userview/") 
    else:
        return render_template('ticketsubmitted.html')
    
## Admin View
@app.route("/admin/", methods=["GET", "POST"])
def admin():
    if (check_type(2)): # check account type is 'admin'
        message = ''
        if (request.method == 'POST'):
            if (request.form['submit'] == 'logout'):
                return redirect('/logout/')
            # Manage Employees
            elif (request.form['submit'] == 'allEmp'):  # On button press, display all employee accounts and information
                return redirect('/admin/roster/')
            elif (request.form['submit'] == 'createEmp'):
                return redirect('/admin/create/')
            elif (request.form['submit'] == 'deleteEmp'):
                empID = request.form['empAccs']
                return redirect('/admin/delete/' + str(empID))
            elif (request.form['submit'] == 'modifyEmp'):
                empID = request.form['empAccs']
                return redirect('/admin/modify/' + str(empID))
            elif (request.form['submit'] == 'deleteCat'):   # Delete a category
                cat = request.form['cats']
                response = delete_category(cat)
                if not response:
                    message = 'Failed to remove: ' + cat
                else:
                    message = 'Successfully removed: ' + cat
            elif (request.form['submit'] == 'createCat'):   # Create a category
                cat = request.form['cat']
                message = 'Successfully added: ' + cat
                new_category(cat)
        
        categories = get_categories_array()
        emps = get_emp_accounts()
        return render_template('admin.html', emps=emps, categories=categories, message=message)
    else:
        return "Error: Not authorized to view this page"    # If account type is not 'admin', throw an error

@app.route("/admin/roster/", methods=["GET", "POST"])
def printRoster():
    if (check_type(2)):
        if (request.method == 'POST'):
            if(request.form['submit'] == 'return'):
                return redirect('/admin/')
        
        accounts = get_emp_accounts()    # grab all employee accounts to be displayed
        return render_template('adminroster.html', accounts=accounts)
    else:
        return 'Error: Not authorized to view this page'
    
@app.route("/admin/create/", methods=["GET", "POST"])
def createEmp():
    if (check_type(2)):
        if (request.method == 'POST'):
            if(request.form['submit'] == 'return'):
                return redirect('/admin/')
            elif(request.form['submit'] == 'createEmp'):
                accID = get_new_ID()    # Genereate a new unique id for the account
                fname = request.form['fname']
                lname = request.form['lname']
                username = request.form['username']
                password = request.form['password']
                accType = int(request.form['accType'])
                if not check_username_free(username):
                    return 'Error: Username is already in use.'
                else:
                    new_account(accID, username, password, fname, lname, accType)    # create a new account with the added information
                    account = get_account(accID)    # update account variable to display new information
                return render_template('admincreate.html', account=account)
        
        return render_template('admincreate.html')
    else:
        return 'Error: Not authorized to view this page'
    
@app.route("/admin/delete/<int:empID>", methods=["GET", "POST"])
def deleteEmp(empID):
    if (check_type(2)):
        account = get_account(empID)
        message = ''
        if (request.method == 'POST'):
            if (request.form['submit'] == 'return'):
                return redirect('/admin/')
            elif (request.form['submit'] == 'confirm'):
                if delete_account(empID):   # account existence and type are checked in function to prevent html modifications from deleting a random account
                    return 'Error: Account deletion unsuccessful, check that the provided id is an employee and that the account exists.'
                message = 'Successfully deleted account.'
        return render_template('admindelete.html', account=account, message=message)
    else:
        return "Error: Not authorized to view this page"
    
@app.route("/admin/modify/<int:empID>", methods=["GET", "POST"])
def modifyEmp(empID):
    if (check_type(2)):
        account = get_account(empID)
        if (not account) or (account.get('type') != 1):  # check that accID exists and is an employee
            return 'Error: Specified employee does not exist.'
        tickets = get_tickets_by_acc(empID)
        schedule = get_schedule(empID)
        # Processing webpage
        if (request.method == 'POST'):
            if(request.form['submit'] == 'return'):
                return redirect('/admin/')
            elif(request.form['submit'] == 'change'):    # Change the current employee being viewed
                empID = request.form['empAccs']
                return redirect('/admin/modify/' + str(empID))
            elif(request.form['submit'] == 'modify'):    # Modify the current employee's information
                fname = request.form['fname']
                lname = request.form['lname']
                username = request.form['username']
                password = request.form['password']
                if not update_account(empID, username, password, fname, lname):
                    return 'Error: Username is already being used.'
            elif(request.form['submit'] == 'reassign'):    # Redirect to reassign interface
                ticketID = request.form['tIDs']
                empID = request.form['eIDs']
                return redirect('/admin/reassign/' + ticketID + '/' + empID)
            elif((request.form['submit'] == 'schedule') or (request.form['submit'] == 'remove')):    # Schedule Modifications
                day = int(request.form['day'])   # indexes: 0-6, sun-sat
                start = request.form['startTime']
                end = request.form['endTime']
                # Formatting startTime to ==> HH:MM:SS
                startDateTime = datetime.strptime(start, '%H:%M')
                startDelta = timedelta(hours=startDateTime.hour, minutes=startDateTime.minute)    # Converting to timedelta for comparisons
                # Calculating duration
                durationDelta = datetime.strptime(end, '%H:%M') - startDateTime
                if(request.form['submit'] == 'schedule'):   # Add timeslot
                    if update_schedule(empID, day, startDelta, durationDelta):
                        return 'Error: Intersection found, please resolve the conflict.'
                else:   # Remove timeslot
                    if delete_schedule(empID, day, startDelta, durationDelta):
                        return 'Error: No timeslots to remove for the specified window.'
            elif(request.form['submit'] == 'default'):
                default_schedule(empID)
            elif(request.form['submit'] == 'clear'):
                clear_schedule(empID)

            # Load modified information
            account = get_account(empID)
            tickets = get_tickets_by_acc(empID)
            schedule = get_schedule(empID)

        days_list = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']    # Formatting
        emps = get_emp_accounts()   # Used for changing employee dropdown
        empIDs = get_emp_ids()  # Ticket reassignment selection
        ticketIDs = get_ticket_ids_by_account(empID)    # For ticket reassignment
        return render_template('adminmodify.html', empID=empID, account=account, tickets=tickets, ticketIDs=ticketIDs, emps=emps, empIDs=empIDs, schedule=schedule, days_list = days_list)
    else:
        return 'Error: Not authorized to view this page'
   
@app.route("/admin/reassign/<int:ticketID>/<int:empID>", methods=["GET", "POST"])
def reassignTicket(ticketID, empID):
    if (check_type(2)):
        ticket = get_ticket_by_id(ticketID)
        if (not ticket) or (ticket.get('status') == 'closed'):  # check that ticket exists and isn't closed
            return 'Error: Specified ticket is ineligible for reassignment.'
        assigned_emp = get_account(ticket.get('assignedEmpID'))    # employee currently assigned to the ticket
        if not assigned_emp:
            return 'Error: Assigned Employee no longer exists.'
        assigned_emp_id = assigned_emp.get('accID')
        candidate = get_account(empID)
        if (not candidate) or (candidate.get('type') != 1):
            return 'Error: Specified employee no longer exists.'
        schedule = get_schedule(empID)
        if len(schedule) == 0:
            return 'Error: Candidate employee has no schedule'
        
        # Processing webpage
        if (request.method == 'POST'):
            if(request.form['submit'] == 'return'):
                return redirect('/admin/')
            elif(request.form['submit'] == 'change'):
                empID = request.form['empAccs']
                return redirect('/admin/reassign/' + str(ticketID) + '/' + empID)
            elif(request.form['submit'] == 'auto'):    # Use the soonest_fit algorithm to reassign the ticket to the currently selected candidate employee
                startTime = get_soonest_fit(empID, ticketID)    # returns start time if it can fit, else max
                if (startTime != datetime.max):   # if candidate found
                    if assign_ticket_emp(ticketID, empID):
                        return 'Error: Ticket could not be reassigned.'
                    else:   # if ticket reassignment was successful, update
                        update_ticket_chat_emp(ticketID, empID)
                        assign_ticket_start_time(ticketID, startTime)
                        ticket = get_ticket_by_id(ticketID)
                else:
                    return 'Error: Ticket could not be reassigned.'
            elif(request.form['submit'] == 'manual'):    # Manually reassign the ticket
                day = int(request.form['day'])
                startTime = request.form['startTime']
                eta = ticket.get('eta')
                tickets = get_tickets_by_acc(empID)
                startTime = manual_reassign(day, startTime, eta, schedule, tickets)    # Call the manual reassignment function
                if startTime != -1:    # Check if an error code was returned
                    if assign_ticket_emp(ticketID, empID):
                        return 'Error: Ticket could not be reassigned.'
                    else:
                        update_ticket_chat_emp(ticketID, empID)
                        assign_ticket_start_time(ticketID, startTime)
                        ticket = get_ticket_by_id(ticketID)
                else:
                    return 'Error: Ticket could not be reassigned.'


        # Page Formatting
        emps = get_emp_accounts()
        tickets = get_tickets_by_acc(empID)
        days_list = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        return render_template('adminreassign.html', emps=emps, account=candidate, ticket=ticket, schedule=schedule, tickets=tickets, days_list=days_list)
    else:
        return 'Error: Not authorized to view this page'

## IT Staff View
@app.route("/ITstaffview/", methods=["GET", "POST"])
def ITstaffview():
    if (check_type(1)):
        if (request.method == 'POST'):
            print('test')
        else:
            empID = cookieID()
            ticketRaw = list(get_tickets_by_acc(empID)) # gets a list of the tickets assinged to empID, list is of JSONs, will be converted to arrays

            ticketJSON = []

            for x in ticketRaw:
                if (x.get('status') == "assigned"):
                    ticketJSON.append(x)

            ticketsArr = [[0] * 5 for _ in range(len(ticketJSON))] # create a 2D array of size [# tickets] x 5

            # TODO: sort list by start time once ticket assignment is implemented

            i = 0
            while(i < len(ticketJSON)): # loops thru all tickets and puts the JSON data into the tickets array
                ticketsArr[i][0] = ticketJSON[i].get('ticketID')
                ticketsArr[i][1] = ticketJSON[i].get('startTime').strftime("%m-%d-%Y %H:%M") 
                ticketsArr[i][2] = ticketJSON[i].get('eta')  
                ticketsArr[i][2] = ticketsArr[i][2][:len(ticketsArr[i][2]) - 3] # remove the last 3 chars of the time string, as these contain the seconds          
                ticketsArr[i][3] = ticketJSON[i].get('category')
                ticketsArr[i][4] = ticketJSON[i].get('description')
                i += 1

            return render_template('ITstaffview.html', tickets = ticketsArr) # ID, start time, ETA, category, description 
    else:
        return "Not authorized to view this page"
    

## IT Staff eta assisgnment overview page page
@app.route("/ITstaffview/eta/", methods=["GET", "POST"])
def etaAssignment():
    if (check_type(1)):
        if (request.method == 'POST'):
            print("test")
        else:
            ticketJSON = list(get_unassigned_tickets()) # gets a list of unassigned tickets

            ticketsArr = [[0] * 3 for _ in range(len(ticketJSON))] # creates a 2D array, # tickets x 3

            i = 0
            while(i < len(ticketJSON)):
                ticketsArr[i][0] = ticketJSON[i].get('ticketID')
                ticketsArr[i][1] = ticketJSON[i].get('category')
                ticketsArr[i][2] = ticketJSON[i].get('description')
                i += 1

            return render_template('etaassignment.html', tickets = ticketsArr)
    else:
        return "Not authorized to view this page"
    

## IT Staff Ticket page
@app.route("/ITstaffview/ticket/<int:ticketID>", methods=["GET", "POST"])
def staffTicketView(ticketID):
    if (check_type(1)):
        ticket = get_ticket_by_id(ticketID)
        if (cookieID() == ticket.get('assignedEmpID') or check_type(2)):
            if request.method == 'POST': # mark ticket as closed
                if (request.form['submit'] == "close"):
                    return redirect("/ITstaffview/ticket/" + str(ticketID) + "/close/")
                else: # send chat msg
                    send_msg(ticketID, cookieID(), request.form['chatInput'])
                    return redirect("/ITstaffview/ticket/" + str(ticketID))
            else:
                ticketJSON = get_ticket_by_id(ticketID) # get the ticket associated with that ticketID

                chatContents = format_ticket_chat(get_ticket_chat(ticketID), cookieID())

                ticketsArr = [0] * 7 # create a list of size 7
                ticketsArr[0] = ticketJSON.get('ticketID')
                ticketsArr[1] = ticketJSON.get('category')
                ticketsArr[2] = ticketJSON.get('status')
                ticketsArr[3] = ticketJSON.get('description')
                ticketsArr[4] = ticketJSON.get('eta')
                ticketsArr[4] = ticketsArr[4][:len(ticketsArr[4]) - 3] # remove the last 3 chars of the time string, as these contain the seconds  
                fName = get_account(ticketJSON.get('userID')).get('fName') 
                lName = get_account(ticketJSON.get('userID')).get('lName') # get user first name and last name
                empName = fName + " " + lName
                ticketsArr[5] = empName
                ticketsArr[6] = ticketJSON.get('startTime').strftime("%m-%d-%Y %H:%M")

                return render_template('ITstaffviewticket.html', ticket = ticketsArr, chatContents = chatContents)
        else:
            return "Not authorized to view this page"
    else:
        return "Not authorized to view this page"
    
@app.route("/ITstaffview/ticket/<int:ticketID>/close/", methods=['GET', 'POST'])
def closeTicket(ticketID):
    if (check_type(1)):
        ticket = get_ticket_by_id(ticketID)
        if (cookieID() == ticket.get('assignedEmpID') or check_type(2)):
            if (request.method == 'GET'):
                return render_template("closeticket.html")
            else:
                hoursWorked = int(request.form['input']) # gets the input hours worked
                update_hours_worked(ticketID, hoursWorked)
                close_ticket(ticketID) 
                return redirect("/ITstaffview/")
        else:
            return "Not authorized to view this page"
    else:
        return "Not authorized to view this page"

## IT Staff ticket eta assignment page
@app.route("/ITstaffview/eta/<ticketID>", methods=["GET", "POST"])
def ticketEtaAssignment(ticketID):
    if (check_type(1)):
        if (request.method == 'POST'):
            if (request.form['hours'].isdigit() & request.form['minutes'].isdigit()):
                if (int(request.form['minutes']) < 60):
                    eta = time(int(request.form['hours']), int(request.form['minutes']))

                    assign_ticket_eta(ticketID, eta.isoformat()) # assignes the input eta estimate to the ticket (must be done before finding fit since eta is used)

                    soonestFit = datetime.max # sets the starting soonest time to the max time, if it is this time at the end, error is returned, as no fit could be found
                    emps = list(get_emp_accounts()) # gets a list of all emps

                    for x in emps: # loops thru all emps, gets the soonest time the ticket could fit into their schedule
                        if (check_if_schedule(x.get('accID'))): # checks to make sure the given emp has a schedule, prevents crash
                            thisEmpSoonestFit = get_soonest_fit(x.get('accID'), ticketID)

                            if (thisEmpSoonestFit < soonestFit): # checks if this emp can do the ticket sooner than previous ones
                                soonestFit = thisEmpSoonestFit
                                soonestEmp = x.get('accID')

                    if (soonestFit == datetime.max):
                        return "error: could not fit ticket with that eta into any employees schedule"
                    else:
                        assign_ticket_emp(ticketID, soonestEmp) # assigns the ticket to the emp that it fit soonest with
                        assign_ticket_start_time(ticketID, soonestFit)

                    return redirect("/ITstaffview/eta")
                else:
                    return "Error: Invalid input"
            else:
                return "Error: Invalid input"
        else:
            ticketJSON = get_ticket_by_id(ticketID) # get the ticket in the url from the db
            ticketArr = [0] * 3
            ticketArr[0] = ticketID
            ticketArr[1] = ticketJSON.get('category')
            ticketArr[2] = ticketJSON.get('description')

            return render_template('ticketeta.html', ticket = ticketArr) # displays the tickets info
    else:
        return "Not authorized to view this page"
    
## IT staff calendar page
@app.route("/ITstaffview/calendar")
def empCalendar():
    if (check_type(1)):
        scheduleRaw = get_schedule(cookieID()) # gets the raw json data for the emps tickets and schedule
        ticketsRaw = list(get_tickets_by_acc(cookieID()))

        schedule = convert_schedule_to_minutes(scheduleRaw) # convets the raw data to arrays of ints representing minutes from 00:00
        tickets = convert_tickets_to_minutes(ticketsRaw)

        firstOfWeek = get_first_day_of_week(datetime.now())

        dayArray = get_day_array(firstOfWeek)

        return render_template('ITstaffcalendar.html', shift = schedule, tickettime = tickets)
    
    return "Not authorized to view this page"

## User view
@app.route("/userview/", methods=["GET", "POST"])
def userview():
    if (check_type(0)):
        if (request.method == 'POST'):
            print('test')
        else:
            accID = cookieID()
            ticketJSON = list(get_active_tickets(accID)) # gets a list of the active tickets of that accID

            ticketsArr = [[0] * 4 for _ in range(len(ticketJSON))] # create a 2D array of size [# tickets] x 4

            for i in range(len(ticketJSON)):
                ticketsArr[i][0] = ticketJSON[i].get('ticketID')
                ticketsArr[i][1] = ticketJSON[i].get('category')
                ticketsArr[i][2] = ticketJSON[i].get('status')
                ticketsArr[i][3] = ticketJSON[i].get('description')

            return render_template('userview.html', tickets = ticketsArr)
    else:
        return "Not authorized to view this page. Ensure that you are logged in."

## Users view their ticket history 
@app.route("/userview/usertickethistory/", methods=["GET", "POST"])
def usertickethistory():
    if (check_type(0)):
        if (request.method == 'POST'):
            print('test')
        else:
            accID = cookieID()
            ticketJSON = list(get_tickets_by_account(accID)) # gets a list of the active tickets of that accID

            ticketsArr = [[0] * 5 for _ in range(len(ticketJSON))] # create a 2D array of size [# tickets] x 6

            for i in range(len(ticketJSON)):
                ticketsArr[i][0] = ticketJSON[i].get('ticketID')
                ticketsArr[i][1] = ticketJSON[i].get('category')
                ticketsArr[i][2] = ticketJSON[i].get('status')
                ticketsArr[i][3] = ticketJSON[i].get('description')

            return render_template('usertickethistory.html', tickets = ticketsArr)
    else:
        return "Not authorized to view this page. Ensure that you are logged in."
    
## Users view ticket 
@app.route("/userview/userviewticket/<int:ID>", methods=["GET", "POST"])
def vewticket(ID):
    ticketJSON = get_ticket_by_id(ID) # get the ticket associated with that ticketID

    if (check_type(0)):
        if (ticketJSON.get('userID') == cookieID() or check_type(2)):          
            if (request.method == 'POST'):
                send_msg(ID, cookieID(), request.form['chatInput'])
                return(redirect("/userview/userviewticket/" + str(ID)))
            else:
                ticketsArr = [0] * 7 # create a list of size 7
                ticketsArr[0] = ticketJSON.get('ticketID')
                ticketsArr[1] = ticketJSON.get('category')
                ticketsArr[2] = ticketJSON.get('status')
                ticketsArr[3] = ticketJSON.get('description')
                ticketsArr[4] = ticketJSON.get('eta')
                # checking if those are NoneType object
                if (ticketsArr[4] is not None):
                    ticketsArr[4] = ticketsArr[4][:len(ticketsArr[4]) - 3] # remove the last 3 chars of the time string, as these contain the seconds  
                if(ticketJSON.get('status') == 'unassigned'):
                    ticketsArr[5] = ''
                    chatContents = None
                    chat = False
                else:
                    fName = get_account(ticketJSON.get('assignedEmpID')).get('fName') 
                    lName = get_account(ticketJSON.get('assignedEmpID')).get('lName') # get empployee first name and last name
                    empName = fName + " " + lName
                    ticketsArr[5] = empName
                    chat = True # chat is true when tickets is assigned
                    chatContents = format_ticket_chat(get_ticket_chat(ID), cookieID()) # get the chat and chat history, stored in an array
                ticketsArr[6] = ticketJSON.get('startTime')
                if(ticketsArr[4] is not None):
                    ticketsArr[6] = ticketJSON.get('startTime').strftime("%m-%d-%Y %H:%M")


                return render_template('userviewticket.html', ticket = ticketsArr, chatContents = chatContents, chat = chat)
            
        else:
            return "Not authorized to view this page. Ensure that you are logged in."
    else:
        return "Not authorized to view this page. Ensure that you are logged in."

if __name__ == '__main__':
    app.run(debug=True)
