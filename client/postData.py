#Instructions:
#Download and install Python 2.7 or 2.8 (not 3.x)
#go to this folder and run: python get-pip.py
#add c:\Python27\Scripts\ to the environment path
#close and reopen command prompt
#cmd run pip install requests


#POST an XML file

import sys
import requests
import json

if __name__ == '__main__':
    host = sys.argv[1]
    method = sys.argv[2]
    arg = sys.argv[3]

##### ORGS API #####

    if method == 'orgs':
    #posts any new orgs (currently skips existing)
        url = host + '/api/orgs'
        with open(arg, 'r') as f:
            clubs = json.load(f)
        header = {'content-type': 'text/json'}
        r = requests.post(url, headers=header, data=json.dumps(clubs))
        print r.text

    elif method == "putorg":
    #updates specified org
        d = {}
        l = arg.split(None, 1)
        d['abbr'] = l[0]
        d['name'] = l[1]
        url = host + '/api/orgs/' + d['abbr']
        header = {'content-type': 'text/json'}
        r = requests.put(url, headers=header, data=json.dumps(d))
        print r.text

    elif method == "delorg":
    #remove the specified org
        abbr = arg
        url = host + '/api/orgs/' + abbr
        r = requests.delete(url)
        print r.text


##### RACES API #####

    elif method == 'races':
    #posts any new races (currently skips existing)
        url = host + '/api/races'
        with open(arg, 'r') as f:
            races = json.load(f)
        header = {'content-type': 'text/json'}
        r = requests.post(url, headers=header, data=json.dumps(races))
        print r.text

    elif method == "putrace":
    #updates specified race
        with open(arg, 'r') as f:
            races = json.load(f)
        for k in races.keys():
            a = races.pop(k)
            races[str(k)] = str(a)
            races['course'] = int(races['course'])
        url = host + '/api/races/' + str(races['code'])
        header = {'content-type': 'text/json'}
        r = requests.put(url, headers=header, data=json.dumps(races))
        print r.text

    elif method == "delrace":
    #remove the specified race
        abbr = arg
        url = host + '/api/races/' + abbr
        r = requests.delete(url)
        print r.text



##### RESULTS API ######

    elif method == 'oorg':
    #post oorg results file
        with open(arg) as infile:
            with open('snapshot.xml','w') as outfile:
                for line in infile:
                    if line.strip().startswith('<'):
                        outfile.write(line)

        url = host + '/api/downloads'
        f = {'file': open('snapshot.xml', 'r')}
        #What should be in this header???
        #header = {'content-type': 'text/plain'}
        r = requests.post(url, files=f)
        print r.text





###### OLD below this line, don't use ######    

    elif method == 'one':
        url = 'http://localhost:3000/api/setFinisher'
        f = {'file': open(filename, 'r')}
        r = requests.post(url, files=f)

    elif method == 'bulk':
        with open(filename) as infile:
            with open('bulkimport.xml','w') as outfile:
                for line in infile:
                    if line.strip().startswith('<'):
                        outfile.write(line)

        url = 'http://localhost:3000/api/refreshData'
        f = {'file': open('bulkimport.xml', 'r')}
        r = requests.post(url, files=f)



    if method == 'course':
        url = 'http://localhost:3000/api/addCourseInfo'
        with open(filename, 'r') as f:
            course = json.load(f)
        r = requests.post(url, json=course)
        print r.text
