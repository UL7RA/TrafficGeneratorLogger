import time
import logging
import subprocess
import re
import mysql.connector
import os
from datetime import date

#Edit here to change the ports watched. Eg: (80, 30, 50)
#For only one element, make sure you put a comma after it, eg: (80,)
portsToWatch = (80,)
#retry interval (seconds) in case of inability to connect to database
retryInterval = 10
#number of consecutive queries succeded to send heartbeat log
heartbeatQueries = 200


def databaseConnect():
    #get database credentials from environment
    dbhost = os.environ.get("MYSQL_HOST")
    dbuser = os.environ.get("MYSQL_USER")
    dbpass = os.environ.get("MYSQL_PASSWORD")
    dbname = os.environ.get("MYSQL_DB")

    connected = False
    while not connected:
        try:
            db = mysql.connector.connect(host=dbhost, user=dbuser, password=dbpass, database = dbname)
            connected = True
            logging.info("Succesfully connected to database")
            return db
        except Exception as e:
            logging.critical("Connection to database failed, retrying in " + str(retryInterval) + " seconds: " + str(e))
            time.sleep(retryInterval)

def InputValidation():
    if len(portsToWatch) == 0:
        raise Exception("Need at least one port to watch!")
    for element in portsToWatch:
        if not isinstance(element,int):
            raise Exception("Only integers allowed for ports! Please change: " + element)
        if element < 0 or element > 65353:
            raise Exception("Port " + str(element) + " is out of range. Please pick a port between 0 and 65353")

#log formatter, writes the log into a logfile and also on the screen
logging.basicConfig(format="%(levelname)s @ %(asctime)s -> %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/log/interceptor.log"), logging.StreamHandler()])
#let's check the input for anomalies
InputValidation()
#start the producer, ignore output
producer = subprocess.Popen("./producer.sh", shell=True, stdout=subprocess.DEVNULL)


#craft tcpdump command
it = 0
command = "tcpdump dst port "
for portNum in portsToWatch:
    if it > 0:
        command += " or "
    command += str(portNum)
    it += 1

mydb = databaseConnect()
cursor = mydb.cursor()

logging.info("tcmdump command running: " + command)
logging.info("Starting connections logging to database. Will send heartbeats every " + str(heartbeatQueries) + " queries")

#run tcpdump
tcpdumpSub = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

#heartbeat initialization
queries = 0

#commence normal functioning
for line in tcpdumpSub.stdout:
    array = str(line).split(" ")
    timestamp = array[0][2:]
    #regex and string manipulation magic to isolate the host & port
    hostport = re.search(".[a-zA-Z0-9]*:$",array[4])
    port = hostport.group()[1:-1]
    host = array[4][:hostport.span()[0]]
    #logging.debug(host + " : " +port)

    #now to properly format the timestamp and add the date
    timestampSplit = timestamp.split(".")
    trueTime = str(date.today()) + " " + timestampSplit[0]
    
    #now push to database
    statement = "INSERT INTO connections (time, host, port) VALUES (%s, %s, %s)"

    values = (trueTime, host, port)
    try:
        cursor.execute(statement, values)
        mydb.commit()
        #I'd have used a function here, but ints are immutable, so
        queries += 1
        if queries == heartbeatQueries:
            logging.info("Heartbeat: " + str(queries) + " inserts succeeded")
            queries = 0

    except mysql.connector.Error as err:
        logging.error("Something went wrong inserting into the db: " + str(err))
        #err 2013: query failed, lost connection -> retry connection
        if err.errno == 2013:
            logging.critical("Connection to database lost. Retrying connection")
            mydb = databaseConnect()
            cursor = mydb.cursor()
            
    except Exception as e:
        logging.critical("Something went wrong inserting into the db: " + str(e))
        raise
    