# Welcome to Human Scrum
## Project Description
The objective of this project is to develop an IT help desk ticket system designed to streamline the process of submitting and managing IT support requests. Users will be able to submit tickets for issues such as account assistance and repair requests.

## Key features of the system include:
  <h4>Automatic Ticket Assignment: </h4> The system will automatically assign tickets to individual IT staff members based on predefined criteria.
  <h4>Built-in Calendar:  </h4> A robust calendar feature to manage the high volume of tickets, ensuring efficient scheduling and tracking.
  <h4>Communication Tools:  </h4> Support for asynchronous messaging between ticket submitters and IT staff to enhance communication and resolution efficiency.
<h3></h3>
The system must be capable of running on multiple machines while accessing a central database. 

## Authors
- Aidan Doherty
- Anh Le
- Corey Telkitz

## Setup:
### How to run locally

Install [Python3](https://www.python.org/downloads/) and [pip](https://pypi.org/project/pip/), follow install instructions on respective webpages

Clone the forked repository to your local machine:
```bash
git clone https://github.com/aidandoherty01/CEN3031-Project.git
``` 
Change to the directory of the cloned repository:
```shell
cd CEN3031-Project
```
Then, type
```shell
python3 -m venv .venv
```
Next,
```shell
.venv/scripts/activate
```
Install
```shell
pip install -r requirements.txt
```
Run
```shell
Flask --app app run
```
Open http://127.0.0.1:5000 in browser
