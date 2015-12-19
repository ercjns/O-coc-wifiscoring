#Instructions:
#Download and install Python 2.7 or 2.8 (not 3.x)
#go to this folder and run: python get-pip.py
#add c:\Python27\Scripts\ to the environment path
#close and reopen command prompt
#cmd run pip install requests

import sys
import requests
import json

if __name__ == '__main__':
    host = sys.argv[1]
    method = sys.argv[2]
    arg = sys.argv[3]
    
    if method == 'iof3':
    # post sport software OE2012 I0F3 results file
        url = host + '/api/results/'
        f = {'file': open(arg, 'r')}
        #What should be in this header???
        #header = {'content-type': 'text/plain'}
        r = requests.post(url, files=f)
        print r.text

    if method == 'telemetry':
    # fake a remote punch call
        d = {}
        d['station'] = sys.argv[3]
        d['sicard'] = sys.argv[4]
        d['time'] = sys.argv[5]
        url = host + '/telemetry/' + d['station']
        header = {'content-type': 'text/json'}
        r = requests.post(url, headers=header, data=json.dumps(d))
        print r.text