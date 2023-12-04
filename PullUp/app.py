import os
import pymysql
from flask import Flask, jsonify, render_template, request, url_for, redirect
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
    print('do sql stuff')
    #redirect to rep settings
    return render_template('rep_setting.html')

@app.route('/register_rep_new_org', methods=['POST'])
def register_rep_new_org():
    print('do sql stuff')
    #redirect to rep settings
    return render_template('rep_setting.html')



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

@app.route('/user_dashboard/<username>')
def user_dashboard(username):
    return render_template('user_dashboard.html', user_id=username)

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

@app.route('/rep_new_org', methods=['POST'])
def rep_new_org():
    # Handle representative signup logic here
    return render_template('signup_rep_neworg.html')

@app.route('/rep_old_org', methods=['POST'])
def rep_old_org():
    # Handle representative signup logic here
    return render_template('signup_rep_existing.html')


