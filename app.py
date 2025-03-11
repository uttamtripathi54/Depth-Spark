# app.py file:
from flask import Flask, render_template, url_for, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import bcrypt

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret_key'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return 'User ' + str(self.id)
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/features')
def features_section():
    return render_template('index.html')

@app.route('/how-it-works')
def how_it_works_section():
    return render_template('index.html')

@app.route('/about')
def about_section():
    return render_template('index.html')

@app.route('/faq')
def faq_section():
    return render_template('index.html')

@app.route('/contact-us')
def contact_us_section():
    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email_or_username = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email_or_username).first() or User.query.filter_by(username=email_or_username).first()
        if user:
            if user.check_password(password):
                session['user'] = user.username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', message='Invalid password')
        else:
            return render_template('login.html', message='Invalid email')
    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            return render_template('signup.html', message='Passwords do not match')
        try:
            user = User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first()
            if user:
                return render_template('signup.html', message='User already exists')
        except:
            pass
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

if __name__ == '__main__':
    app.run(debug=True)