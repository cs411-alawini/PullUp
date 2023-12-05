import os
import pymysql
from flask import Flask, jsonify, render_template, request, url_for, redirect, flash
import mysql.connector
'''
ClOUD_SQL_CONNECTION_NAME: cs411pineapple:us-central1:pineapplezone
MySQL
InstanceID: pineapplezone
password: @[4OljDzhKbv*H$m
'''

# Replace these values with your GCP MySQL instance details
host = "34.123.222.214"
user = "root"
password = "password"
database = "team_pineapple"




# Create a connection to the MySQL instance

app = Flask(__name__)
app.secret_key = 'deez'

def connect():
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        return connection

    except mysql.connector.Error as e:
        print(f"Error: {e}")

connection = connect()

def closeConnection():
    if connection.is_connected():
        connection.close()
        print("MySQL connection closed")


def sendSQLQueryFetch(query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall() #list of tuples 
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        
def sendSQLQueryModifyV2(query, params):
    cursor = connection.cursor()
    try:
        cursor.execute(query, params)
        connection.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()


def sendSQLQueryModify(query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        return 1
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return 0
    finally:
        cursor.close()




@app.route("/")
def index():
  return render_template("index.html")

@app.route("/profile")
def profile():
  return render_template("profile.html")

@app.route('/list', methods=['GET'])
def list():
    connection = connect()
    cursor = connection.cursor()
    #1:Lists Organization Names with their highest rating for some event hosted.
    cursor.execute('''SELECT o.OrgName, sub.MaxRating
FROM Organization o
JOIN (
    SELECT e.OrgID, r.EventIdentifier, MAX(r.Rating) AS MaxRating
    FROM Events e
    JOIN Rating r ON e.EventID = r.EventIdentifier
    GROUP BY e.OrgID, r.EventIdentifier
) AS sub ON o.OrgID = sub.OrgID
ORDER BY o.OrgName, sub.MaxRating DESC
LIMIT 15;''')
    lis = []
    rows = cursor.fetchall()
    for row in rows:
        lis.append(row)
    closeConnection(connection)
    return lis


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if request.method == 'POST':
        name = request.form.get('username')
        email = request.form.get('email')
        preferences = request.form.get('preferences')
        query = f'''INSERT INTO UserProfile (Name, Preferences, Contact) VALUES ('{name}', '{preferences}', '{email}')'''
        print(query)
        sendSQLQueryModify(query)

        get_user_id_query = '''SELECT UserID FROM UserProfile ORDER BY UserID DESC LIMIT 1'''
        response = sendSQLQueryFetch(get_user_id_query)
        print(response[0][0])
        
        user_id = response[0][0]

        return redirect(url_for('give_user_id', user_id=user_id))

@app.route('/give_user_id/<user_id>', methods=['POST', 'GET'])
def give_user_id(user_id):

    return render_template('give_user_id.html', user_id=user_id)

@app.route('/register_rep_old_org', methods=['POST'])
def register_rep_old_org():
    if request.method == 'POST':

        orgId = request.form.get('orgId')
        repName = request.form.get('repName')
        repContact = request.form.get('repContact')

        # Validate if there is an existing org, if there is not redirect to signup page?
        query = f"""
        SELECT Organization.OrgID
        FROM Organization
        WHERE Organization.OrgID = {orgId}
        """
        rows = sendSQLQueryFetch(query=query)

        if not rows or len(rows) == 0:
            # no login exists
            return render_template('signup_rep_existing.html', error = 1)
        
        # login exists so add to rep // assuming repcontact string
        query = f"INSERT INTO Representative (OrgID, Name, Contact) VALUES ({orgId}, '{repName}', '{repContact}')"
        sendSQLQueryModify(query=query)

        # assuming we wanna pass something here? idk rep page
        return render_template('rep_setting.html')

@app.route('/register_rep_new_org', methods=['POST'])
def register_rep_new_org():
    if request.method == 'POST':
        org_name = request.form.get('orgName')
        org_type = request.form.get('orgType')
        org_location = request.form.get('orgLocation')
        rep_name = request.form.get('repName')
        rep_contact = request.form.get('repContact')

        cursor = connection.cursor()
        try:
            # Insert into Organization table if not exists
            insert_org_query = """
                                INSERT INTO Organization (OrgName, OrgType, Location, ContactInfo)
                                SELECT * FROM (SELECT %s AS OrgName, %s AS OrgType, %s AS Location, %s AS ContactInfo) AS tmp
                                WHERE NOT EXISTS (
                                    SELECT OrgName FROM Organization WHERE OrgName = %s
                                ) LIMIT 1;
                                """
            cursor.execute(insert_org_query, (org_name, org_type, org_location, rep_contact, org_name))

            if cursor.rowcount == 0:
                connection.rollback()
                flash("Organization/rep already exists", "warning")
                return redirect(url_for('rep_new_org'))

            org_id = cursor.lastrowid

            # Insert into Representative table if not exists
            insert_rep_query = """
                                INSERT INTO Representative (OrgID, Name, Contact)
                                SELECT * FROM (SELECT %s AS OrgID, %s AS Name, %s AS Contact) AS tmp
                                WHERE NOT EXISTS (
                                    SELECT 1 FROM Representative WHERE OrgID = %s AND Name = %s AND Contact = %s
                                );
                                """
            cursor.execute(insert_rep_query, (org_id, rep_name, rep_contact, org_id, rep_name, rep_contact))

            if cursor.rowcount == 0:
                connection.rollback()
                flash("Organization/rep already exists", "warning")
                return redirect(url_for('rep_new_org'))
            
            repId =  cursor.lastrowid
            connection.commit()
            flash(f"Organization and Representative Registered Successfully. Your RepID is {repId}", "success")
            return redirect(url_for('rep_new_org'))
        except Exception as e:
            connection.rollback()
            print(f"An error occurred: {e}")
            return f"An error occurred: {e}"
        finally:
            cursor.close()





@app.route('/login_user', methods=['POST'])
def login():
    username = request.form.get('username') 
    # validate here
    # if its not valid
    q = f"""
    SELECT UserProfile.UserID
    FROM UserProfile
    WHERE UserProfile.UserID = {username}
    """
    rows = sendSQLQueryFetch(q)
    if(rows is None):
        return redirect(url_for('index'))
    if(len(rows) == 0):
        # no login exists
        return redirect(url_for('signup'))
    else:
        return redirect(url_for('user_dashboard', username=username))
    
# @app.route('/login_rep', methods=['POST'])
# def login():
#     return redirect(url_for('user_dashboard', username="1"))
@app.route('/login_rep', methods=['POST', 'GET'])
def login_rep():
    if request.method == 'POST':
        repId = request.form.get('repId') 
        q = f"""
        SELECT Representative.RepID
        FROM Representative
        WHERE Representative.RepID = {repId}
        """
        rows = sendSQLQueryFetch(q)
        if rows is None or len(rows) == 0:
            return render_template('login_rep.html', error=1)
        else:
            return redirect(url_for('rep_dashboard', repID=repId)) # add the id as well
    else:
        return render_template('login_rep.html')


@app.route('/user_dashboard/<username>')
def user_dashboard(username):
    # Fetch user's name from the database
    query = "SELECT Name FROM UserProfile WHERE UserID = %s;"
    
    try:
        cursor = connection.cursor()
        cursor.execute(query, (username,))
        result = cursor.fetchone()  # Assuming username is unique and returns a single record
        user_name = result[0] if result else "Unknown"
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        user_name = "Unknown"
    finally:
        cursor.close()

    # Pass both username (UserID) and user's name to the template
    return render_template('user_dashboard.html', user_id=username, user_name=user_name)


@app.route('/user_settings/<username>')
def user_setting(username):
# Your logic here
    return render_template('user_settings.html', user_id=username)

@app.route('/update_user_name/<username>', methods=['POST'])
def update_user_name(username):
    new_name = request.form.get('newFullName')
    user_id = username

    # Use a parameterized query to prevent SQL injection
    query = """
            UPDATE UserProfile
            SET Name = %s
            WHERE UserID = %s;
            """
    try:
        # Assuming sendSQLQueryModify is adapted to handle parameterized queries
        sendSQLQueryModifyV2(query, (new_name, user_id))
        flash(f"Name updated successfully to '{new_name}' | UserId: {user_id}", "success")
    except Exception as e:
        # Log the exception for debugging
        print(f"Error during update: {e}")
        flash(f"Error Update Failed", "warning")

    return redirect(url_for('user_setting', username=user_id))

@app.route('/rep_dashboard/<repID>', methods=['POST', 'GET'])
def rep_dashboard(repID):
    orgId = "unknown"
    query = "SELECT OrgID FROM Representative WHERE RepID = %s;"

    print("trynig to get ORgiD")
    try:
        cursor = connection.cursor()
        cursor.execute(query, (repID,))
        result = cursor.fetchone()  # Assuming username is unique and returns a single record
        orgId = result[0] if result else "Unknown"
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        orgId = "Unknown"
    finally:
        cursor.close()
    if request.method == 'POST':
        data = request.get_json()
        eventName = data['eventName']
        location = data['location']
        selectedEventTypes = data['selectedEventTypes']

        # First query for representatives org id
        q = f"""
        SELECT OrgID
        FROM Representative
        WHERE RepID = {repID}
        """
        rows = sendSQLQueryFetch(q)
        orgId = rows[0][0]
        print(f'orgId: {orgId}')
        # Then Create Event
        query = f"INSERT INTO Events (OrgID, Location) VALUES ({orgId}, '{location}')"
        sendSQLQueryModify(query=query)

        # Find eventnum well a little sus but eh
        q = f"""
        SELECT EventID
        FROM Events
        WHERE OrgID = {orgId} AND Location = '{location}'
        """
        rows = sendSQLQueryFetch(q)
        eventID = rows[0][0]
        if (len(rows)) > 1:
            print('oh well')
        print(f'eventID: {eventID}')

        #Then for every tag create an eventTag, i guess they all have the same name
        for tag in selectedEventTypes:
            query = f"INSERT INTO EventTags (EventNum, Tag, EventName) VALUES ({eventID}, '{tag}', '{eventName}')"
            sendSQLQueryModify(query=query)

       


    if 'success' in request.args:
        print("success")
        return render_template('rep_setting.html', repID=repID, orgID = orgId ,succ=request.args['success'])
    elif 'badd' in request.args:
        print("bad")
        return render_template('rep_setting.html', repID=repID, badd=request.args['badd'])
    else:
        print("idk what this is")
        return render_template('rep_setting.html', repID=repID, orgID = orgId)

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup_user', methods=['POST'])
def signup_user():
    # Handle user signup logic here
    return render_template('profile.html')

@app.route('/signup_rep', methods=['POST'])
def signup_rep():
    # Handle representative signup logic here
    return render_template('signup_rep_one.html')

@app.route('/rep_new_org', methods=['POST', 'GET'])
def rep_new_org():
    # Handle representative signup logic here
    return render_template('signup_rep_neworg.html')

@app.route('/rep_old_org', methods=['POST'])
def rep_old_org():
    # Handle representative signup logic here
    return render_template('signup_rep_existing.html')

@app.route('/event_success/<repID>', methods=['GET'])
def event_sucess(repID):
    return redirect(url_for('rep_dashboard', repID=repID, success=True))


# forms cannot have DELETE events at this time so shitty work around
@app.route('/deleteEvent', methods=['GET', 'POST'])
def deleteEvent():
    if request.method == 'POST':
        eventID = request.form.get('eventId')
        repID = request.args['repID']
        query = f"""
        SELECT EventID
        FROM Events
        WHERE EventID = {eventID}
        """
        rows = sendSQLQueryFetch(query)
        if rows and len(rows) != 0:
            query = f"""
            DELETE FROM Events
            WHERE EventID = {eventID}
            """
            sendSQLQueryModify(query)
            print("era")
            return redirect(url_for('rep_dashboard', repID=repID, success=True))
    return redirect(url_for('rep_dashboard', repID=repID, badd=True))

@app.route('/dummy', methods=['GET'])
def dummy():
    q = f"""
        SELECT *
        FROM EventTags
        WHERE EventNum = 1001
        """
    rows = sendSQLQueryFetch(q)
    print(rows)
    return render_template('index.html')
