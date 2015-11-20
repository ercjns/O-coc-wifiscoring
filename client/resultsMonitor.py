import sys
import os
import time
import requests
    
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
    
    if len(dircontents) > 0:
        dircontents.find

def postToMeetWeb(fn):
    host = 'http://192.168.103.14'
    api = '/api/downloads'
    url = host + api
    f = {'file': open(fn, 'r')}
    try:
        r = requests.post(url, files=f)
        print r.text
    except:
        print "post failed"
    return
  
if __name__ == "__main__":
    args = sys.argv[1:]
    poll_for_results(args[0])

    
