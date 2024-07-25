# Important imports
import json
import os
import pickle
import random
import string

import cv2
import nltk
import numpy as np

#chatbot
from flask import (Flask, flash, redirect, render_template, request, session,url_for)
from flask_mysqldb import MySQL
from keras.models import load_model
from nltk.stem import WordNetLemmatizer
from PIL import Image
from werkzeug.security import check_password_hash, generate_password_hash

from app import app

nltk.download('popular')
lemmatizer = WordNetLemmatizer()

model = load_model('chatbot_model.h5')
intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
 

def clean_up_sentence(sentence):
    # tokenize the pattern - split words into array
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word - create short form for word
    sentence_words = [lemmatizer.lemmatize(
        word.lower()) for word in sentence_words]
    return sentence_words

# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence


def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0]*len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)
    return (np.array(bag))


def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list


def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if (i['tag'] == tag):
            result = random.choice(i['responses'])
            break
    return result


def chatbot_response(msg):
    ints = predict_class(msg, model)
    res = getResponse(ints, intents)
    return res


@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/tentang")

def tentang():
    return render_template("tentang.html")

@app.route("/ulasan")
def ulasan():
    return render_template("ulasan.html")

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return chatbot_response(userText)

#koneksi
app.secret_key = 'bebasapasaja'
app.config['MYSQL_HOST'] ='localhost'
app.config['MYSQL_USER'] ='root'
app.config['MYSQL_PASSWORD'] =''
app.config['MYSQL_DB'] ='jenis_kendaraan' 
mysql = MySQL(app)

#index
@app.route('/')
def indexx():
    if 'loggedin' in session:
        return render_template('indexx.html')
    flash('Harap Login dulu','danger')
    return redirect(url_for('login'))

#registrpasi
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
            flash('Login Gagal, Cek Password Anda Coba lagi', 'danger')
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
truck_cascade_src = 'app/static/cascade/truck.xml'

# Route to home page
@app.route("/", methods=["GET", "POST"])
def index():

	# Execute if request is get
	if request.method == "GET":
		full_filename =  'images/white_bg.jpg'
		return render_template("indexx.html", full_filename = full_filename)

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
		return render_template('indexx.html', full_filename = full_filename, pred = result)

# Main function
if __name__ == '__main__':
    app.run(debug=True)
