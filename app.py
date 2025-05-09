from flask import Flask, render_template, request, redirect, url_for, flash, session
import joblib
import re
import string
import sqlite3
import random
import smtplib
from email.message import EmailMessage
from googletrans import Translator
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from werkzeug.utils import secure_filename
import PyPDF2
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure database
DATABASE = 'signup.db'

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Initialize translator
translator = Translator()

# Load model and vectorizer
try:
    model = joblib.load("model/model.sav")
    vectorizer = joblib.load("model/vectorizer.sav")
except Exception as e:
    print(f"Error loading model: {e}")

# Database connection helper
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Extract text from PDF
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# Create tables if they don't exist
def init_db():
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                mobile TEXT
            )
        """)
        db.commit()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Text cleaning function
def clean_text(text):
    text = text.lower()
    text = re.sub(r"\d+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Routes
@app.route("/")
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        name = request.form['name']
        mobile = request.form['mobile']
        password = generate_password_hash(request.form['password'])
        
        try:
            db = get_db()
            db.execute(
                'INSERT INTO users (username, email, password, name, mobile) VALUES (?, ?, ?, ?, ?)',
                (username, email, password, name, mobile)
            )
            db.commit()
            db.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'danger')
    
    return render_template('signup.html')

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    if request.method == "POST":
        # Check if a file was uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', 'warning')
                return redirect(url_for('index'))
            
            if file and allowed_file(file.filename):
                try:
                    # Read PDF file
                    pdf_text = extract_text_from_pdf(BytesIO(file.read()))
                    if not pdf_text:
                        flash('Could not extract text from PDF', 'danger')
                        return redirect(url_for('index'))
                    
                    user_input = pdf_text
                    input_type = 'PDF'
                except Exception as e:
                    flash(f'Error processing PDF: {str(e)}', 'danger')
                    return redirect(url_for('index'))
            else:
                flash('Only PDF files are allowed', 'warning')
                return redirect(url_for('index'))
        else:
            # Get text from form
            user_input = request.form['message']
            if not user_input.strip():
                flash('Please enter some text or upload a PDF', 'warning')
                return redirect(url_for('index'))
            input_type = 'Text'
        
        try:
            # Translate to English if needed
            translation = translator.translate(user_input, dest='en')
            cleaned_input = clean_text(translation.text)
        except Exception as e:
            print(f"Translation error: {e}")
            cleaned_input = clean_text(user_input)
        
        # Vectorize and predict
        try:
            vectorized_input = vectorizer.transform([cleaned_input])
            prediction = model.predict(vectorized_input)[0]
            return render_template('result.html', 
                                  prediction=prediction, 
                                  message=user_input,
                                  input_type=input_type)
        except Exception as e:
            print(f"Prediction error: {e}")
            flash('Error processing your request. Please try again.', 'danger')
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route("/notebook")
@login_required
def notebook():
    return render_template("notebook.html")

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)