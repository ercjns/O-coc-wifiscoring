# O-coc-wifiscoring
Live-updating results for orienteering races on a local wifi network with no internet dependency

This system is intended to provide functionality for meet participants and organizers in order to increase excitement and safety and is *not* a replacement for meet management / course checking software.

# Usage
## Cascade OC WIOL meets
1. Set up the hardware. 
    1. Set up epunch computers as normal except for the network cable. Instead of linking them directly, run a network cable from each epunch computer to the wifi router. 
    2. Run a network cable from the Pi to the router. 
    3. Power the router. 
    4. Power the pi (micro usb).
2. Set up the web server. 
    1. Navigate to wifi.cascadeoc.org/admin/events. 
    2. Click the "delete event" button next to any events in the list. 
    3. Input info for today's meet and click "new WIOL meet". The new meet should show up in the list. Leave this page open, you'll need it.
3. Set up SportSoftware. 
    1. Open the event and open a preliminary results by class window. 
    2. In the left sidebar, click automatic report. 
    3. Set the refresh interval to 5:00, check export, make sure display changed classes only is *not* checked, and click start. 
    4. Select XML V.3.x as the file type, and check the boxes for "unique filenames by timestamp" and "upload files to web". Click OK.
    5. On the upload dialog, the website should be `wifi.cascadeoc.org` and the folder is the event code from the admin view. It looks like `YYYY-MM-DD-N`.
    6. Input the username and password and click upload
    7. You'll get a warning asking to create a folder. Click ok.
    8. Minimize this window inside sport software (so that it isn't accidentally closed)

## General

### Set up an Event
Setting up an event consists of creating an event and creating event classes that need to be scored.

```/api/events```

```PUT``` Send a tab separated file with event information: code, name, date, venue, description

```/api/event/<eventID>/classes```

```PUT``` Send a comma separated file with class information for this event: class code, class name, scored, scoring method, multi-scored, multi-score method, team class, team classes

### Update event results

```/api/event/<eventID>/results```

```POST``` Send an IOF XML v3 file to the server with the complete results. The server will process based on class information provided, and serve new results when processing is complete.

### Telemetry controls
There is preliminary support for telemetry controls, which can be helpful for announcing or monitoring an out-count during a meet.

```/telemetry/<stationID>```

```GET``` Displays a webpage with all punch events for this si station.

```POST``` Send an individual punch event to the server. Header should include ```station```, ```sicard``` and ```time```.


# Technical Notes
### Router Configuration
The deployment for Cascade OC uses a router with DD-WRT installed. The epunch computers and the pi all have static IP addresses. There is a DNSmasq configuration within DD-WRT that sends traffic for `wifi.cascadeoc.org` to the pi's IP address.

### SportSoftware "Upload to Web"
The "Upload to web" feature creates an FTP request to send each of the files, *not* an HTTP POST request. For Cascade OC, there is an python based FTP server running on the pi to handle these requests. When the FTP server recieves a file, it uses the python requests library to send the file to the web server via HTTP POST.

### SportSoftware Export
A previous iteration of this system instead used a combination of a samba file-share on the pi and a script monitoring that folder for changes to detect new files to send to the webserver. (Sport-Software can save the xml file to a windows-viewable network location.) The monitoring folder was implemented on the pi for the convienence of keeping all the code on the pi rather than having code running on an epunch computer.


## License
This work is licensed under the [Creative Commons BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/) license. 
jQuery licensed from jQuery Foundation under the [MIT license here](https://jquery.org/license/)
socketio licensed from Guillermo Rauch under the [MIT license here](https://github.com/socketio/socket.io-client/blob/master/LICENSE)
sireader.py licensed from Gaudenz Steinlin and Simon Harston under the [GNU GPLv3 license here](http://www.gnu.org/licenses/gpl.html)

## Thanks!
Thanks to Mike Schuh, Gordon Walsh, Carl Walsh, Ing Uhlin, Bob Forgrave, and Gina Nuss for their ideas, expertise, and support.
Much of the code here is originally adapted from https://realpython.com/blog/python/python-web-applications-with-flask-part-i/

