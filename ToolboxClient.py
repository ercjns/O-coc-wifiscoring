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
    
    if method == 'iof3':
        ''' 
        post an iof3 resultList file to refresh the data on the server
        python ToolboxClient.py http://localhost iof3 testdata.xml 
        '''
        post_iof3_resultList(host, sys.argv[3])
    
    elif method == 'monitor':
        ''' 
        monitor a folder for new results and post them
        usage: python ToolboxClient.py http://localhost monitor ./results_go_here 
        '''
        poll_for_results(sys.argv[3])
        
    elif method == 'telemetry':
        ''' 
        mimic a call coming in from a remote punch box
        python ToolboxClient.py http://localhost telemetry 17 99999 "09:42:17" 
        '''
        d = {}
        d['station'] = sys.argv[3]
        d['sicard'] = sys.argv[4]
        d['time'] = sys.argv[5]
        url = host + '/telemetry/' + d['station']
        header = {'content-type': 'text/json'}
        r = requests.post(url, headers=header, data=json.dumps(d))
        print r.text

def post_iof3_resultList(host, file):
    # post sport software IOFv3 results file
    url = host + '/api/results/'
    f = {'file': open(file, 'r')}
    #What should be in this header???
    #header = {'content-type': 'text/plain'}
    r = requests.post(url, files=f)
    return r.text
            
def poll_for_results(dir):
    lastUpdate = None
    while True:
        dircontents = os.listdir(dir)
        if len(dircontents) == 1:
            # TODO actually get the right file rather than picking the only one!
            fn = os.path.join(dir, dircontents[0])
            t = os.path.getmtime(fn)
            if t > lastUpdate:
                print "found new file, posting"
                postToMeetWeb(fn)
                lastUpdate = t
            else:
                print "no new file"
        print "sleeping, brb"
        for i in range(60):
            time.sleep(1)