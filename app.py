from flask import Flask, request, redirect, render_template, current_app, g
from flask_pymongo import PyMongo
from pymongo import MongoClient

import random
import os
import datetime
import string

from db import init_app, new_ticket, get_ticket_count, get_ticket_by_id, get_tickets_by_acc, assign_ticket_emp, assign_ticket_eta, assign_ticket_start_time, close_ticket, new_account, delete_account, get_account_count, get_accounts

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

        ticketID = get_ticket_count() + 1   # potential bug if tickets can be deleted, generating new tickets with overlapping ids

        new_ticket(ticketID, accID, category, desc) # creates a new ticket with the info given

        return redirect("/ticketsubmitted")

    else:
        catagoriesArray = ["category1", "category2", "category3"] # TODO: get catagories from database

        return render_template('newticket.html', catagoriesArray=catagoriesArray)


## Ticket Submitted Page
@app.route("/ticketsubmitted/", methods=['GET', 'POST'])
def ticketSubmitted():
    if (request.method == 'POST'):
        return redirect("/homepage/") # link to homepage/dashboard/ect goes here
    else:
        return render_template('ticketsubmitted.html')
    
## Admin Page
@app.route("/admin/", methods=["GET", "POST"])
def admin():
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
        # Start Admin Functionality
        elif (request.form['submit'] == 'allEmp'):  # On button press, display all employee accounts and information
            accounts = get_accounts()
            return render_template('admin.html', accounts=accounts)
        elif (request.form['submit'] == 'createEmp'):
            accID = get_account_count()
            fname = request.form['fname']
            lname = request.form['lname']
            username = request.form['username']
            password = request.form['password']
            new_account(accID, username, password, fname, lname)
        elif (request.form['submit'] == 'deleteEmp'):
            accID = request.form['delID']
            # if not isinstance(accID, int):
                # print('Error: Incorrect Input')   # Figure out better way to handle this
            # else:
                # delete_account(accID)
            delete_account(int(accID))
        # add ticket view

    return render_template('admin.html')


if __name__ == '__main__':
    app.run(debug=True)