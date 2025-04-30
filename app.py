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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MODEL_FOLDER'] = os.path.join(app.static_folder, 'models')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

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
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message='Invalid email or password')
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
        option = request.form.get('option')
        motion_effect = request.form.get('motion_effect')
        image_url = request.form.get('image_url')
        file = request.files.get('file')

        if not option:
            return jsonify({'error': 'Please select a 3D experience option'}), 400

        if option == 'animation' and not motion_effect:
            return jsonify({'error': 'Please select a motion effect for animation'}), 400

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

            # Process the result based on the selected option
            output = {}
            if option == 'animation':
                output['video_url'] = result.get('video_url', '')
            elif option == 'static':
                output['image_url'] = result.get('image_url', '')
            elif option == 'interactive':
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

if __name__ == '__main__':
    app.run(debug=True)