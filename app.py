from flask import Flask, render_template, url_for, request, redirect, flash, session, send_file, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import requests
import uuid
from model import process_image_to_3d
import tempfile
import shutil
import magic  # For file type validation
from dotenv import load_dotenv
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import random
import string
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MODEL_FOLDER'] = os.path.join(app.static_folder, 'models')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    reset_token = db.Column(db.String(6))
    reset_token_expiry = db.Column(db.DateTime)

    def __repr__(self):
        return 'User ' + str(self.id)
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'Contact {self.id}'

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_valid_gltf(file_path):
    """Check if the file is a valid GLTF/GLB by checking the magic number or extension."""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        return file_type in ['model/gltf-binary', 'application/octet-stream'] or file_path.endswith('.glb')
    except Exception as e:
        print(f"Error validating GLTF file: {str(e)}")
        return False

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
def about():
    return render_template('about.html')

@app.route('/faq')
def faq_section():
    return render_template('index.html')

@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email_or_username = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email_or_username).first() or User.query.filter_by(username=email_or_username).first()
        
        if user and user.check_password(password):
            session['user'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            error = 'Invalid email or password'
            return render_template('login.html', error=error)
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
        user = User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first()
        if user:
            return render_template('signup.html', message='User already exists')
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/convert', methods=['GET', 'POST'])
def convert():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        image_url = request.form.get('image_url')
        file = request.files.get('file')

        if not image_url and not file:
            return jsonify({'error': 'Please provide an image URL or upload a file'}), 400

        try:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(temp_path)
                result = process_image_to_3d(temp_path, is_url=False)
                os.remove(temp_path)
            elif image_url:
                result = process_image_to_3d(image_url, is_url=True)
            else:
                return jsonify({'error': 'Invalid input'}), 400

            print('fal_client result:', result)  # Log the full result for debugging

            # Process the result for 3D model
            output = {}
            # Try multiple possible keys for the model, including nested model_mesh.url
            possible_keys = ['model_url', 'model', 'glb_url', 'output', 'file_url', 'gltf_url']
            model_url = None
            for key in possible_keys:
                model_url = result.get(key)
                if model_url and isinstance(model_url, str) and model_url.startswith(('http://', 'https://')):
                    print(f"Found model URL in key '{key}': {model_url}")
                    break
            # Check for nested model_mesh.url
            if not model_url and 'model_mesh' in result and isinstance(result['model_mesh'], dict):
                model_url = result['model_mesh'].get('url')
                if model_url and isinstance(model_url, str) and model_url.startswith(('http://', 'https://')):
                    print(f"Found model URL in model_mesh.url: {model_url}")
                else:
                    model_url = None

            if model_url:
                # Download the model to static/models
                model_filename = f"model_{uuid.uuid4()}.glb"
                model_path = os.path.join(app.config['MODEL_FOLDER'], model_filename)
                os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)

                try:
                    response = requests.get(model_url, stream=True, timeout=10)
                    if response.status_code == 200:
                        # Save to a temporary file first
                        temp_model_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{model_filename}")
                        with open(temp_model_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        
                        # Validate the file
                        if is_valid_gltf(temp_model_path):
                            shutil.move(temp_model_path, model_path)
                            output['model_url'] = url_for('static', filename=f'models/{model_filename}')
                            print(f"Successfully saved model to {model_path}")
                        else:
                            print(f"Invalid GLTF file downloaded from {model_url}")
                            os.remove(temp_model_path)
                            output['model_url'] = ''
                    else:
                        print(f"Failed to download model from {model_url}: HTTP {response.status_code}")
                        output['model_url'] = ''
                except Exception as e:
                    print(f"Error downloading model from {model_url}: {str(e)}")
                    output['model_url'] = ''
            else:
                # Check if result contains binary data or a file
                if isinstance(result, bytes) or (isinstance(result, dict) and 'data' in result and isinstance(result['data'], bytes)):
                    model_filename = f"model_{uuid.uuid4()}.glb"
                    model_path = os.path.join(app.config['MODEL_FOLDER'], model_filename)
                    os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)
                    temp_model_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{model_filename}")
                    
                    try:
                        if isinstance(result, bytes):
                            model_data = result
                        else:
                            model_data = result['data']
                        
                        with open(temp_model_path, 'wb') as f:
                            f.write(model_data)
                        
                        if is_valid_gltf(temp_model_path):
                            shutil.move(temp_model_path, model_path)
                            output['model_url'] = url_for('static', filename=f'models/{model_filename}')
                            print(f"Successfully saved model from binary data to {model_path}")
                        else:
                            print("Invalid GLTF data in fal_client result")
                            os.remove(temp_model_path)
                            output['model_url'] = ''
                    except Exception as e:
                        print(f"Error saving model from binary data: {str(e)}")
                        output['model_url'] = ''
                else:
                    print('No valid model URL or data found in fal_client result:', result)
                    output['model_url'] = ''

            return jsonify({'success': True, 'result': output})

        except Exception as e:
            print(f"Error in /convert: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return render_template('convert.html')

@app.route('/models/<path:filename>')
def serve_model(filename):
    return send_from_directory(app.config['MODEL_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/submit-contact-form', methods=['POST'])
def submit_contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        try:
            contact = Contact(name=name,email=email, subject=subject, message=message)
            db.session.add(contact)
            db.session.commit()
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            flash('An error occurred while sending your message.', 'error')
            db.session.rollback()
        
        return redirect(url_for('contact_us'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate 6-digit OTP
            otp = ''.join(random.choices(string.digits, k=6))
            user.reset_token = otp
            user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)
            
            # Send email with OTP
            msg = Message('Password Reset Request',
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[email])
            msg.body = f'''To reset your password, use the following code:

{otp}

This code will expire in 15 minutes.

If you did not request a password reset, please ignore this email.
'''
            mail.send(msg)
            db.session.commit()
            
            flash('Password reset code has been sent to your email.', 'success')
            return render_template('verify_otp.html', email=email)
        else:
            flash('No account found with that email address.', 'error')
    
    return render_template('forgot_password.html')

@app.route('/verify-reset-token', methods=['POST'])
def verify_reset_token():
    email = request.form['email']
    otp = request.form['otp']
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('Invalid email address.', 'error')
        return redirect(url_for('forgot_password'))
    
    if not user.reset_token or not user.reset_token_expiry:
        flash('No reset code was requested.', 'error')
        return redirect(url_for('forgot_password'))
    
    if datetime.utcnow() > user.reset_token_expiry:
        flash('Reset code has expired. Please request a new one.', 'error')
        return redirect(url_for('forgot_password'))
    
    if user.reset_token != otp:
        flash('Invalid reset code.', 'error')
        return render_template('verify_otp.html', email=email)
    
    return render_template('reset_password.html', email=email, token=otp)

@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.form['email']
    token = request.form['token']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('reset_password.html', email=email, token=token)
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.reset_token or user.reset_token != token:
        flash('Invalid reset request.', 'error')
        return redirect(url_for('forgot_password'))
    
    if datetime.utcnow() > user.reset_token_expiry:
        flash('Reset code has expired. Please request a new one.', 'error')
        return redirect(url_for('forgot_password'))
    
    # Update password
    user.password = bcrypt.generate_password_hash(password).decode('utf-8')
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()
    
    flash('Your password has been reset successfully. Please log in with your new password.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)