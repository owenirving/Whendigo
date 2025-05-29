# Author: Prof. MM Ghassemi <ghassem3@msu.edu>

#--------------------------------------------------
# Import Requirements
#--------------------------------------------------
import os
from flask import Flask
from flask_socketio import SocketIO
from flask_failsafe import failsafe
from dotenv import load_dotenv

load_dotenv()
socketio = SocketIO()

#--------------------------------------------------
# Create a Failsafe Web Application
#--------------------------------------------------
@failsafe
def create_app(debug=False):
    app = Flask(__name__)

    # This will prevent issues with cached static files
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.debug = debug
    # The secret key is used to cryptographically-sign the cookies used for storing the session data.
    app.secret_key = os.getenv('SECRET_KEY')
    # ----------------------------------------------

    # Create database
    from .utils.database.database import database
    db = database()
    db.createTables(purge=True)

    socketio.init_app(app)
        
    with app.app_context():
        from . import routes
        return app
