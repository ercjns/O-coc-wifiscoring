#!/usr/bin/env python
import config
from coc_wifiscoring import app, db, socketio

if __name__ == "__main__":
    # Because we did not initialize Flask-SQLAlchemy with an application
    # it will use `current_app` instead.  Since we are not in an application
    # context right now, we will instead pass in the configured application
    # into our `create_all` call.
    db.create_all(app=app)
    socketio.run(app, host=0.0.0.0, port=config.PORT)
