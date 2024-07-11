from flask import Flask, request, redirect, render_template, current_app, g
from flask_pymongo import PyMongo
from pymongo import MongoClient

import random
import os
import datetime
import string

from db import init_app, new_ticket, get_ticket_count, assign_ticket_emp, close_ticket, get_ticket_by_id, get_tickets_by_acc, assign_ticket_start_time, assign_ticket_eta, new_account, get_account_count, get_unassigned_tickets

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb+srv://admin:j6BIXDqwhnSevMT9@group29.xghzavk.mongodb.net/testDB"
init_app(app)


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template('index.html')

@app.route("/homepage/", methods=["GET", "POST"])
def homepage():
    return render_template('homepage.html')

@app.route("/login/", methods=["GET", "POST"])
def login():
    return render_template('login.html')

# Register for a new account
@app.route("/register/", methods=["GET", "POST"])
def register():
    if (request.method == 'POST'):
        accID = get_account_count() + 1
        username = request.form.get("username")
        password = request.form.get("password")
        fname = request.form.get("fname")
        lname = request.form.get('lname')

        new_account(accID, username, password, fname, lname)

        return redirect("/login/")
    
    else:
        return render_template('register.html')

## New Ticket Page
@app.route("/newticket/", methods=['GET', 'POST'])
def newTicket():   
    if (request.method == 'POST'):
        out = "" # will hold the info sumbitted by user to be sent to database as a newticket, seperated by commas
        # formatted as: "accID,category,description"
        
        accID = random.randrange(100, 999) # TODO: get accID from cached acc info once accounts have been implemented
        out += str(accID)

        category = request.form['catagories']
        desc = request.form['desc']

        ticketID = get_ticket_count() + 1

        new_ticket(ticketID, accID, category, desc) # creates a new ticket with the info given

        return redirect("/ticketsubmitted")

    else:
        catagoriesArray = ["category1", "category2", "category3"] # TODO: get catagories from database

        return render_template('newticket.html', catagoriesArray=catagoriesArray)


## Ticket Submitted Page
@app.route("/ticketsubmitted/", methods=['GET', 'POST'])
def ticketSubmitted():
    if (request.method == 'POST'):
        return redirect("/homepage/") 
    else:
        return render_template('ticketsubmitted.html')
    
## Debug Page
@app.route("/debug/", methods=["GET", "POST"])
def debug():
    if (request.method == 'POST'):
        if (request.form['submit'] == "assign"):            
            ticketID = request.form['ticketID']
            empID = request.form['empID']
            assign_ticket_emp(ticketID, empID)
        elif (request.form['submit'] == "close"):
            ticketID = request.form['ticketIDc']
            close_ticket(ticketID)
        elif (request.form['submit'] == "lookTicket"):
            ticketID = request.form['ticketIDl']
            ticket = get_ticket_by_id(ticketID)
            print(ticket)
        elif (request.form['submit'] == "lookAcc"):
            accID = request.form['accID']
            tickets = get_tickets_by_acc(accID)
            for x in tickets:
                print(x)

    return render_template('debug.html')

## IT Staff View
@app.route("/ITstaffview/", methods=["GET", "POST"])
def ITstaffview():
    if (request.method == 'POST'):
        print('test')
    else:
        empID = 2 # TODO: get empID from logged in account
        ticketJSON = list(get_tickets_by_acc(empID)) # gets a list of the tickets assinged to empID, list is of JSONs, will be converted to arrays

        ticketsArr = [[0] * 5 for _ in range(len(ticketJSON))] # create a 2D array of size [# tickets] x 5

        # TODO: sort list by start time once ticket assignment is implemented

        i = 0
        while(i < len(ticketJSON)): # loops thru all tickets and puts the JSON data into the tickets array
            ticketsArr[i][0] = ticketJSON[i].get('ticketID')
            #ticketsArr[i][1] = ticketJSON[i].get('startTime') TODO: UNCOMMENT THESE TWO LINES AND REMOVE THE TWO BELOW THEM ONCE TICKET ASSIGNEMENT IS DONE
            #ticketsArr[i][2] = ticketJSON[i].get('eta)             
            ticketsArr[i][1] = "12/24/2024, 13:30"
            ticketsArr[i][2] = "01:15"
            ticketsArr[i][3] = ticketJSON[i].get('category')
            ticketsArr[i][4] = ticketJSON[i].get('description')
            i += 1

        return render_template('ITstaffview.html', tickets = ticketsArr) # ID, start time, ETA, category, description 
    

## IT Staff eta assisgnment overview page page
@app.route("/ITstaffview/eta/", methods=["GET", "POST"])
def etaAssignment():
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
    

## IT Staff Ticket page
@app.route("/ITstaffview/ticket/<int:ticketID>", methods=["GET", "POST"])
def staffTicketView(ticketID):
    return "ticket: " + str(ticketID)


## IT Staff ticket eta assignment page
@app.route("/ITstaffview/eta/<ticketID>", methods=["GET", "POST"])
def ticketEtaAssignment(ticketID):
    return "ticket: " + str(ticketID)


## User view
@app.route("/userview/", methods=["GET", "POST"])
def userview():
    if (request.method == 'POST'):
        print('test')
    else:
        '''
        TODO:
        - get userID
        - users active tickets (store as a 2D list)        
        '''
        return render_template('userview.html', tickets = [["01", "1", "des1"], ["02", "2", "des2"]])

if __name__ == '__main__':
    app.run(debug=True)