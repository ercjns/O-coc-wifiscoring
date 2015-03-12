# O-coc-wifiscoring
Cascade Orienteering Club / WIOL wifi results, team scoring, and more

### Design and Usage
Orienteering results in IOF ResultList format can be POSTed to the server either as individual results come in ("delta") or as a bulk update ("snapshot"). The server stores this data and presents results pages. A typical setup would be to host a local WiFi network at the meet, as many orienteering venues do not have reliable cell phone signal. 

Currently, the pages are designed specifically for Cascade OC's Winter Series meets, and as such the project also includes team scoring calculations for the WIOL (school league) competition.  

This software is not a replacement for meet management software.

### Technology Notes
The project is built in Node and uses a Mongo database via the mongoose package. This was my first project using node, and mongoose appeared to be a popular database engine for use with node, which heavily influenced that decision. In retrospect, a document based NoSQL database did not map well to the highly-relational data, so there are many opportunities for improvement in data storage. There are also plenty of opportunities for revised API design, what exists today is about the minimum for a successful COC meet, but there are many improvements to make the system more easily extensible.

### License
This work is licensed under the [Creative Commons BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/) license

### Thanks!
Thanks to Mike Schuh and Gordon Walsh for helping with system design and data load.  

