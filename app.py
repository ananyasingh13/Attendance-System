import base64
import numpy as np
import cv2
import os
from flask import Flask, render_template, request, jsonify
import math
from flask_mysqldb import MySQL
import bcrypt
import face_recognition
import pickle
from datetime import datetime
import mysql.connector
from mysql.connector import Error


app = Flask(__name__)

# MySQL Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "123",
    "database": "attendance"
}
# Function to establish a MySQL connection
def connect():
    """ Connect to MySQL database """
    conn = None
    try:
        conn = mysql.connector.connect(host='localhost',
                                       database='attendance',
                                       user='root',
                                       password='123')
        if conn.is_connected():
            print('Connected to MySQL database')

    except Error as e:
        print(e)

    finally:
        if conn is not None and conn.is_connected():
            conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/services.html')
def service():
    return render_template('services.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')



# @app.route('/login', methods=['POST'])
# def login():
#     if request.method == 'POST':
#         print("YESSSSSS")

#         username = request.form['username']
#         password = request.form['password']

#         cursor = mysql.connection.cursor()
#         cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
#         user = cursor.fetchone()
#         cursor.close()

#         if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
#             return jsonify({'status': 'success', 'message': 'Login successful!'})
#         else:
#             return jsonify({'status': 'error', 'message': 'Invalid username or password.'})

@app.route('/adduser.html')
def register():
    return render_template('adduser.html')

@app.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':
        print("Adding user")

        name = request.form['name']
        regno = request.form['regno']
        branch = request.form['branch']
        img = request.files['fileUpload']

        if img and name and regno and branch:
            file_path = "static/Images/"+regno+".png"
            img.save(file_path)

            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Establish a MySQL connection
            db_connection = mysql.connector.connect(**db_config)  # Establish the MySQL connection
            if db_connection.is_connected():
                print("Inside DB")
                cursor = db_connection.cursor()
                
                cursor.execute("INSERT INTO ATT (name, regno, branch, lastatt) VALUES (%s, %s, %s, %s)",(str(name), str(regno), str(branch), str(current_datetime)))
                
                db_connection.commit()
                cursor.close()
                db_connection.close()

                training()
                return jsonify({'status': 'success', 'message': 'Training Complete!'})
            else:
                return jsonify({'status': 'error', 'message': 'Database connection failed.'})


def training():
    folderPath = 'static/Images'
    pathList = os.listdir(folderPath)
    print(pathList)
    imgList = []
    studentIds = []
    for path in pathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        studentIds.append(os.path.splitext(path)[0])
    print("Encoding Started ...")
    encodeList = []
    for img in imgList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    encodeListKnownWithIds = [encodeList, studentIds]
    print("Encoding Complete")
    file = open("EncodeFile.p", 'wb')
    pickle.dump(encodeListKnownWithIds, file)
    file.close()
    print("File Saved")



@app.route('/liveatt.html')
def takeatt():
    return render_template('liveatt.html')



@app.route('/live', methods=['POST'])
def live():
    if request.method == 'POST':
        print("YESSSSSS")

        print("Loading Encode File ...")
        file = open('EncodeFile.p', 'rb')
        encodeListKnownWithIds = pickle.load(file)
        file.close()
        encodeListKnown, studentIds = encodeListKnownWithIds
        print("Encode File Loaded")

        data = request.get_json()

        img_data = data.get('imgData')

        img_data = img_data.split(',')[1]
        # Decode the base64 image data
        img_bytes = base64.b64decode(img_data)

        # Convert the bytes to a NumPy array
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)

        # Decode the NumPy array as an image
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:
                    print("Known Face Detected")
                    print(studentIds[matchIndex])
                    # Establish a MySQL connection
                    db_connection = mysql.connector.connect(**db_config)  # Establish the MySQL connection
                    if db_connection.is_connected():
                        cursor = db_connection.cursor()
                        cursor.execute("SELECT * FROM att")
                        a = cursor.fetchall()
                        for row in a:
                            if row[1]==studentIds[matchIndex]:
                                attendance_data = row
                        print(attendance_data)

                        #Retrieve the existing lastatt value for the specified regno
                        cursor.execute("SELECT lastatt FROM att WHERE regno = %s", (str(studentIds[matchIndex]),))
                        existing_lastatt = cursor.fetchone()

                        print(existing_lastatt)
                        
                        if existing_lastatt:
                            # Convert the existing_lastatt value to a datetime object
                            existing_lastatt_datetime = datetime.strptime(existing_lastatt[0], '%Y-%m-%d %H:%M:%S')
                            
                            # Calculate the time difference between the existing value and the current time
                            time_difference = datetime.now() - existing_lastatt_datetime

                            
                            if time_difference.total_seconds() > 30:
                                # Only update lastatt if the time difference is greater than 30 seconds
                                current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                update_query = "UPDATE att SET lastatt = %s WHERE regno = %s"
                                cursor.execute(update_query, (str(current_datetime), str(studentIds[matchIndex])))
                        db_connection.commit()  # Commit the changes to the database
                        cursor.close()  # Close the cursor
                        db_connection.close()

                        if attendance_data:
                            # Assuming you want to return the data as JSON
                            return jsonify({'status': 'success', 'attendance_data': attendance_data})
                        else:
                            return jsonify({'status': 'error', 'message': 'No data found for the given ID.'})
        return jsonify({'status': 'error', 'message': 'No face detected.'})
                    


if __name__ == '__main__':
    app.run(debug=True)