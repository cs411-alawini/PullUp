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

def closeConnection(connection):
    if connection.is_connected():
        connection.close()
        print("MySQL connection closed")


def sendSQLQuery(query):
    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        closeConnection(connection)
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        closeConnection(connection)
    return


@app.route("/")
def index():
  print("ACSC")
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
        print("got here")
        updated_email = request.form.get('email')
        updated_preferences = request.form.get('preferences')
        print(f"{updated_email} {updated_preferences}")
        query = f'''UPDATE UserProfile
                          SET Name = {updated_email}, Preferences = {updated_preferences}
                          WHERE UserID = {user}'''
        #sendSQLQuery(query)