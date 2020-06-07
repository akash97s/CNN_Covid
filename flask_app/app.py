from flask import Flask, render_template, flash, redirect, url_for, logging, request, session
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
# imports for Ml model
import base64
import numpy as np
import io
from PIL import Image
import keras
from keras import backend as K
from keras.models import Sequential
from keras.models import load_model
from keras.preprocessing.image import ImageDataGenerator
from keras.preprocessing.image import img_to_array
from flask import jsonify

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin123'
app.config['MYSQL_DB'] = 'myflaskapp'
# to return data form sql as dictionary
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')

# register form
class RegisterForm(Form):
    user_name = StringField(u'User Name', [
    validators.DataRequired(),
    validators.Length(min=4, max=25)
    ])
    password  = PasswordField(u'Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Conifrm Password')

# user register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        user_name = form.user_name.data
        password = sha256_crypt.encrypt(str(form.password.data))
        #create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(username, password) VALUES(%s, %s)", (user_name, password))
        # commit to db
        mysql.connection.commit()
        #Close connection
        cur.close()
        flash('Registration successful', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form = form)

# user login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # get from fields
        user_name = request.form['username']
        password_candidate = request.form['password']

        # create DictCursor
        cur = mysql.connection.cursor();

        # get user by user_name
        result = cur.execute("SELECT * FROM users WHERE username = %s", [user_name])

        if result > 0 :
            # get stored hash
            data = cur.fetchone()
            password = data['password']
            # compare passwords
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session['logged_in'] = True
                session['username'] = user_name

                flash('You are now logged in', 'success')
                return redirect(url_for('services'))
                # app.logger.info('Password matched')
            else:
                error = 'Invalid login'
                return render_template('login.html', error = error )
            # close connection
            cur.close()
        else:
            error = 'Username not found'
            # app.logger.info('No user')
            return render_template('login.html', error = error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Pleae Login', 'danger')
            return redirect(url_for('login'))
    return wrap

# logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('login'))



# ML model

def get_model():
    global model
    model = load_model('basic_cnn_model.hdf5')
    print("Model loaded!")

def preprocess_image(image, target_size):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    return image

print(" * Loading Keras model...")
get_model()

def predict(message):
    print('!!!!  Inside predict model  !!!!')
    encoded = message['image']
    decoded = base64.b64decode(encoded)
    image = Image.open(io.BytesIO(decoded))
    processed_image = preprocess_image(image, target_size=(224, 224))

    prediction = model.predict(processed_image).tolist()

    response = {
        'prediction': {
            'Covid': prediction[0][0],
            'Normal': prediction[0][1]
        }
    }
    return jsonify(response)

# ML model ends


# services page where model runs
@app.route('/services', methods=['GET', 'POST'])
# restricts access via url
@is_logged_in
def services():
    if request.method == 'POST':
        message = request.get_json(force=True)
        if message['model'] == 'CNN':
            response = predict(message)
            print('!!!!! Image came to server  !!!!!')
            return response
        elif message['model'] == 'Model1':
            # response
            return null
        elif message['model'] == 'Model2':
            return null


    return render_template('services.html')




# for testing
@app.route('/others')
# restricts access via url
@is_logged_in
def others():
    return render_template('others.html')

# Python class for ML model
# return response and display in services page



if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
