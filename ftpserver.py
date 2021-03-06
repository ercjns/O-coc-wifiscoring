from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from threading import Thread
import os
import requests

import imp

secrets = imp.load_source('instanceconfig', os.path.join('instance', 'instanceconfig.py'))

class RelayHandler(FTPHandler):

    def on_file_received(self, file):
        def close_and_post(file):
            self.close() # disconnect FTP client. This unblocks SportSoftware
            # this does NOT log out of the FTP server.
            # "control connection timed out" at handler.timeout below

            hosts = get_hosts()
            event = os.path.split(os.path.dirname(file))[1]
            fn = os.path.basename(file)
            for h in hosts:
                try:
                    with open(file, 'r') as f:
                        url = h + '/api/event/' + event + '/results'
                        f = {'file': f}
                        r = requests.post(url, files=f)
                        print('Sent to {} with result {} {}'.format(h, r.status_code, r.text))
                except:
                    print('Failed to send {} to {}'.format(fn, h))
            return

        Thread(target=close_and_post(file)).start()
        return

def get_hosts():
    hostlist = []
    with open("hosts.txt", "r") as hosts:
        host = hosts.readline().rstrip()
        hostlist.append(host)
    return hostlist


def main():
    authorizer = DummyAuthorizer()
    authorizer.add_user(secrets.ADMIN_USER, secrets.ADMIN_PASS, "./ftp", perm="elradfmw")

    handler = RelayHandler
    handler.authorizer = authorizer

    handler.timeout = 30 # seconds. Default: 300

    server = FTPServer(('', 21), handler)
    server.serve_forever()

if __name__ == "__main__":
    main()