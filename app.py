from flask import Flask, request, redirect, render_template, current_app, g
from flask_pymongo import PyMongo
from pymongo import MongoClient

import random
import os
import datetime
import string

from db import init_app, new_ticket, get_ticket_count, assign_ticket_emp, close_ticket, get_ticket_by_id, get_tickets_by_acc, assign_ticket_start_time, assign_ticket_eta


app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb+srv://admin:j6BIXDqwhnSevMT9@group29.xghzavk.mongodb.net/testDB"
init_app(app)


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template('index.html')

@app.route("/homepage/", methods=["GET", "POST"])
def hoempage():
    return render_template('homepage.html')

@app.route("/login/", methods=["GET", "POST"])
def login():
    return render_template('login.html')

@app.route("/register/", methods=["GET", "POST"])
def register():
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
        return redirect("/homepage/") # link to homepage/dashboard/ect goes here
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


if __name__ == '__main__':
    app.run(debug=True)