from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return "Login Page - Placeholder"  # You can replace this with a proper login page later

@app.route('/signup')
def signup():
    return "Signup Page - Placeholder" # You can replace this with a proper signup page later

@app.route('/convert')
def convert():
    return "Convert Page - Placeholder" # You can replace this with a proper convert page later

if __name__ == '__main__':
    app.run(debug=True)