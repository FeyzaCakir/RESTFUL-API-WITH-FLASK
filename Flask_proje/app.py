
from flask import Flask, redirect, url_for,render_template, request, session, flash
import requests

from firebase_admin import credentials, auth, firestore, initialize_app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length
import os 

# Firebase yapılandırması
cred = credentials.Certificate(r"C:\Users\feyza\Documents\Flask_proje\filmapi.json")
firebase = initialize_app(cred)
db = firestore.client()

app= Flask(__name__)

app.secret_key = "supersecretkey"  # Oturum için gerekli

# Kullanıcı Formları
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    submit = SubmitField('Register')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        print("Form validated!")
        try:
            user = auth.create_user(
                email=form.email.data,
                password=form.password.data,
                display_name=form.username.data
            )
            db.collection('users').document(user.uid).set({
                'username': form.username.data,
                'email': form.email.data
            })
            #oturum başlatma
            session['user'] = {'email': form.email.data, 'uid': user.uid}
            flash("User registered successfully!", 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        print("Form validation failed!")
    return render_template('register.html', form=form)
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # Firebase Authentication'dan kullanıcı kontrolü (şifre doğrulama)
            user = auth.get_user_by_email(form.email.data)
            # Oturum açma simülasyonu (Firebase, şifre doğrulama sunucusuyla birlikte çalışır)
            session['user'] = {'email': user.email, 'uid': user.uid}
            flash("Login successful!", 'success')
            return redirect(url_for('register'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('login.html', form=form)




@app.route('/dashboard',methods=['GET',"POST"])
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    else:
        flash("Please log in to access the dashboard.", 'warning')
        return redirect(url_for('login'))




@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully!", 'info')
    return redirect(url_for('login'))




#API
BASE_URL = "https://api.themoviedb.org/3/movie/popular"
TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjMjU3MDA3MmY1MmUyYzgwZDU4ZTU1OTA4NTBiM2ViYiIsIm5iZiI6MTczOTk2NzYzNy45MDgsInN1YiI6IjY3YjVjYzk1ZDI4ZTg3ZTBlNWUzYzViYiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Gm0lNlwENOflI0FEu5MqMGU6V29QuALTFM4cq6DWPno"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
    }
response = requests.get(BASE_URL, headers=headers)
data=response.json()

favori_films=[]

@app.route("/anasayfa", methods=["POST","GET"])
def anasayfa():
    return render_template("anasayfa.html",movies=data['results'])


@app.route("/ekle", methods=["POST","GET"])
def ekle():
    title = request.form.get('title')
    poster_path = request.form.get('poster_path')
    release_date = request.form.get('release_date')
    
    film = {
        "title": title,
        "poster_path": poster_path,
        "release_date": release_date
    }
    
    if title and film not in favori_films:
        favori_films.append(film)
    return redirect(url_for('anasayfa'))

  

@app.route("/sil", methods=["POST"])
def sil():
    title = request.form.get('title')
    
    global favori_films
    favori_films = [film for film in favori_films if film['title'] != title]
    return redirect(url_for('favoriler'))


@app.route("/favoriler", methods=["POST","GET"])
def favoriler():
    return render_template("favoriler.html", favori_films=favori_films)

@app.route("/film_detay/<int:film_id>", methods=["GET","POST"])
def film_detay(film_id):
    film = next((item for item in data['results'] if item["id"] == film_id), None)
    if film:
        return render_template("read.html", film=film)
    else:
        return "Film bulunamadı", 404

if __name__ == "__main__":
    app.run(debug=True,port=5000)

    