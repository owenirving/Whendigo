import mysql.connector
import glob
import json
import csv
from io import StringIO
import itertools
import hashlib
import os
import cryptography
from cryptography.fernet import Fernet
from math import pow
from flask import session
from datetime import timedelta, datetime

class database:

    def __init__(self, purge = False):

        # Grab information from the configuration file
        self.database       = 'db'
        self.host           = '127.0.0.1'
        self.user           = 'master'
        self.port           = 3306
        self.password       = 'master'
        self.tables         = ['users', 'events', 'invitees', 'availability']
        self.encryption     =  {   'oneway': {'salt' : b'averysaltysailortookalongwalkoffashortbridge',
                                                 'n' : int(pow(2,5)),
                                                 'r' : 9,
                                                 'p' : 1
                                             },
                                'reversible': { 'key' : '7pK_fnSKIjZKuv_Gwc--sZEMKn2zc8VvD6zS96XcNHE='}
                                }

    def query(self, query = "SELECT * FROM users", parameters = None):
        ''' Executes a query on the database and returns the results. '''

        cnx = mysql.connector.connect(host     = self.host,
                                      user     = self.user,
                                      password = self.password,
                                      port     = self.port,
                                      database = self.database,
                                      charset  = 'latin1'
                                     )


        if parameters is not None:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query, parameters)
        else:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query)

        # Fetch one result
        row = cur.fetchall()
        cnx.commit()

        if "INSERT" in query:
            cur.execute("SELECT LAST_INSERT_ID()")
            row = cur.fetchall()
            cnx.commit()
        cur.close()
        cnx.close()
        return row
        query = """select concat(col.table_schema, '.', col.table_name) as 'table',
                          col.column_name                               as column_name,
                          col.column_key                                as is_key,
                          col.column_comment                            as column_comment,
                          kcu.referenced_column_name                    as fk_column_name,
                          kcu.referenced_table_name                     as fk_table_name
                    from information_schema.columns col
                    join information_schema.tables tab on col.table_schema = tab.table_schema and col.table_name = tab.table_name
                    left join information_schema.key_column_usage kcu on col.table_schema = kcu.table_schema
                                                                     and col.table_name = kcu.table_name
                                                                     and col.column_name = kcu.column_name
                                                                     and kcu.referenced_table_schema is not null
                    where col.table_schema not in('information_schema','sys', 'mysql', 'performance_schema')
                                              and tab.table_type = 'BASE TABLE'
                    order by col.table_schema, col.table_name, col.ordinal_position;"""
        results = self.query(query)
        if nested == False:
            return results

        table_info = {}
        for row in results:
            table_info[row['table']] = {} if table_info.get(row['table']) is None else table_info[row['table']]
            table_info[row['table']][row['column_name']] = {} if table_info.get(row['table']).get(row['column_name']) is None else table_info[row['table']][row['column_name']]
            table_info[row['table']][row['column_name']]['column_comment']     = row['column_comment']
            table_info[row['table']][row['column_name']]['fk_column_name']     = row['fk_column_name']
            table_info[row['table']][row['column_name']]['fk_table_name']      = row['fk_table_name']
            table_info[row['table']][row['column_name']]['is_key']             = row['is_key']
            table_info[row['table']][row['column_name']]['table']              = row['table']
        return table_info

    def createTables(self, purge=False, data_path = 'flask_app/database/'):
        '''Creates database tables'''

        # Should be in order or creation
        if purge:
            for table in self.tables[::-1]:
                self.query(f"""DROP TABLE IF EXISTS {table}""")
            
        # Execute all SQL queries in the /database/create_tables directory.
        for table in self.tables:
            
            # Create each table using the .sql file in /database/create_tables directory.
            with open(data_path + f"create_tables/{table}.sql") as read_file:
                create_statement = read_file.read()
            self.query(create_statement)

            # Import the initial data
            try:
                params = []
                with open(data_path + f"initial_data/{table}.csv") as read_file:
                    scsv = read_file.read()            
                for row in csv.reader(StringIO(scsv), delimiter=','):
                    params.append(row)
            
                # Insert the data
                cols = params[0]; params = params[1:] 
                self.insertRows(table = table,  columns = cols, parameters = params)
            except:
                print('no initial data')

    def insertRows(self, table='table', columns=['x','y'], parameters=[['v11','v12'],['v21','v22']]):
        ''' Inserts rows into the database. '''

        # Check if there are multiple rows present in the parameters
        has_multiple_rows = any(isinstance(el, list) for el in parameters)
        keys, values      = ','.join(columns), ','.join(['%s' for x in columns])
        
        # Construct the query we will execute to insert the row(s)
        query = f"""INSERT IGNORE INTO {table} ({keys}) VALUES """
        if has_multiple_rows:
            for p in parameters:
                query += f"""({values}),"""
            query     = query[:-1] 
            parameters = list(itertools.chain(*parameters))
        else:
            query += f"""({values}) """                      
        
        insert_id = self.query(query,parameters)[0]['LAST_INSERT_ID()']         
        return insert_id


#######################################################################################
# AUTHENTICATION RELATED
#######################################################################################
    def createUser(self, email='me@email.com', password='password', name='name'):
        '''Creates a user and adds them to the database if they dont already exist'''
        # Check if email already exists in users
        if self.query("SELECT * FROM users WHERE email = %s", [email]):
            return {'success' : 0, 'message' : 'User already exists'}
        
        # Add user to users table
        try:
            encrypted = self.onewayEncrypt(password)
            columns = ['name', 'email', 'password']
            parameters = [[name, email, encrypted]]
            self.insertRows(table='users', columns=columns, parameters=parameters)
            return {'success' : 1}
        except Exception as e:
            return {'success' : 0,'message' : e}

    def authenticate(self, email='me@email.com', password='password'):
        '''Returns whether or not a given email/password combo exists in the database'''
        # Check database for user
        encrypted = self.onewayEncrypt(password)
        user = self.query("SELECT * FROM users WHERE email = %s AND password = %s", [email, encrypted])
        if user:
            return {'success': 0, 'message': 'User already exists'}
        else:
            return {'success': 1}

    def onewayEncrypt(self, string):
        ''' Perform a one-way encryption on a string using scrypt '''
        encrypted_string = hashlib.scrypt(string.encode('utf-8'),
                                          salt = self.encryption['oneway']['salt'],
                                          n    = self.encryption['oneway']['n'],
                                          r    = self.encryption['oneway']['r'],
                                          p    = self.encryption['oneway']['p']
                                          ).hex()
        return encrypted_string

    def reversibleEncrypt(self, type, message):
        ''' Perform a reversible encryption on a string using Fernet '''
        fernet = Fernet(self.encryption['reversible']['key'])
        
        if type == 'encrypt':
            message = fernet.encrypt(message.encode())
        elif type == 'decrypt':
            message = fernet.decrypt(message).decode()

        return message

#######################################################################################
# EVENT RELATED
#######################################################################################

    def createEvent(self, name='name', start_date = '2026-01-01', end_date = '2026-01-2', start_time = '08:00:00', end_time = '20:00:00', invitees = None, creator_id = None):
        '''Creates a event and adds it to the database if it doesnt already exist'''
        try:
            # Get creator id from session if not provided
            if not creator_id:
                creatorEmail = session['email']
                creator_id = self.query("SELECT user_id FROM users WHERE email = %s", [creatorEmail])[0]['user_id']

            # Add event to events table
            columns = ['creator_id', 'name', 'start_date', 'end_date', 'start_time', 'end_time']
            parameters = [[creator_id, name, start_date, end_date, start_time, end_time]]
            event_id = self.insertRows(table='events', columns=columns, parameters=parameters)
        
            # Add invitees to invitees table
            if invitees:
                invitee_list = invitees.split(',')
                for invitee in invitee_list:
                    invitee = invitee.strip()
                    columns = ['event_id', 'email']
                    parameters = [[event_id, invitee]]
                    self.insertRows(table='invitees', columns=columns, parameters=parameters)

            return {'success' : 1, 'event_id' : event_id}
        except Exception as e:
            return {'success' : 0, 'message' : e} 

    def availability(self, event_id, user, slots=None, status=None):
        ''' Sets the availability of a user for a given event. If slots is None, it will return the availability of the user. '''
        
        # Get user id from user
        user = self.query("SELECT user_id FROM users WHERE email = %s", [user])
        user = user[0]['user_id'] if user else None

        # Get availability mode
        if slots is None and status is None:
            results = self.query("SELECT date, time, status FROM availability WHERE event_id = %s AND user_id = %s", [event_id, user])
            return [{
                'slot_date': row['date'].strftime('%Y-%m-%d'),
                'slot_time': str(row['time']),
                'status': row['status']
            } for row in results]
        
        # Set availability mode
        else:
            for slot in slots:                
                if 'slot_date' in slot:
                    date = slot['slot_date']
                    time = slot['slot_time']
                
                # Clear slot
                self.query("DELETE FROM availability WHERE event_id = %s AND user_id = %s AND date = %s AND time = %s", [event_id, user, date, time])

                # Set slot
                columns = ['event_id', 'user_id', 'date', 'time', 'status']
                parameters = [[event_id, user, date, time, status]]
                self.insertRows(table='availability', columns=columns, parameters=parameters)

            return {'success': 1}
    
    def getGroupAvailability(self, event_id):
        ''' Get the availability of all users for a given event. '''

        results = self.query("SELECT date, time, status, COUNT(*) as count FROM availability WHERE event_id = %s GROUP BY date, time, status", [event_id])
        
        availability = {}
        for row in results:
            date = row['date'].strftime('%Y-%m-%d')
            time = str(row['time']).zfill(8)
            key = f"{date} {time}"
            
            if key not in availability:
                availability[key] = {'available': 0, 'maybe': 0, 'unavailable': 0}
            
            availability[key][row['status']] = row['count']
        
        return availability

    def calculateBestTime(self, event_id):
        ''' Calculate the best time for a given event. '''
        # Calculate best time sorting by availability count, with unavailability as a tiebreaker, sorted by time if still tied
        results = self.query("""
            SELECT date, time
            FROM availability
            WHERE event_id = %s
            GROUP BY date, time
            ORDER BY
                SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) DESC,
                SUM(CASE WHEN status = 'unavailable' THEN 1 ELSE 0 END) ASC,
                date ASC,
                time ASC
            LIMIT 1
        """, [event_id])
        
        if not results:
            return {'message': 'No availability submitted yet'}
        
        
        # Get best time and a second time for 30 mins later
        results = results[0]
        
        start = results['time']
        end = datetime(results['date'].year, results['date'].month, results['date'].day)
        end = end + timedelta(days=1)
        end = end + timedelta(seconds=start.seconds)
        end = end + timedelta(minutes=30)
        
        return {
            'date': results['date'].strftime('%Y-%m-%d'),
            'start': str(start).zfill(8),
            'end': str(end)
        }



