import mysql.connector
import os
import time
import logging
from prometheus_client import start_http_server, Gauge

#time (in seconds) between updates
timeBetweenUpdates = 15
#retry interval (seconds) in case of inability to connect to database
retryInterval = 10


def databaseConnect():
    #get database credentials from environment
    dbhost = os.environ.get("MYSQL_HOST")
    dbuser = os.environ.get("MYSQL_USER")
    dbpass = os.environ.get("MYSQL_PASSWORD")
    dbname = os.environ.get("MYSQL_DB")
    #connect to database
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

#log formatter, writes the log into a logfile and also on the screen
logging.basicConfig(format="%(levelname)s @ %(asctime)s -> %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/log/exporter.log"), logging.StreamHandler()])

#Connect to database and prepare SQL statement
mydb = databaseConnect()
cursor = mydb.cursor()
statement = "SELECT host, count(*) FROM connections GROUP BY host;"

#starting http server
start_http_server(8000)
#prometheus metric here
metric = Gauge("mysql_connections_by_host","Number of connection attempts made, by host address",["host",])

while True:
    try:
        cursor.execute(statement)
        result = cursor.fetchall()
        mydb.commit()
        
    except mysql.connector.Error as err:
        logging.error("Something went wrong querying the db: " + str(err))
        #err 2013: query failed, lost connection -> retry connection
        if err.errno == 2013:
            logging.critical("Connection to database lost. Retrying connection")
            mydb = databaseConnect()
            cursor = mydb.cursor()

    except Exception as e:
        logging.critical("Something went wrong querying the db: " + str(e))
        raise

    for x in result:
        #print(x, flush=True)
        #this seems to work properly
        metric.labels(str(x[0])).set(x[1])
    #zzz
    time.sleep(timeBetweenUpdates)

