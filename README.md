# O-coc-wifiscoring
Cascade Orienteering Club / WIOL wifi results, team scoring, and more


## Goals
This branch will contain a complete re-write of the application using python's Flask web framework. The goal of this re-write is to encourage shared development in a common language (python) as well as increase stablity of the application when it is run on the target Raspberry Pi 2.

This system is *not* a replacement for meet management software. Functionality such as downloading results from an epunch stick and course checking are out of scope. This system is intended to provide functionality for meet participants and organizers in order to increase safety as well as excitement. 


## System Overview
This system is designed to be used during and after an Orienteering meet in support of the following scenarios:
* Competition results for meet participants
* Out-count for meet organizers and coaches
* Data from telemetry controls for announcing

At the core is a web service which provides both an API layer used mainly for data updates and a frontend layer for data consumption. This service will run on a Raspberry Pi 2 computer and be available to clients over a local WiFi network at meet locations (which have minimal cell coverage, if any).

#### Input: Competition Results
Cascade OC has adopted the OE2010 meet management software. During a meet, competition results will be transferred out of OE2010 via that software's automatic export capability. An API which allows this file to be ```PUT``` or ```POST```ed to the system will be made available.

#### Input: Telemetry Controls
Telemetry controls send individual e-punch data (SIcard and time) over wifi to a pre-configured machine and port. An API which allows this data to be ```PUT``` or ```POST```ed to the system will be made available.

#### Output: Individual Results
(detailed design tbd)

#### Output: Team Results
(detailed design tbd)

#### Output: Out Count
By including telemetry on the start box, organizers can know how many individuals are on the course without interrupting the epunch download line in order to read data from the start box. (detailed design tbd)


## License
This work is licensed under the [Creative Commons BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/) license. 
jQuery licensed by jQuery Foundation under the [MIT license here](https://jquery.org/license/)
socketio licensed by Guillermo Rauch under the [MIT license here](https://github.com/socketio/socket.io-client/blob/master/LICENSE)
sireader.py licensed by Gaudenz Steinlin and Simon Harston under the [GNU GPLv3 license here](http://www.gnu.org/licenses/gpl.html)


## Thanks!
Thanks to Mike Schuh, Gordon Walsh, Carl Walsh, Ing Uhlin, Bob Forgrave, and Gina Nuss for their ideas, expertise, and support.
Much of the code here is originally adapted from https://realpython.com/blog/python/python-web-applications-with-flask-part-i/

