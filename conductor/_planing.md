# Live Results

## Goals
- Works at locations without internet connection
- Ideally can post to internet as well if we have an internet connection
- Low setup cost per meet
- Can easily be configured for different classes/courses
- Can easily be configured for different scoring schemes
- Leverage LostTime as much as possible.
  - Ok to use a version of LostTime running locally as a dependency. Don't re-write scoring code.
- Handle WIOL
- Handle Junior Nationals.

## Tech Design Dump
Lots of applicaitons working together here. This application is mostly serving as an orchestration layer. Moving files between other tools that provide various pieces of functionality.
Everything should be possible to be running on the same computer as the download computer, but likely it runs on another windows computer in the same network. 

### Data Flow
1. Results/Splits XML Files are exported from sportsoftware on a regular interval. They can either have the same name always, or be named with a timestamp. They can be sent to an FTP location, or can be saved to a network location visible by the (windows) computer where OE is running.
2. Orchestration app sends the XML files to LostTime (also running locally?) for generation of HTML files. Orchstration app ends up in possession of these files.
3. Orchestration app moves the HTML file to a location where they are able to be served by a web server - this could be on a local wifi network, or could involve getting the files uploaded to an internet location to serve on the internet.

### Unknowns
- How does an admin configure how to score any given class that shows up in an XML file?
- What is actually serving the html to end users? How is it configured for a given event?

## Setup
- Install python 3.11 on Windows: https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
- make sure you're using the new pip for this version of python (trick for me was to use `py` and not `python`)
- py -m pip install virtualenv
- New virtualenv in the conductor folder
- cd conductor
- py -m virtualenv venv-conductor
- venv-conductor\scripts\activate
Great, now I have a clean python 3.11 environment to work on.
not sure I trust the requirements file so going to try building it up from scratch.
looks like it was pretty clean, extras were just wheel and setuptools. cool.

installed requests library so I can do things with that too.

## two different pieces:
- web server: just start it, that's all for now. It serves a public folder on 8080. The Router will forward reqests to this location.
- conductor: watches a folder for a specific file(s), processes them, moves them to where they can be served.
- use a startup script to start both as separate processes.
- startup script should also start LostTime local as that's required.