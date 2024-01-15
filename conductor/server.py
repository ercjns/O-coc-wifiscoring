# use waitress??
# just using the static python library for now

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PUBLIC_PATH='./web-public/'

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=PUBLIC_PATH, **kwargs)

def run(server_class=ThreadingHTTPServer, handler_class=CustomHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

run()