from flask import Flask, request, redirect, render_template
import random

app = Flask(__name__)


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

        desc = desc.replace(",", "") # removes commas to prevent messing up the format, TODO: implement input validation for other unwanted inputs

        out += ","
        out += category
        out += ","
        out += desc

        print(out)
        # send out to wherever new tickets go

        return redirect("/ticketsubmitted")

    else:
        catagoriesArray = ["category1", "category2", "category3"] # TODO: get catagories from database

        return render_template('newticket.html', catagoriesArray=catagoriesArray)


## Ticket Submitted Page
@app.route("/ticketsubmitted/", methods=['GET', 'POST'])
def ticketSubmitted():
    if (request.method == 'POST'):
        return redirect("/") # link to homepage/dashboard/ect goes here
    else:
        return render_template('ticketsubmitted.html')


if __name__ == '__main__':
    app.run(debug=True)