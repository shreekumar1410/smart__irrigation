from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
import cv2
import numpy as np
import torch
from ultralytics import YOLO
import argparse
import io
from PIL import Image
import time

app = Flask(__name__)

# Load your pre-trained YOLOv8 model here
model_path = 'Uploads/best.pt'
model = YOLO(model_path)  # Load the trained YOLOv8 model

app.secret_key = 'xyzsdfg'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'user-system'

mysql = MySQL(app)

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        user = cursor.fetchone()
        if user and user['password'] == password:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            message = 'Logged in successfully!'
            return redirect(url_for('home'))  # Redirect to home.html
        else:
            message = 'Please enter correct email / password!'
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO user (name, email, password) VALUES (%s, %s, %s)', (userName, email, password,))
            mysql.connection.commit()
            message = 'You have successfully registered!'
            return redirect(url_for('login'))  # Redirect to the login page
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)

# Route for the webpage with the upload form
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/weather')
def weather():
    return render_template('weather.html')

@app.route('/weed_detection')
def weed_detection():
    return render_template('weed_detection.html')

# Function to perform weed detection on an image
def detect_weeds_image(image_path):
    img = cv2.imread(image_path)
    frame = cv2.imencode('.jpg', cv2.UMat(img))[1].tobytes()
    image = Image.open(io.BytesIO(frame))
    results = model.predict(image, save=True)
    return results, 'weed occur' if results else 'weed not occur'

# Function to perform weed detection on a video
def detect_weeds_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('output.mp4', fourcc, 30.0, (frame_width, frame_height))
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, save=True)
        res_plotted = results[0].plot()
        out.write(res_plotted)
        cv2.waitKey(1)
    return results, 'weed occur' if results else 'weed not occur'  # Return results, not video_feed()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files['file']
    file_type = file.filename.split('.')[-1].lower()

    if file_type in {'png', 'jpg', 'jpeg', 'gif'}:
        # Save and detect weeds in the image
        image_path = 'static/uploads/' + file.filename
        file.save(image_path)
        results, prediction = detect_weeds_image(image_path)
        return render_template('image.html', file_path=image_path, results=results, prediction=prediction)
    elif file_type in {'mp4', 'mov', 'avi'}:
        # Save and detect weeds in the video
        video_path = 'static/uploads/' + file.filename
        file.save(video_path)
        results, prediction = detect_weeds_video(video_path)
        return render_template('video.html', file_path=video_path, results=results, prediction=prediction)
    else:
        return 'Invalid file type'

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/image')
def image():
    return render_template('image.html')

@app.route('/video')
def video():
    return render_template('video.html')

@app.route('/sensors')
def sensors():
    return render_template('sensors.html')

@app.route('/redirect')
def redirect_to_thingspeak():
    # Replace 'YOUR_CHANNEL_ID' and 'YOUR_API_KEY' with your actual ThingSpeak channel ID and API key
    channel_id = '2539016'
    api_key = 'JJ75NEO7W6EW18NP'
    
    # Construct the ThingSpeak channel URL with the API key
    channel_url = f'https://thingspeak.com/channels/{channel_id}?api_key={api_key}'
    
    # Redirect the user to the ThingSpeak channel URL
    return redirect(channel_url)
if __name__ == '__main__':
    app.run(debug=True)
