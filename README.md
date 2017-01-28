# O-coc-wifiscoring
Cascade Orienteering Club / WIOL wifi results, team scoring, and more

This system is *not* a replacement for meet management software. Functionality such as downloading results from an epunch stick and course checking are out of scope. This system is intended to provide functionality for meet participants and organizers in order to increase safety as well as excitement. 

## System Overview
This system is designed to be used during and after an Orienteering meet in support of the following scenarios:
* Competition results for meet participants
* Out-count for meet organizers and coaches
* Data from telemetry controls for announcing

At the core is a web service which provides both an API layer used mainly for data updates and a frontend layer for data consumption. This service will run on a Raspberry Pi 2 computer and be available to clients over a local WiFi network at meet locations (which have minimal cell coverage, if any).

#### API: Competition Results
```/api/event/<eventID>/results``` ```POST```
Send an IOF XML v3 file to the server. Data in this file overwrites and replaces existing data.

#### API: Telemetry controls
```/telemetry/<stationID>``` ```POST```
Send an individual punch event to the server. Header should include ```station```, ```sicard``` and ```time```

#### API: configuration
```/api/events``` ```PUT```
Send a tab separated file with event information: code, name, date, venue, description

```/api/event/<eventID>/classes``` ```PUT```
Send a comma separated file with class information for this event: class code, class name, scored, scoring method, multi-scored, multi-score method, team class, team classes

## Deployment
For brand new single WIOL events, the easiest deployment is to simply delete the database file and then repopulate the proper event information via the above APIs for event and class information. Once an event is set up, the server is ready to receive new data via the results API.

## License
This work is licensed under the [Creative Commons BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/) license. 
jQuery licensed from jQuery Foundation under the [MIT license here](https://jquery.org/license/)
socketio licensed from Guillermo Rauch under the [MIT license here](https://github.com/socketio/socket.io-client/blob/master/LICENSE)
sireader.py licensed from Gaudenz Steinlin and Simon Harston under the [GNU GPLv3 license here](http://www.gnu.org/licenses/gpl.html)


## Thanks!
Thanks to Mike Schuh, Gordon Walsh, Carl Walsh, Ing Uhlin, Bob Forgrave, and Gina Nuss for their ideas, expertise, and support.
Much of the code here is originally adapted from https://realpython.com/blog/python/python-web-applications-with-flask-part-i/

