# Important imports
from app import app
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash

from flask import request, render_template, url_for
import cv2
import numpy as np
from PIL import Image
import string
import random
import os

#koneksi
app.secret_key = 'bebasapasaja'
app.config['MYSQL_HOST'] ='localhost'
app.config['MYSQL_USER'] ='root'
app.config['MYSQL_PASSWORD'] =''
app.config['MYSQL_DB'] ='smk_nusantara'
mysql = MySQL(app)

#indexx

@app.route('/')
def indexx
():
    if 'loggedin' in session:
        return render_template('indexx
		.html')
    flash('Harap Login dulu','danger')
    return redirect(url_for('login'))

#registrasi
@app.route('/registrasi', methods=('GET','POST'))
def registrasi():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        level = request.form['level']

        #cek username atau email
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_users WHERE username=%s OR email=%s',(username, email, ))
        akun = cursor.fetchone()
        if akun is None:
            cursor.execute('INSERT INTO tb_users VALUES (NULL, %s, %s, %s, %s)', (username, email, generate_password_hash(password), level))
            mysql.connection.commit()
            flash('Registrasi Berhasil','success')
        else :
            flash('Username atau email sudah ada','danger')
    return render_template('registrasi.html')

#login
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        #cek data username
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_users WHERE email=%s',(email, ))
        akun = cursor.fetchone()
        if akun is None:
            flash('Login Gagal, Cek Username Anda','danger')
        elif not check_password_hash(akun[3], password):
            flash('Login gagal, Cek Password Anda', 'danger')
        else:
            session['loggedin'] = True
            session['username'] = akun[1]
            session['level'] = akun[4]
            return redirect(url_for('index'))
    return render_template('login.html')

#logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    return redirect(url_for('login'))


# Adding path to config
app.config['INITIAL_FILE_UPLOADS'] = 'app/static/uploads'

car_cascade_src = 'app/static/cascade/cars.xml'
bus_cascade_src = 'app/static/cascade/Bus_front.xml'

# Route to home page
@app.route("/", methods=["GET", "POST"])
def index():

	# Execute if request is get
	if request.method == "GET":
		full_filename =  'images/white_bg.jpg'
		return render_template("indexx
		.html", full_filename = full_filename)

	# Execute if reuqest is post
	if request.method == "POST":

		image_upload = request.files['image_upload']
		imagename = image_upload.filename

		# generating unique name to save image
		letters = string.ascii_lowercase
		name = ''.join(random.choice(letters) for i in range(10)) + '.png'
		full_filename =  'uploads/' + name

		image = Image.open(image_upload)
		image = image.resize((450,250))
		image_arr = np.array(image)
		grey = cv2.cvtColor(image_arr,cv2.COLOR_BGR2GRAY)

	    #Cascade
		car_cascade = cv2.CascadeClassifier(car_cascade_src)
		cars = car_cascade.detectMultiScale(grey, 1.1, 1)

		bcnt = 0
		bus_cascade = cv2.CascadeClassifier(bus_cascade_src)
		bus = bus_cascade.detectMultiScale(grey, 1.1, 1)
		for (x,y,w,h) in bus:
			cv2.rectangle(image_arr,(x,y),(x+w,y+h),(0,255,0),2)
			bcnt += 1

		ccnt = 0
		if bcnt == 0:
			for (x,y,w,h) in cars:
				cv2.rectangle(image_arr,(x,y),(x+w,y+h),(255,0,0),2)
				ccnt += 1

		img = Image.fromarray(image_arr, 'RGB')
		img.save(os.path.join(app.config['INITIAL_FILE_UPLOADS'], name))

		# Returning template, filename, extracted text
		result = str(ccnt) + ' cars and ' + str(bcnt) + ' buses found'
		return render_template('indexx
		.html', full_filename = full_filename, pred = result)

# Main function
if __name__ == '__main__':
    app.run(debug=True)
