from flask import current_app as app
from flask import render_template, redirect, request, session, url_for, copy_current_request_context, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from .utils.database.database  import database
from werkzeug.datastructures   import ImmutableMultiDict
from pprint import pprint
import datetime
import json
import random
import functools
from . import socketio
db = database()


#######################################################################################
# AUTHENTICATION RELATED
#######################################################################################
# Require login
def login_required(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login", next=request.url))
        return func(*args, **kwargs)
    return secure_function

# Get user email from session
def getUser():
    return session['email'] if 'email' in session else 'Unknown'

# Render login page
@app.route('/login')
def login():
    return render_template('login.html')

# Remove user from session
@app.route('/logout')
def logout():
    session.pop('email', default=None)
    return redirect('/')

# Process user login and add them to session
@app.route('/processlogin', methods = ["POST","GET"])
def processLogin():
    # Get user input from the form
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
    email = form_fields['email']
    password = form_fields['password']

    # Check if user exists in users
    if db.query("SELECT * FROM users WHERE email = %s AND password = %s", [email, db.onewayEncrypt(password)]):
        session['email'] = email
        return json.dumps({'success': 1})

    # Return error message if username/password doesnt exist in db
    return json.dumps({'success' : 0, 'message' : 'Incorrect username or password'})

# process user account registration and add them to the session
@app.route('/processregister', methods = ["POST","GET"])
def processRegister():
    # Get user input from the form and save to db
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
    email = form_fields['email']
    password = form_fields['password']
    name = form_fields['name']

    # Check if user already exists in users
    if db.query("SELECT * FROM users WHERE email = %s", [email]):
        return json.dumps({'success' : 0, 'message' : 'Email already in use'})

    # Add user to db and add to session
    db.createUser(email=email, password=password, name=name)
    session['email'] = email
    return json.dumps({'success':1})

# Render registration page
@app.route('/register')
def create():
    return render_template('register.html')

#######################################################################################
# EVENT RELATED
#######################################################################################
# Render create event page
@app.route('/create')
@login_required
def home():
    return render_template('create.html', user = getUser())

# Process event creation and add event to db
@app.route('/processcreate', methods = ["POST","GET"])
def processCreate():
    # Get user input from the form and save to db
    form_fields = request.get_json()

    # make sure all required fields are filled
    required = ['name', 'start_date', 'end_date', 'start_time', 'end_time']
    for field in required:
        if not form_fields.get(field):
            return json.dumps({'success': 0, 'message': 'All events must have a name, start date, end date, start time, and end time.'})
        
    name = form_fields['name']
    start_date = form_fields['start_date']
    end_date = form_fields['end_date']
    start_time = form_fields['start_time']
    end_time = form_fields['end_time']
    invitees = form_fields['invitees']

    # Require times to be on the hour or half hour
    valid_times = [0, 30]
    val_start_time = datetime.datetime.strptime(start_time, '%H:%M')
    val_end_time = datetime.datetime.strptime(end_time, '%H:%M')
    if val_start_time.minute not in valid_times or val_end_time.minute not in valid_times:
        return json.dumps({'success': 0, 'message': 'Start and End times must be on the hour or half hour.'})

    # Add event to db
    event_id = db.createEvent(name=name, start_date=start_date, end_date=end_date, start_time=start_time, end_time=end_time, invitees=invitees)
    return json.dumps({'success':1, 'event_id': event_id['event_id']})

# Render event page
@app.route('/event/<int:event_id>')
@login_required
def displayEvent(event_id):
    # Get event
    event = db.query("SELECT * FROM events WHERE event_id = %s", [event_id])
    
    # Prevent access to non-existent events
    if not event:
        return redirect('/')
    event = event[0]
    
    # Convert times to strings
    event['start_time'] = str(event['start_time'])
    event['end_time'] = str(event['end_time'])
    
    # Convert dates to strings
    event['start_date'] = event['start_date'].strftime('%Y-%m-%d')
    event['end_date'] = event['end_date'].strftime('%Y-%m-%d')
    
    invitees = db.query("SELECT * FROM invitees WHERE event_id = %s", [event_id])

    # Redirect user away if they are not the creator or an invitee
    user = getUser()
    creator = db.query("SELECT email FROM users WHERE user_id = %s", [event['creator_id']])
    creator = creator[0]['email'] if creator else None
    invitee = db.query("SELECT email FROM invitees WHERE event_id = %s AND email = %s", [event_id, user])
    invitee = invitee[0]['email'] if invitee else None
    if user != creator and user != invitee:
        return redirect('/')

    return render_template('event.html', event=event, invitees=invitees, user=getUser())

# Render list of events page
@app.route('/events')
@login_required
def displayEvents():
    # Get all events for the user and set up creator email for each event
    user = getUser()
    created_events = db.query("""
        SELECT events.*, users.email AS creator_email FROM events
        JOIN users ON events.creator_id = users.user_id
        WHERE events.creator_id = (SELECT user_id FROM users WHERE email = %s)
    """, [user])
    invited_events = db.query("""
        SELECT events.*, users.email AS creator_email FROM events
        JOIN users ON events.creator_id = users.user_id
        WHERE events.event_id IN (SELECT event_id FROM invitees WHERE email = %s)
    """, [user])
    return render_template('events.html', events=created_events + invited_events, user=user)    

# Handle user availability for event
@app.route('/api/event/<int:event_id>/availability', methods=['POST', 'GET'])
@login_required
def handleAvailability(event_id):
    user = getUser()
    availability = db.availability(event_id, user)
    group_availability = db.getGroupAvailability(event_id)
    best_time = db.calculateBestTime(event_id)

    # Retrieve availability data
    if request.method == 'GET':
        return jsonify({
            'user_availability': availability,
            'group_availability': group_availability,
            'best_time': best_time
        })
    
    # Update availability data
    elif request.method == 'POST':
        data = request.get_json()
        slots = data.get('slots', [])
        status = data.get('status')
            
        db.availability(event_id, user, slots, status)
        group_availability = db.getGroupAvailability(event_id)
        best_time = db.calculateBestTime(event_id)
        socketio.emit('availability_update', {'event_id': event_id, 'group_availability': group_availability, 'best_time': best_time}, room=f'event_{event_id}', namespace='/event')
        return jsonify({'success': 1})

# Add user to event
@socketio.on('join_event', namespace='/event')
def joinEvent(data):
    event_id = data.get('event_id')
    join_room(f'event_{event_id}')

#######################################################################################
# DEFAULT ROUTE
#######################################################################################
# Redirect to event creation page if logged in else login page
@app.route('/')
def root():
    if 'email' in session:
        return redirect('/create')
    else:
        return redirect('/login')

#######################################################################################
# OTHER
#######################################################################################

@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r
