from flask import Flask, request, redirect, render_template, current_app, g, make_response
from flask_pymongo import PyMongo
from pymongo import MongoClient

from datetime import date,time,datetime,timedelta

import random
import os
import string

from db import init_app, new_ticket, get_ticket_count, assign_ticket_emp, close_ticket, get_ticket_by_id, get_tickets_by_acc, assign_ticket_start_time, assign_ticket_eta, new_account, get_account_count, get_unassigned_tickets, get_active_tickets, check_account, new_schedule, get_schedule, get_soonest_fit, get_emp_accounts, get_account, get_tickets_by_account, get_accounts, delete_account, get_new_ID, check_username_free, get_account_by_username

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb+srv://admin:j6BIXDqwhnSevMT9@group29.xghzavk.mongodb.net/testDB"
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

@app.route("/logout/", methods=["GET", "POST"])
def logout():
    response = make_response(redirect('/'))
    response.delete_cookie('accID')
    response.delete_cookie('type')
    return response

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template('index.html')

## delete late
@app.route("/homepage/", methods=["GET", "POST"])
def homepage():
    return render_template('homepage.html')

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if check_account(username, password):
            acc = get_account_by_username(username)

            if (acc.get('type') == 0):
                response = make_response(redirect('/userview/'))
            elif (acc.get('type') == 1):
                response = make_response(redirect('/ITstaffview/'))
            else:
                response = make_response(redirect('/admin/'))

            response.set_cookie('accID', str(acc.get('accID')), secure=True)
            response.set_cookie('type', str(acc.get('type')), secure=True)

            return response
        else:
            return "Login Failed, incorrect username or password"
    else:
        return render_template("login.html")
    

# Register for a new account
@app.route("/register/", methods=["GET", "POST"])
def register():
    if (request.method == 'POST'):
        accID = get_new_ID()
        username = request.form.get("username")
        password = request.form.get("password")
        fname = request.form.get("fname")
        lname = request.form.get('lname')

        if (check_username_free):
            new_account(accID, username, password, fname, lname, 0)

            return redirect("/login/")
        else:
            return "Error: username is already in use"
    
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

            return redirect("/userview/ticketsubmitted/")

        else:
            catagoriesArray = ["category1", "category2", "category3"] # TODO: get catagories from database

            return render_template('newticket.html', catagoriesArray=catagoriesArray)
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
        if (request.method == 'POST'):
            if (request.form['submit'] == 'allEmp'):  # On button press, display all employee accounts and information
                return redirect('/admin/roster/')
            elif (request.form['submit'] == 'createEmp'):
                return redirect('/admin/create/')
            elif (request.form['submit'] == 'deleteEmp'):
                return redirect('/admin/delete')
        return render_template('admin.html')
    else:
        return "Not authorized to view this page"

@app.route("/admin/roster/", methods=["GET", "POST"])
def printRoster():
    if (check_type(2)):
        if (request.method == 'POST'):
            if(request.form['submit'] == 'return'):
                return redirect('/admin/')
        else:
            accounts = get_emp_accounts()
            return render_template('adminroster.html', accounts=accounts)
    else:
        return 'Not authorized to view this page'
    
@app.route("/admin/create/", methods=["GET", "POST"])
def createEmp():
    if (check_type(2)):
        if (request.method == 'POST'):
            if(request.form['submit'] == 'return'):
                return redirect('/admin/')
            elif(request.form['submit'] == 'createEmp'):
                accID = get_new_ID()
                fname = request.form['fname']
                lname = request.form['lname']
                username = request.form['username']
                password = request.form['password']
                new_account(accID, username, password, fname, lname, 1)
                account = get_account(accID)
                return render_template('admincreate.html', account=account)
        else:
            return render_template('admincreate.html')
    else:
        return 'Not authorized to view this page'
    
@app.route("/admin/delete/", methods=["GET", "POST"])
def deleteEmp():
    if (check_type(2)):
        if (request.method == 'POST'):
            if(request.form['submit'] == 'return'):
                return redirect('/admin/')
            elif(request.form['submit'] == 'deleteEmp'):
                accID = int(request.form['delID'])
                if not get_account(accID):
                    return 'Specified employee does not exist'
                else:
                    delete_account(accID)
                    return render_template('admindelete.html', message='Account successfully deleted')
        else:
            return render_template('admindelete.html')
    else:
        return 'Not authorized to view this page'

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
            if request.method == 'POST':
                close_ticket(ticketID)
                return redirect("/ITstaffview/ticket/" + str(ticketID))
            else:
                ticketJSON = get_ticket_by_id(ticketID) # get the ticket associated with that ticketID

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

                return render_template('ITstaffviewticket.html', ticket = ticketsArr)
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

                    assign_ticket_eta(ticketID, eta.isoformat())

                    soonestFit = datetime.max
                    emps = list(get_emp_accounts())

                    for x in emps:
                        thisEmpSoonestFit = get_soonest_fit(x.get('accID'), ticketID)

                        if (thisEmpSoonestFit < soonestFit):
                            soonestFit = thisEmpSoonestFit
                            soonestEmp = x.get('accID')

                    if (soonestFit == datetime.max):
                        return "error: could not fit ticket with that eta into any employees schedule"
                    else:
                        assign_ticket_emp(ticketID, soonestEmp)
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

            return render_template('ticketeta.html', ticket = ticketArr)
    else:
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
                print('test')
            else:
                ticketsArr = [0] * 7 # create a list of size 7
                print('HI')
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
                    chat = False
                else:
                    fName = get_account(ticketJSON.get('assignedEmpID')).get('fName') 
                    lName = get_account(ticketJSON.get('assignedEmpID')).get('lName') # get empployee first name and last name
                    empName = fName + " " + lName
                    ticketsArr[5] = empName
                    chat = True
                ticketsArr[6] = ticketJSON.get('startTime')
                if(ticketsArr[4] is not None):
                    ticketsArr[6] = ticketJSON.get('startTime').strftime("%m-%d-%Y %H:%M")


                return render_template('userviewticket.html', ticket = ticketsArr, chat = chat)
            
        else:
            return "Not authorized to view this page. Ensure that you are logged in."
    else:
        return "Not authorized to view this page. Ensure that you are logged in."

if __name__ == '__main__':
    app.run(debug=True)