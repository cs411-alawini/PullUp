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
        

def sendSQLQueryModify(query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    return




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
        return redirect(url_for('index'))

@app.route('/register_rep_old_org', methods=['POST'])
def register_rep_old_org():
    print('do sql stuff')
    #redirect to rep settings
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
@app.route('/login_rep')
def lg_rep():
    
    return render_template('login_rep.html')


@app.route('/user_dashboard/<username>')
def user_dashboard(username):
    return render_template('user_dashboard.html', username=username)

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