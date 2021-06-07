# Readme

## General approach:

Created using Docker 20.10.5\. Used a docker-compose file for ease of use.

- Traffic generator+interceptor: I chose to write a Python script that crafts a tcpdump command according to the ports specified in the script (after doing input validation), and runs it as a subprocess, iterating over the output lines as they become available. The traffic generator script is also run as a subprocess, and its output is discarded. I wrote a function that takes the database credentials from env vars and tries logging in. In case it fails, an exception is raised and gets logged (to the console and in a log file, created in a bind mounted folder for persistence and ease of access from the host computer), and retries after waiting a set amount of time (customizable). The tcpdump output gets processed using string manipulation and regex. In case inserting into the database fails because of a lost connection, it tries to reconnect. The script will log "heartbeats" after a set amount of inserts (also customizable).

- The database: uses a volume for persistence. Uses the credentials set in the docker-compose file. Runs commands from an init.sql file upon start (bind mounted), to set up the database in case it's the first run.

- The custom exporter: written in Python. As this was my first experience with scrapers and exporters, I took inspiration for the working principle from a similar project on github. No actual code was reused: [https://github.com/braedon/prometheus-mysql-exporter](https://github.com/braedon/prometheus-mysql-exporter)

The script uses the same database connect function as the traffic generator. It queries the database and counts every entry by host. The values are then written in a prometheus gauge.

- The non-custom exporter was just pointed towards the database container.

- The prometheus image was configured to scrape info from both exporters, and from itself. Uses a volume for persistence. The configuration file was bind mounted from the compose file.

## Test guide:

--- In the same location as the docker-compose.yml file, open a command window and type "<span style="color: #ff6600;">docker-compose build</span>" to build the traffic generator and the custom exporter containers. Retry the command if building any of the containers fails.

--- Type "<span style="color: #ff6600;">docker-compose up</span>" to start the application. It might take a while if the images the app needs are not already downloaded.

--- Watch the output of the command window:

For the interceptor: normal functionality is confirmed by the messages:

<span style="color: #3366ff;">interceptor | INFO @ 2021-04-09 13:52:14,138 -> Succesfully connected to database</span>

<span style="color: #3366ff;">interceptor | INFO @ 2021-04-09 13:52:14,138 -> tcmdump command running: tcpdump dst port 80</span>

<span style="color: #3366ff;">interceptor | INFO @ 2021-04-09 13:52:14,138 -> Starting connections logging to database. Will send heartbeats every 200 queries</span>

After a while, you will see the aforementioned heartbeat messages:

<span style="color: #3366ff;">interceptor | INFO @ 2021-04-09 13:56:48,727 -> Heartbeat: 200 inserts succeeded</span>

For the custom exporter: normal functionality:

<span style="color: #0000ff;">my_exporter | INFO @ 2021-04-09 13:52:14,088 -> Succesfully connected to database</span>

You can also check these logs in the corresponding "files" folder:

<span style="color: #008000;">./interceptor/files/interceptor.log</span>

<span style="color: #008000;">./pymysqlhostexporter/files/exporter.log</span>

--- In another command window, check that all containers are running using the command "<span style="color: #ff6600;">docker ps</span>". The output should look something like below. If you don't see the 5 entries corresponding to the 5 containers the app has, in the command window used for the docker-compose command, press CTRL-C to signal the app to stop, then run "<span style="color: #ff6600;">docker-compose up</span>" to restart everything. 

<table width="955" border="1">

<tbody>

<tr>

<td>CONTAINER ID</td>

<td>IMAGE</td>

<td>COMMAND</td>

<td>CREATED</td>

<td>STATUS</td>

<td>PORTS</td>

<td>Names</td>

</tr>

<tr>

<td>edf8d64028cd</td>

<td>mysql:8.0.23</td>

<td>docker-entrypoint.s…</td>

<td>9 minutes ago</td>

<td>Up 2 minutes</td>

<td>3306/tcp, 33060/tcp</td>

<td>mysql_database</td>

</tr>

<tr>

<td>79dc85e11386</td>

<td>challengedocker_interceptor</td>

<td>python ./intercepto…</td>

<td>9 minutes ago</td>

<td>Up 2 minutes</td>

<td></td>

<td>interceptor</td>

</tr>

<tr>

<td>7af37980a994</td>

<td>prom/prometheus</td>

<td>/bin/prometheus --c…</td>

<td>9 minutes ago</td>

<td>Up 2 minutes</td>

<td>0.0.0.0:9090->9090/tcp</td>

<td>prometheus</td>

</tr>

<tr>

<td>95d0348f4d9e</td>

<td>prom/mysqld-exporter</td>

<td>/bin/mysqld_exporter</td>

<td>9 minutes ago</td>

<td>Up 2 minutes</td>

<td>0.0.0.0:9104->9104/tcp</td>

<td>not_my_exporter</td>

</tr>

<tr>

<td>4cb594555936</td>

<td>challengedocker_pyexporter</td>

<td>python ./pymysqlhos…</td>

<td>9 minutes ago</td>

<td>Up 2 minutes</td>

<td>0.0.0.0:8000->8000/tcp</td>

<td>my_exporter</td>

</tr>

</tbody>

</table>

--- Prometheus is configured to be accessed on port 9090\. In a browser, access [http://localhost:9090](http://localhost:9090)

--- Go to Status - Targets - and ensure all 3 entries are Up.

--- Go to Graph, and in the window that says "Expression", input "<span style="color: #ff00ff;">mysql_global_status_commands_total</span>" and click Execute to see one of the metrics scraped from the non-custom exporter.

Switch to Graph view instead of Table for easier reading.

--- To see the metric scraped from the custom exporter, input "<span style="color: #ff00ff;">mysql_connections_by_host</span>" and Execute.

--- If you wish to see the metrics from the two exporters:

[http://localhost:9104/metrics](http://localhost:9104/metrics)

And for the custom exporter:

[http://localhost:8000/metrics](http://localhost:8000/metrics)

--- To shut everything down, in the command window where you ran the docker-compose commands, press CTRL-C to send the stop signal. If you wish to delete the persistent data of the prometheus and mysql containers - after shutting down the containers, input "<span style="color: #ff6600;">docker-compose down -v</span>". The log files of the traffic generator and of the custom exporter need to be deleted manually from their respective "files" folder. See above for their location.