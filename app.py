from flask import Flask, request, redirect, render_template
import random

app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')

## New Ticket Page
@app.route("/newticket/")
def newTicket():   
    catagoriesArray = ["category1", "category2", "category3"] # TODO: get catagories from database

    return render_template('newticket.html', catagoriesArray=catagoriesArray)

@app.route("/newticket/", methods=['POST'])
def newTicketPost():
    out = "" # will hold the info sumbitted by user to be sent to database as a newticket, seperated by commas
    # formatted as: "accID,category,description"
    
    accID = random.randrange(100, 999) # TODO: get accID from cached acc info once accounts have been implemented
    out += str(accID)

    category = request.form['catagories']
    desc = request.form['desc']

    desc = desc.replace(",", "") # removes commas to prevent messing up the format, TODO: implement input validation for other unwanted inputs

    out += ","
    out += category
    out += ","
    out += desc

    print(out)
    # send out to wherever new tickets go

    return redirect("/ticketsubmitted")

## Ticket Submitted Page
@app.route("/ticketsubmitted/")
def ticketSubmitted():
    return render_template('ticketsubmitted.html')

@app.route("/ticketsubmitted/", methods=['POST'])
def ticketSubmittedPost():
    return redirect("/") # link to homepage/dashboard/ect goes here


if __name__ == '__main__':
    app.run(debug=True)