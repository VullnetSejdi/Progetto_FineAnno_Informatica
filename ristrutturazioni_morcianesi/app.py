"""
Ristrutturazioni Morcianesi - Applicazione Web
---------------------------------------------
Applicazione Flask per la gestione del sito web aziendale,
sistema di autenticazione utenti e chat preventivi con AI.
"""

import os
import re
import secrets
import sqlite3
import requests
import json
import time
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for, flash, 
    session, g, jsonify, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from functools import wraps

# =============== DECORATORI PER L'AUTENTICAZIONE ===============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        
        # Verifica se l'utente è un admin
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
        user_data = cursor.fetchone()
        
        if not user_data or user_data['role'] != 'admin':
            flash('Accesso non autorizzato. Solo gli amministratori possono visualizzare questa pagina.', 'danger')
            return redirect(url_for('home'))
            
        return f(*args, **kwargs)
    return decorated_function

# =============== CONFIGURAZIONE DELL'APPLICAZIONE ===============

app = Flask(__name__)
app.config.update(
    SECRET_KEY='Gobettidegasperiano',
    DATABASE=os.path.join(app.root_path, 'database.db'),
    EMAIL_HOST='smtp.gmail.com',
    EMAIL_PORT=587,
    EMAIL_USER='ristruttura.morcianesi.verifica@gmail.com',
    EMAIL_PASSWORD='mgtcrlketbprtoin',
    OPENROUTER_API_KEY="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",
    OPENROUTER_URL="https://openrouter.ai/api/v1/chat/completions",
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='ristruttura.morcianesi.verifica@gmail.com',
    MAIL_PASSWORD='mgtcrlketbprtoin',
    MAIL_DEFAULT_SENDER='ristruttura.morcianesi.verifica@gmail.com',
    ADMIN_EMAIL='admin@ristrutturazionimorcianesi.it',
    DEBUG=True
)

csrf = CSRFProtect(app)
mail = Mail(app)  # Inizializzazione dell'oggetto mail

# =============== DATABASE E CONNESSIONE ===============

def get_db():
    """Stabilisce e restituisce una connessione al database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Chiude la connessione al database alla fine della richiesta."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Inizializza il database con le tabelle necessarie."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('init-db')
def init_db_command():
    """Comando da terminale per creare le tabelle."""
    init_db()
    print('Database inizializzato con successo.')

def safe_get(row, key, default=None):
    """Helper per ottenere valori da sqlite3.Row con default per colonne mancanti."""
    try:
        return row[key]
    except (IndexError, KeyError):
        return default

# =============== FUNZIONI PER L'INVIO DI EMAIL ===============

def send_email(to_email, subject, html_content):
    """Funzione generica per inviare email."""
    msg = MIMEMultipart()
    msg['From'] = app.config['EMAIL_USER']
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP(app.config['EMAIL_HOST'], app.config['EMAIL_PORT'])
        server.starttls()
        server.login(app.config['EMAIL_USER'], app.config['EMAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")
        return False

def send_verification_email(user_email, username, token):
    """Invia un'email di verifica all'utente."""
    verification_url = url_for('verify_email', token=token, _external=True)
    subject = 'Verifica il tuo account Ristrutturazioni Morcianesi'
    
    html_content = f'''
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h2 style="color: #1B9DD1;">Benvenuto su Ristrutturazioni Morcianesi, {username}!</h2>
            <p>Grazie per esserti registrato. Per completare la registrazione, verifica il tuo indirizzo email cliccando sul link qui sotto:</p>
            <p>
                <a href="{verification_url}" 
                   style="display: inline-block; padding: 10px 20px; background-color: #1B9DD1; color: #ffffff; text-decoration: none; border-radius: 5px;">
                   Verifica il tuo account
                </a>
            </p>
            <p>Oppure copia questo link nel tuo browser:</p>
            <p style="word-break: break-all; color: #666;">{verification_url}</p>
            <p><strong>Nota:</strong> Il link scadrà tra 24 ore.</p>
            <p>Se non hai richiesto questa registrazione, ignora questa email.</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="font-size: 0.9em; color: #777;">Cordiali saluti,<br>Il team di Ristrutturazioni Morcianesi</p>
        </div>
    </body>
    </html>
    '''
    
    return send_email(user_email, subject, html_content)
    
def send_reset_password_email(user_email, username, token):
    """Invia un'email per il reset della password."""
    reset_url = url_for('reset_password', token=token, _external=True)
    subject = 'Reset Password - Ristrutturazioni Morcianesi'
    
    html_content = f'''
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h2 style="color: #1B9DD1;">Reset Password - Ristrutturazioni Morcianesi</h2>
            <p>Ciao {username},</p>
            <p>Hai richiesto il reset della tua password. Clicca sul link qui sotto per impostare una nuova password:</p>
            <p>
                <a href="{reset_url}" 
                   style="display: inline-block; padding: 10px 20px; background-color: #1B9DD1; color: #ffffff; text-decoration: none; border-radius: 5px;">
                   Reset Password
                </a>
            </p>
            <p>Oppure copia questo link nel tuo browser:</p>
            <p style="word-break: break-all; color: #666;">{reset_url}</p>
            <p><strong>Attenzione:</strong> Il link scadrà tra 1 ora.</p>
            <p>Se non hai richiesto il reset della password, ignora questa email.</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="font-size: 0.9em; color: #777;">Cordiali saluti,<br>Il team di Ristrutturazioni Morcianesi</p>
        </div>
    </body>
    </html>
    '''
    
    return send_email(user_email, subject, html_content)

# =============== MODELLO UTENTE ===============

class User:
    """Classe per la gestione degli utenti nel sistema."""
    
    def __init__(self, id=None, username=None, email=None, password_hash=None, is_verified=0, 
                 verification_token=None, token_created_at=None, reset_token=None, reset_token_created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_verified = is_verified
        self.verification_token = verification_token
        self.token_created_at = token_created_at
        self.reset_token = reset_token
        self.reset_token_created_at = reset_token_created_at

    @staticmethod
    def get_by_id(user_id):
        """Recupera un utente dal database tramite ID."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_verified=safe_get(user_data, 'is_verified', 0),
                verification_token=safe_get(user_data, 'verification_token'),
                token_created_at=safe_get(user_data, 'token_created_at'),
                reset_token=safe_get(user_data, 'reset_token'),
                reset_token_created_at=safe_get(user_data, 'reset_token_created_at')
            )
        return None

    @staticmethod
    def get_by_email(email):
        """Recupera un utente dal database tramite email."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_verified=safe_get(user_data, 'is_verified', 0),
                verification_token=safe_get(user_data, 'verification_token'),
                token_created_at=safe_get(user_data, 'token_created_at'),
                reset_token=safe_get(user_data, 'reset_token'),
                reset_token_created_at=safe_get(user_data, 'reset_token_created_at')
            )
        return None

    @staticmethod
    def get_by_token(token):
        """Recupera un utente dal database tramite token di verifica."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE verification_token = ?', (token,))
        user_data = cursor.fetchone()
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_verified=safe_get(user_data, 'is_verified', 0),
                verification_token=safe_get(user_data, 'verification_token'),
                token_created_at=safe_get(user_data, 'token_created_at')
            )
        return None

    @staticmethod
    def get_by_reset_token(token):
        """Recupera un utente dal database tramite token di reset password."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE reset_token = ?', (token,))
        user_data = cursor.fetchone()
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_verified=safe_get(user_data, 'is_verified', 0),
                reset_token=safe_get(user_data, 'reset_token'),
                reset_token_created_at=safe_get(user_data, 'reset_token_created_at')
            )
        return None

    def save(self):
        """Salva un nuovo utente nel database o aggiorna un utente esistente."""
        db = get_db()
        cursor = db.cursor()

        if self.id is None:
            # INSERT per un nuovo utente
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, is_verified, verification_token, token_created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (self.username, self.email, self.password_hash, self.is_verified, self.verification_token, self.token_created_at)
            )
            self.id = cursor.lastrowid
        else:
            # UPDATE per un utente esistente
            cursor.execute(
                'UPDATE users SET username = ?, email = ?, password_hash = ?, is_verified = ?, verification_token = ?, token_created_at = ? WHERE id = ?',
                (self.username, self.email, self.password_hash, self.is_verified, self.verification_token, self.token_created_at, self.id)
            )

        db.commit()
        return self
        
    def verify(self):
        """Imposta l'account come verificato."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'UPDATE users SET is_verified = 1, verification_token = NULL, token_created_at = NULL WHERE id = ?',
            (self.id,)
        )
        db.commit()
        self.is_verified = 1
        self.verification_token = None
        self.token_created_at = None
        return True

    def set_reset_token(self):
        """Imposta un token di reset password."""
        reset_token = secrets.token_urlsafe(32)
        token_created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'UPDATE users SET reset_token = ?, reset_token_created_at = ? WHERE id = ?',
            (reset_token, token_created_at, self.id)
        )
        db.commit()

        return reset_token

    def update_password(self, new_password):
        """Aggiorna la password dell'utente e rimuove il token di reset."""
        self.password_hash = generate_password_hash(new_password)

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_created_at = NULL WHERE id = ?',
            (self.password_hash, self.id)
        )
        db.commit()
        return True

# =============== VARIABILI GLOBALI PER IL TEMPLATE ===============

@app.context_processor
def inject_global_vars():
    """Aggiunge variabili globali a tutti i template."""
    user_id = session.get('user_id')
    user = None
    if user_id:
        user = User.get_by_id(user_id)
    return {
        'year': datetime.utcnow().year,
        'logged_in_user': user
    }

# =============== AUTENTICAZIONE E GESTIONE UTENTI ===============

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Gestisce la registrazione di un nuovo utente."""
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        errors = []

        # Validazione input
        if not username or len(username) < 3 or len(username) > 30:
            errors.append("Il nome utente deve avere tra 3 e 30 caratteri.")
        if not email:
            errors.append("L'email è richiesta.")
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            errors.append("L'indirizzo email non è valido.")
        if not password or len(password) < 12 or len(password) > 60:
            errors.append("La password deve avere tra 12 e 60 caratteri.")
        if password != confirm_password:
            errors.append("Le password non corrispondono.")

        if User.get_by_email(email):
            errors.append('Un account con questa email esiste già. Prova ad accedere.')

        if not errors:
            # Genera un token di verifica
            verification_token = secrets.token_urlsafe(32)
            token_created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Salva l'utente con il token
            hashed_password = generate_password_hash(password)
            new_user = User(
                id=None, 
                username=username, 
                email=email, 
                password_hash=hashed_password,
                is_verified=0,
                verification_token=verification_token,
                token_created_at=token_created_at
            )
            new_user.save()
            
            # Invia l'email di verifica
            if send_verification_email(email, username, verification_token):
                flash('Registrazione completata! Ti abbiamo inviato un\'email di verifica. Per favore, controlla la tua casella di posta.', 'success')
            else:
                flash('Registrazione completata, ma non è stato possibile inviare l\'email di verifica. Prova a richiederne un\'altra.', 'warning')
            
            return redirect(url_for('login'))
        else:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', title='Registrazione',
                                  username_val=username, email_val=email)

    return render_template('register.html', title='Registrazione')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Gestisce il login degli utenti."""
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        errors = []

        if not email:
            errors.append("L'email è richiesta.")
        if not password:
            errors.append("La password è richiesta.")

        user = User.get_by_email(email)

        if not errors:
            if not user:
                errors.append('Accesso non riuscito. Controlla email e password.')
            elif not check_password_hash(user.password_hash, password):
                errors.append('Accesso non riuscito. Controlla email e password.')
            elif not user.is_verified:
                errors.append('Il tuo account non è stato ancora verificato. Per favore, controlla la tua email o richiedi una nuova email di verifica.')
        
        if not errors and user and user.is_verified:
            # Login riuscito
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_username'] = user.username
            flash('Accesso effettuato con successo!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            for error in errors:
                flash(error, 'danger')
            return render_template('login.html', title='Accesso', email_val=email)

    return render_template('login.html', title='Accesso')

@app.route('/verify/<token>')
def verify_email(token):
    """Verifica l'email dell'utente tramite token."""
    user = User.get_by_token(token)
    
    if not user:
        flash('Token di verifica non valido o scaduto.', 'danger')
        return redirect(url_for('login'))
    
    # Controlla se il token è scaduto (24 ore)
    if user.token_created_at:
        token_date = datetime.strptime(user.token_created_at, '%Y-%m-%d %H:%M:%S')
        if (datetime.now() - token_date) > timedelta(hours=24):
            flash('Il token di verifica è scaduto. Richiedi una nuova email di verifica.', 'danger')
            return redirect(url_for('resend_verification'))
    
    # Verifica l'account
    user.verify()
    flash('Account verificato con successo! Ora puoi accedere.', 'success')
    return redirect(url_for('login'))

@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Permette di richiedere un nuovo link di verifica."""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.get_by_email(email)
        
        if not user:
            flash('Email non trovata.', 'danger')
            return render_template('resend_verification.html')
        
        if user.is_verified:
            flash('Questo account è già verificato. Puoi effettuare il login.', 'info')
            return redirect(url_for('login'))
        
        # Genera un nuovo token
        verification_token = secrets.token_urlsafe(32)
        token_created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Aggiorna l'utente con il nuovo token
        user.verification_token = verification_token
        user.token_created_at = token_created_at
        user.save()
        
        # Invia la nuova email
        if send_verification_email(email, user.username, verification_token):
            flash('Email di verifica inviata! Controlla la tua casella di posta.', 'success')
        else:
            flash('Errore nell\'invio dell\'email. Riprova più tardi.', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('resend_verification.html')

@app.route('/logout')
def logout():
    """Gestisce il logout dell'utente."""
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_username', None)
    flash('Ti sei disconnesso.', 'info')
    return redirect(url_for('home'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Gestisce il recupero della password dimenticata."""
    if 'user_id' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.get_by_email(email)
        
        if user:
            reset_token = user.set_reset_token()
            if send_reset_password_email(user.email, user.username, reset_token):
                flash('Ti abbiamo inviato un\'email con le istruzioni per reimpostare la tua password.', 'success')
            else:
                flash('Si è verificato un errore nell\'invio dell\'email. Riprova più tardi.', 'danger')
        else:
            # Non rivelare che l'email non esiste (per sicurezza)
            flash('Se l\'indirizzo email è registrato, riceverai le istruzioni per reimpostare la password.', 'info')
            
        return redirect(url_for('login'))
        
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Gestisce il reset della password tramite token."""
    if 'user_id' in session:
        return redirect(url_for('home'))
        
    user = User.get_by_reset_token(token)
    
    if not user:
        flash('Il link per il reset della password non è valido o è scaduto.', 'danger')
        return redirect(url_for('forgot_password'))
    
    # Controlla se il token è scaduto (1 ora)
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT reset_token_created_at FROM users WHERE reset_token = ?', (token,))
    result = cursor.fetchone()
    
    if result and 'reset_token_created_at' in result:
        token_date = datetime.strptime(result['reset_token_created_at'], '%Y-%m-%d %H:%M:%S')
        if (datetime.now() - token_date) > timedelta(hours=1):
            flash('Il link per il reset della password è scaduto. Richiedi un nuovo link.', 'danger')
            return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        errors = []
        
        if not password or len(password) < 12 or len(password) > 60:
            errors.append("La password deve avere tra 12 e 60 caratteri.")
        if password != confirm_password:
            errors.append("Le password non corrispondono.")
            
        if not errors:
            user.update_password(password)
            flash('La tua password è stata reimpostata con successo! Ora puoi accedere.', 'success')
            return redirect(url_for('login'))
        else:
            for error in errors:
                flash(error, 'danger')
    
    return render_template('reset_password.html', token=token)

# =============== PAGINE PRINCIPALI ===============

@app.route('/preventivo-form')
def preventivo_form():
    """Pagina con form per la richiesta di preventivo dettagliato."""
    return render_template('preventivo_form.html', title='Richiesta Preventivo')

@app.route('/')
@app.route('/home')
def home():
    """Pagina principale del sito."""
    return render_template('home.html', title='Home')

@app.route('/services')
def services():
    """Pagina dei servizi offerti."""
    return render_template('home.html', title='Servizi')  # Per ora utilizziamo home.html, puoi creare un template specifico in futuro

@app.route('/quote')
def quote():
    """Pagina per richiedere un preventivo."""
    return render_template('quote.html', title='Preventivo')

@app.route('/gallery')
def gallery():
    """Pagina della galleria di immagini."""
    return render_template('home.html', title='Galleria')  # Per ora utilizziamo home.html, puoi creare un template specifico in futuro

@app.route('/contact')
def contact():
    """Pagina dei contatti."""
    return render_template('home.html', title='Contatti')  # Per ora utilizziamo home.html, puoi creare un template specifico in futuro


# =============== CHAT AI CON OPENROUTER ===============

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint per gestire le richieste della chat con OpenRouter."""
    if not request.is_json:
        return jsonify({'error': 'La richiesta deve essere in formato JSON'}), 400
    
    data = request.json
    user_message = data.get('message', '')
    chat_history = data.get('history', [])
    
    if not user_message:
        return jsonify({'error': 'Il messaggio non può essere vuoto'}), 400
    
    # Ottieni l'ora corrente in Italia
    now = datetime.now()
    current_hour = now.hour
    
    # Determina il saluto in base all'ora
    if 5 <= current_hour < 12:
        time_greeting = "buongiorno"
    elif 12 <= current_hour < 18:
        time_greeting = "buon pomeriggio"
    else:
        time_greeting = "buonasera"
    
    # Preparazione dei messaggi per OpenRouter
    messages = []
    
    # Aggiungi un messaggio di sistema che definisce il contesto
        # Aggiungi un messaggio di sistema che definisce il contesto
    messages.append({
                "role": "system", 
                "content": f"""Sei l'assistente virtuale ufficiale di Ristrutturazioni Morcianesi, azienda fondata nel 2003 a Morciano di Romagna (RN) e specializzata in ristrutturazioni edilizie di alta qualità. 

        INFORMAZIONI SULL'AZIENDA:
        - Nome: Ristrutturazioni Morcianesi
        - Fondazione: 2003
        - Sede: Via Francesco Petrarca, 19, Morciano di Romagna (RN)
        - Contatti: Tel: 351 781 4956 (Neti), 328 883 7562 (Shino), Email: ristrutturazionimorcianesi@gmail.com
        - Esperienza: Oltre 20 anni nel settore delle ristrutturazioni, con centinaia di progetti completati in tutta la provincia di Rimini e Pesaro
        - Filosofia: Qualità, professionalità e rispetto delle tempistiche e dei preventivi concordati

        SERVIZI OFFERTI:
        1. Ristrutturazione completa appartamenti
        2. Rifacimento bagni e cucine
        3. Opere murarie e demolizioni
        4. Impianti idraulici ed elettrici(Contatti stretti della ditta)
        5. Pavimentazioni e rivestimenti
        6. Controsoffitti e cartongesso
        7. Pitture e decorazioni
        8. Facciate esterne
        9. Ristrutturazioni commerciali

        PROCESSI DI LAVORO:
        - Sopralluogo gratuito ed entro 24 ore
        - Preventivo dettagliato senza impegno
        - Progettazione personalizzata
        - Gestione completa dei lavori e delle pratiche burocratiche
        - Consegna nei tempi concordati
        - Garanzia sui lavori eseguiti

        ISTRUZIONI IMPORTANTI:
        - L'ora attuale è {now.strftime('%H:%M')} e oggi è {now.strftime('%A %d %B %Y')}
        - Se l'utente saluta con "ciao", "salve", "buongiorno", ecc., rispondi sempre con "{time_greeting}" seguito dalla tua risposta
        - Quando chiedi informazioni di contatto, menziona gli orari di lavoro dell'azienda
        - Fornisci sempre informazioni accurate sugli orari, sui contatti e sui servizi


        Il tuo compito è aiutare i clienti a ottenere informazioni sui servizi, stimare costi e tempi approssimativi per lavori di ristrutturazione, e raccogliere le informazioni necessarie per un preventivo dettagliato. Quando un utente chiede un preventivo, cerca di ottenere: tipo di lavoro, metratura, ubicazione, e tempistiche desiderate. 

        Rispondi sempre in modo professionale, cordiale e conciso, rappresentando al meglio l'immagine di Ristrutturazioni Morcianesi."""
            })
    
    # Aggiungi la cronologia della chat
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Aggiungi il messaggio dell'utente
    messages.append({"role": "user", "content": user_message})
    
    # Torna a usare gpt-3.5-turbo che funziona sicuramente con OpenRouter
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    headers = {
        "Authorization": f"Bearer {app.config['OPENROUTER_API_KEY']}",
        "HTTP-Referer": request.host_url,  # Richiesto da OpenRouter
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(app.config['OPENROUTER_URL'], headers=headers, json=payload)
        response.raise_for_status()  # Solleva un'eccezione in caso di errore HTTP
        
        result = response.json()
        
        # Debug - Aggiungi questo per vedere la struttura della risposta
        print(f"Risposta API: {json.dumps(result, indent=2)}")
        
        # Gestione della risposta con verifica della struttura
        if "choices" in result and len(result["choices"]) > 0:
            if "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                ai_message = result["choices"][0]["message"]["content"]
            else:
                # Fallback per altri modelli con struttura diversa
                ai_message = "Mi dispiace, ho avuto problemi a interpretare la risposta. Puoi riprovare con una domanda diversa?"
                print(f"Struttura risposta inaspettata: {result}")
        else:
            ai_message = "Mi dispiace, ho ricevuto una risposta vuota dal modello. Riprova più tardi."
        
        return jsonify({
            "success": True,
            "message": ai_message
        })
    
    except Exception as e:
        print(f"Errore nella richiesta all'API: {str(e)}")
        if response and hasattr(response, 'text'):
            print(f"Risposta del server: {response.text}")
        return jsonify({
            "success": False,
            "error": "Si è verificato un errore durante la comunicazione con l'assistente AI"
        }), 500

# =============== API PER LA GESTIONE DELLE CHAT SALVATE ===============

@app.route('/api/save-chat', methods=['POST'])
def save_chat():
    """API endpoint per salvare una conversazione nella cronologia dell'utente."""
    # Verifica se l'utente è autenticato
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'error': 'Devi essere autenticato per salvare una conversazione'
        }), 401
    
    if not request.is_json:
        return jsonify({'success': False, 'error': 'La richiesta deve essere in formato JSON'}), 400
    
    data = request.json
    title = data.get('title', 'Conversazione senza titolo')
    messages = data.get('messages', [])
    chat_id = data.get('chat_id', None)
    
    if not messages:
        return jsonify({'success': False, 'error': 'Nessun messaggio da salvare'}), 400
    
    # Converti i messaggi in formato JSON
    messages_json = json.dumps(messages)
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        if chat_id:  # Se esiste un ID, aggiorna la chat esistente
            cursor.execute(
                'UPDATE saved_chats SET title = ?, messages = ?, updated_at = ? WHERE id = ? AND user_id = ?',
                (title, messages_json, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), chat_id, session['user_id'])
            )
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'error': 'Chat non trovata o non autorizzato'}), 404
        else:  # Altrimenti, crea una nuova chat
            cursor.execute(
                'INSERT INTO saved_chats (user_id, title, messages) VALUES (?, ?, ?)',
                (session['user_id'], title, messages_json)
            )
            chat_id = cursor.lastrowid
        
        db.commit()
        return jsonify({'success': True, 'chat_id': chat_id})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/saved-chats', methods=['GET'])
def get_saved_chats():
    """API endpoint per ottenere tutte le conversazioni salvate dell'utente."""
    # Verifica se l'utente è autenticato
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'error': 'Devi essere autenticato per visualizzare le conversazioni salvate'
        }), 401
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(
            'SELECT id, title, messages, created_at, updated_at FROM saved_chats WHERE user_id = ? ORDER BY updated_at DESC',
            (session['user_id'],)
        )
        
        chats = []
        for row in cursor.fetchall():
            chats.append({
                'id': row['id'],
                'title': row['title'],
                'messages': row['messages'],  # Questo sarà già in formato JSON
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return jsonify({'success': True, 'chats': chats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chat/<int:chat_id>', methods=['GET', 'DELETE'])
def manage_chat(chat_id):
    """API endpoint per gestire una specifica conversazione salvata (caricamento o eliminazione)."""
    # Verifica se l'utente è autenticato
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'error': 'Devi essere autenticato per gestire le conversazioni'
        }), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # Verifica che la chat appartenga all'utente
    cursor.execute(
        'SELECT id, title, messages, created_at, updated_at FROM saved_chats WHERE id = ? AND user_id = ?',
        (chat_id, session['user_id'])
    )
    chat = cursor.fetchone()
    
    if not chat:
        return jsonify({'success': False, 'error': 'Chat non trovata o non autorizzato'}), 404
    
    if request.method == 'GET':
        # Carica la chat
        chat_data = {
            'id': chat['id'],
            'title': chat['title'],
            'messages': chat['messages'],  # Già in formato JSON
            'created_at': chat['created_at'],
            'updated_at': chat['updated_at']
        }
        
        return jsonify({'success': True, 'chat': chat_data})
    
    elif request.method == 'DELETE':
        # Elimina la chat
        try:
            cursor.execute('DELETE FROM saved_chats WHERE id = ? AND user_id = ?', (chat_id, session['user_id']))
            db.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

# =============== API ===============

@app.route('/api/invia-preventivo', methods=['POST'])
def invia_preventivo():
    """API per l'invio di un preventivo dettagliato."""
    # Non richiediamo più l'autenticazione per inviare un preventivo
    
    try:
        # Ottieni dati dal form
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        indirizzo = request.form.get('indirizzo')
        tipologia = request.form.get('tipologia')
        altro_dettaglio = request.form.get('altro_dettaglio')
        descrizione = request.form.get('descrizione')
        
        # Se è stato selezionato "altro" come tipologia, usa il dettaglio fornito
        if tipologia == 'altro' and altro_dettaglio:
            tipo_lavoro = altro_dettaglio
        else:
            tipo_lavoro = tipologia
        
        # Gestione delle foto
        foto_paths = []
        if 'foto' in request.files:
            foto_files = request.files.getlist('foto')
            for i, foto in enumerate(foto_files):
                if foto.filename != '':
                    # Genera un nome file sicuro
                    filename = secure_filename(foto.filename)
                    # Creiamo una cartella per le foto dei preventivi se non esiste
                    preventivi_dir = os.path.join(app.static_folder, 'uploads', 'preventivi')
                    if not os.path.exists(preventivi_dir):
                        os.makedirs(preventivi_dir)
                    # Salva il file
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    file_path = os.path.join(preventivi_dir, f"{timestamp}_{filename}")
                    foto.save(file_path)
                    foto_paths.append(os.path.join('uploads', 'preventivi', f"{timestamp}_{filename}"))
        
        # Determina l'ID utente se autenticato, altrimenti NULL
        user_id = session.get('user_id', None)
        
        # Salva nel database
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO preventivi (user_id, nome, email, telefono, indirizzo, tipologia, '
            'descrizione, foto_paths, data_richiesta, stato) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, nome, email, telefono, indirizzo, tipo_lavoro,
             descrizione, json.dumps(foto_paths), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Nuovo')
        )
        db.commit()
        
        # Invia email di notifica all'azienda
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@ristrutturazionimorcianesi.it')
        subject = 'Nuova richiesta di preventivo'
        
        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #1B9DD1;">Nuova richiesta di preventivo</h2>
                <p><strong>Nome:</strong> {nome}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Telefono:</strong> {telefono}</p>
                <p><strong>Indirizzo:</strong> {indirizzo}</p>
                <p><strong>Tipologia lavoro:</strong> {tipo_lavoro}</p>
                <p><strong>Descrizione:</strong></p>
                <p style="background-color: #f9f9f9; padding: 10px; border-radius: 5px;">{descrizione}</p>
                <p><strong>Allegati:</strong> {len(foto_paths)} foto</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 0.9em; color: #777;">Questa email è stata generata automaticamente dal sito Ristrutturazioni Morcianesi.</p>
            </div>
        </body>
        </html>
        '''
        
        send_email(admin_email, subject, html_content)
        
        # Invia email di conferma al cliente
        client_subject = 'Abbiamo ricevuto la tua richiesta di preventivo - Ristrutturazioni Morcianesi'
        
        client_html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #1B9DD1;">Grazie per la tua richiesta di preventivo!</h2>
                <p>Gentile {nome},</p>
                <p>Abbiamo ricevuto la tua richiesta di preventivo e ti ringraziamo per averci contattato.</p>
                <p>Un nostro tecnico esaminerà i dettagli e ti contatterà al più presto per fissare un sopralluogo gratuito.</p>
                <p>Ecco un riepilogo della tua richiesta:</p>
                <ul>
                    <li><strong>Tipologia lavoro:</strong> {tipo_lavoro}</li>
                    <li><strong>Indirizzo:</strong> {indirizzo}</li>
                    <li><strong>Descrizione:</strong> {descrizione[:100]}...</li>
                </ul>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 0.9em; color: #777;">Cordiali saluti,<br>Il team di Ristrutturazioni Morcianesi</p>
            </div>
        </body>
        </html>
        '''
        
        send_email(email, client_subject, client_html_content)
        
        return jsonify({'success': True, 'message': 'Richiesta di preventivo inviata con successo!'})
    
    except Exception as e:
        app.logger.error(f"Errore nell'invio del preventivo: {str(e)}")
        return jsonify({'success': False, 'error': 'Si è verificato un errore durante l\'invio del preventivo.'}), 500

@app.route('/api/preventivo', methods=['POST'])
@login_required
def submit_preventivo():
    """API per l'invio di una richiesta di preventivo dettagliata."""
    try:
        data = {
            'user_id': session['user_id'],
            'nome': request.form.get('nome'),
            'email': request.form.get('email'),
            'telefono': request.form.get('telefono'),
            'indirizzo': request.form.get('indirizzo'),
            'tipologia': request.form.get('tipologia'),
            'descrizione': request.form.get('descrizione'),
            'budget': request.form.get('budget'),
            'tempistiche': request.form.get('tempistiche'),
            'data_richiesta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stato': 'nuovo'
        }
        
        # Gestione upload di foto
        foto_paths = []
        for i in range(1, 6):  # Fino a 5 foto
            if f'foto{i}' in request.files:
                foto = request.files[f'foto{i}']
                if foto and foto.filename != '':
                    filename = secure_filename(f"{session['user_id']}_{int(time.time())}_{i}_{foto.filename}")
                    upload_folder = os.path.join(app.static_folder, 'uploads', 'preventivi')
                    
                    # Crea la directory se non esiste
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    
                    filepath = os.path.join(upload_folder, filename)
                    foto.save(filepath)
                    foto_paths.append(os.path.join('uploads', 'preventivi', filename))
        
        # Salva nel database
        data['foto_paths'] = json.dumps(foto_paths)
        
        db = get_db()
        db.execute(
            'INSERT INTO preventivi (user_id, nome, email, telefono, indirizzo, '
            'tipologia, descrizione, budget, tempistiche, foto_paths, data_richiesta, stato) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (data['user_id'], data['nome'], data['email'], data['telefono'], 
             data['indirizzo'], data['tipologia'], data['descrizione'], 
             data['budget'], data['tempistiche'], data['foto_paths'], 
             data['data_richiesta'], data['stato'])
        )
        db.commit()
        
        # Invia email di conferma
        msg = Message("Richiesta di preventivo ricevuta",
                     sender=app.config['MAIL_DEFAULT_SENDER'],
                     recipients=[data['email']])
        msg.body = f"""
        Gentile {data['nome']},
        
        Abbiamo ricevuto la tua richiesta di preventivo per il tuo progetto di ristrutturazione.
        
        Un nostro operatore la esaminerà al più presto e ti contatterà per ulteriori dettagli.
        
        Grazie per aver scelto Ristrutturazioni Morcianesi.
        
        Cordiali saluti,
        Il team di Ristrutturazioni Morcianesi
        """
        mail.send(msg)
        
        # Invia email di notifica all'amministratore
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@ristrutturazionimorcianesi.it')
        admin_msg = Message("Nuova richiesta di preventivo",
                           sender=app.config['MAIL_DEFAULT_SENDER'],
                           recipients=[admin_email])
        admin_msg.body = f"""
        È stata ricevuta una nuova richiesta di preventivo:
        
        Cliente: {data['nome']} ({data['email']})
        Telefono: {data['telefono']}
        Indirizzo: {data['indirizzo']}
        Tipologia: {data['tipologia']}
        Descrizione: {data['descrizione']}
        Budget: {data['budget']}
        Tempistiche: {data['tempistiche']}
        
        Accedi al pannello amministrativo per visualizzare i dettagli completi.
        """
        mail.send(admin_msg)
        
        flash('La tua richiesta di preventivo è stata inviata con successo! Ti contatteremo presto.', 'success')
        return redirect(url_for('preventivo_form'))
    
    except Exception as e:
        app.logger.error(f"Errore nell'invio del preventivo: {str(e)}")
        flash('Si è verificato un errore durante l\'invio del preventivo. Riprova più tardi.', 'danger')
        return redirect(url_for('preventivo_form'))

# =============== GESTIONE PREVENTIVI ===============

@app.route('/admin/preventivi')
@admin_required
def admin_preventivi():
    """Pagina di gestione preventivi per amministratori."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            p.id, p.nome, p.email, p.telefono, p.indirizzo, p.tipo_lavoro, p.descrizione, 
            p.foto_paths, p.created_at, p.stato, u.username as richiesto_da
        FROM preventivi p
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
    """)
    preventivi = cursor.fetchall()
    
    return render_template('gestione_preventivi.html', title='Gestione Preventivi', preventivi=preventivi)


@app.route('/api/cambia-stato-preventivo', methods=['POST'])
def cambia_stato_preventivo():
    """API endpoint per cambiare lo stato di un preventivo."""
    # Verifica che l'utente sia autenticato e sia un amministratore
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Utente non autenticato'}), 401
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if not user or user['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Permessi insufficienti'}), 403
    
    # Ottieni i dati dalla richiesta
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Dati non validi'}), 400
    
    data = request.json
    preventivo_id = data.get('preventivo_id')
    nuovo_stato = data.get('stato')
    
    if not preventivo_id or not nuovo_stato:
        return jsonify({'success': False, 'error': 'Dati mancanti'}), 400
    
    # Controlla che lo stato sia valido
    stati_validi = ['nuovo', 'in_lavorazione', 'completato', 'rifiutato']
    if nuovo_stato not in stati_validi:
        return jsonify({'success': False, 'error': 'Stato non valido'}), 400
    
    # Aggiorna lo stato del preventivo
    try:
        cursor.execute(
            'UPDATE preventivi SET stato = ? WHERE id = ?',
            (nuovo_stato, preventivo_id)
        )
        db.commit()
        
        # Registra un messaggio di sistema nella chat
        stato_leggibile = {
            'nuovo': 'nuovo',
            'in_lavorazione': 'in lavorazione',
            'completato': 'completato',
            'rifiutato': 'rifiutato'
        }
        
        messaggio = f"Lo stato del preventivo è stato aggiornato a: {stato_leggibile[nuovo_stato]}"
        
        cursor.execute(
            '''INSERT INTO chat_messages (preventivo_id, user_id, message, is_system)
               VALUES (?, ?, ?, 1)''',
            (preventivo_id, session['user_id'], messaggio)
        )
        db.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/rispondi-preventivo', methods=['POST'])
def rispondi_preventivo():
    """API endpoint per rispondere a un preventivo."""
    # Verifica che l'utente sia autenticato
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Utente non autenticato'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # Verifica se l'utente è un amministratore o il proprietario del preventivo
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Ottieni i dati dalla richiesta
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Dati non validi'}), 400
    
    data = request.json
    preventivo_id = data.get('preventivo_id')
    messaggio = data.get('messaggio')
    
    if not preventivo_id or not messaggio:
        return jsonify({'success': False, 'error': 'Dati mancanti'}), 400
    
    # Se non è admin, verifica che il preventivo appartenga all'utente
    if user['role'] != 'admin':
        cursor.execute(
            'SELECT COUNT(*) as count FROM preventivi WHERE id = ? AND user_id = ?',
            (preventivo_id, session['user_id'])
        )
        result = cursor.fetchone()
        if result['count'] == 0:
            return jsonify({'success': False, 'error': 'Preventivo non trovato o non autorizzato'}), 404
    
    # Salva il messaggio nella tabella chat_messages
    try:
        cursor.execute(
            '''INSERT INTO chat_messages (preventivo_id, user_id, message)
               VALUES (?, ?, ?)''',
            (preventivo_id, session['user_id'], messaggio)
        )
        db.commit()
        
        # Recupera le informazioni dell'utente che ha inviato il messaggio
        cursor.execute(
            'SELECT u.nome, u.cognome, u.role FROM users u WHERE id = ?',
            (session['user_id'],)
        )
        sender = cursor.fetchone()
        
        # Recupera l'orario di invio del messaggio
        cursor.execute(
            'SELECT created_at FROM chat_messages WHERE id = last_insert_rowid()'
        )
        timestamp = cursor.fetchone()['created_at']
        
        return jsonify({
            'success': True,
            'message': {
                'content': messaggio,
                'sender': f"{sender['nome']} {sender['cognome']}",
                'is_admin': sender['role'] == 'admin',
                'timestamp': timestamp
            }
        })
    
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/get-chat-messages/<int:preventivo_id>', methods=['GET'])
def get_chat_messages(preventivo_id):
    """API endpoint per ottenere tutti i messaggi di chat di un preventivo."""
    # Verifica che l'utente sia autenticato
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Utente non autenticato'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # Verifica se l'utente è un amministratore o il proprietario del preventivo
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Se non è admin, verifica che il preventivo appartenga all'utente
    if user['role'] != 'admin':
        cursor.execute(
            'SELECT COUNT(*) as count FROM preventivi WHERE id = ? AND user_id = ?',
            (preventivo_id, session['user_id'])
        )
        result = cursor.fetchone()
        if result['count'] == 0:
            return jsonify({'success': False, 'error': 'Preventivo non trovato o non autorizzato'}), 404
    
    # Recupera tutti i messaggi della chat
    cursor.execute('''
        SELECT cm.id, cm.preventivo_id, cm.user_id, cm.message, cm.is_system, cm.created_at,
               u.nome, u.cognome, u.role
        FROM chat_messages cm
        JOIN users u ON cm.user_id = u.id
        WHERE cm.preventivo_id = ?
        ORDER BY cm.created_at ASC
    ''', (preventivo_id,))
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            'id': row['id'],
            'content': row['message'],
            'sender': f"{row['nome']} {row['cognome']}",
            'is_admin': row['role'] == 'admin',
            'is_system': bool(row['is_system']),
            'timestamp': row['created_at']
        })
    
    return jsonify({'success': True, 'messages': messages})


@app.route('/i-miei-preventivi')
def i_miei_preventivi():
    """Visualizza i preventivi dell'utente corrente."""
    # Verifica che l'utente sia autenticato
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Recupera i preventivi dell'utente
    cursor.execute('''
        SELECT p.*, 
               (SELECT COUNT(*) FROM chat_messages WHERE preventivo_id = p.id) as num_messaggi
        FROM preventivi p
        WHERE p.user_id = ?
        ORDER BY p.data_richiesta DESC
    ''', (session['user_id'],))
    
    preventivi = cursor.fetchall()
    
    return render_template('i_miei_preventivi.html', preventivi=preventivi)


@app.route('/chat-preventivo/<int:preventivo_id>')
def chat_preventivo(preventivo_id):
    """Visualizza la chat di un preventivo specifico."""
    # Verifica che l'utente sia autenticato
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Verifica se l'utente è un amministratore o il proprietario del preventivo
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Recupera le informazioni del preventivo
    cursor.execute('SELECT * FROM preventivi WHERE id = ?', (preventivo_id,))
    preventivo = cursor.fetchone()
    
    if not preventivo:
        flash('Preventivo non trovato', 'danger')
        return redirect(url_for('home'))
    
    # Se non è admin, verifica che il preventivo appartenga all'utente
    if user['role'] != 'admin' and preventivo['user_id'] != session['user_id']:
        flash('Non hai i permessi per visualizzare questo preventivo', 'danger')
        return redirect(url_for('home'))
    
    # Recupera tutti i messaggi della chat
    cursor.execute('''
        SELECT cm.id, cm.preventivo_id, cm.user_id, cm.message, cm.is_system, cm.created_at,
               u.nome, u.cognome, u.role
        FROM chat_messages cm
        JOIN users u ON cm.user_id = u.id
        WHERE cm.preventivo_id = ?
        ORDER BY cm.created_at ASC
    ''', (preventivo_id,))
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            'id': row['id'],
            'content': row['message'],
            'sender': f"{row['nome']} {row['cognome']}",
            'is_admin': row['role'] == 'admin',
            'is_system': bool(row['is_system']),
            'timestamp': row['created_at']
        })
    
    return render_template('chat_preventivo.html', preventivo=preventivo, messages=messages)

# =============== BLOCCO PER L'AVVIO DIRETTO ===============

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)