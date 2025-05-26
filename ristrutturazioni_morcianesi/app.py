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

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

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
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token

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
    DEBUG=True,
    # OAuth Configuration
    GOOGLE_CLIENT_ID=os.environ.get('GOOGLE_CLIENT_ID', ''),
    GOOGLE_CLIENT_SECRET=os.environ.get('GOOGLE_CLIENT_SECRET', ''),
    APPLE_CLIENT_ID=os.environ.get('APPLE_CLIENT_ID', ''),
    APPLE_CLIENT_SECRET=os.environ.get('APPLE_CLIENT_SECRET', ''),
    APPLE_TEAM_ID=os.environ.get('APPLE_TEAM_ID', ''),
    APPLE_KEY_ID=os.environ.get('APPLE_KEY_ID', ''),
)

csrf = CSRFProtect(app)
mail = Mail(app)  # Inizializzazione dell'oggetto mail

# =============== OAUTH CONFIGURATION ===============
oauth = OAuth(app)

# Check which OAuth providers are configured
GOOGLE_OAUTH_ENABLED = bool(
    app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET')
)

APPLE_OAUTH_ENABLED = bool(
    app.config.get('APPLE_CLIENT_ID') and app.config.get('APPLE_TEAM_ID') and 
    app.config.get('APPLE_KEY_ID')
)

# Overall OAuth enabled if at least one provider is configured
OAUTH_ENABLED = GOOGLE_OAUTH_ENABLED or APPLE_OAUTH_ENABLED

# Initialize OAuth providers
google = None
apple = None

# Configure Google OAuth if credentials are available
if GOOGLE_OAUTH_ENABLED:
    google = oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        access_token_url='https://oauth2.googleapis.com/token',
        access_token_params=None,
        refresh_token_url=None,
        client_kwargs={
            'scope': 'openid email profile'
        },
    )
    print("✅ Google OAuth configured successfully")

# Configure Apple OAuth if credentials are available
if APPLE_OAUTH_ENABLED:
    apple = oauth.register(
        name='apple',
        client_id=app.config['APPLE_CLIENT_ID'],
        client_secret=app.config['APPLE_CLIENT_SECRET'],
        authorize_url='https://appleid.apple.com/auth/authorize',
        authorize_params={
            'response_mode': 'form_post',
        },
        access_token_url='https://appleid.apple.com/auth/token',
        client_kwargs={
            'scope': 'name email'
        },
    )
    print("✅ Apple OAuth configured successfully")

# Status messages
if not OAUTH_ENABLED:
    print("⚠️  No OAuth providers configured. OAuth login buttons will be disabled.")
    print("   To enable OAuth, add credentials to your .env file.")
    print("   See OAUTH_SETUP.md for detailed instructions.")
elif GOOGLE_OAUTH_ENABLED and not APPLE_OAUTH_ENABLED:
    print("ℹ️  Google OAuth enabled, Apple OAuth disabled.")
    print("   You can add Apple OAuth credentials later to enable it.")
elif APPLE_OAUTH_ENABLED and not GOOGLE_OAUTH_ENABLED:
    print("ℹ️  Apple OAuth enabled, Google OAuth disabled.")
elif GOOGLE_OAUTH_ENABLED and APPLE_OAUTH_ENABLED:
    print("✅ Both Google and Apple OAuth configured successfully!")

# Make OAuth status available to templates
app.config['OAUTH_ENABLED'] = OAUTH_ENABLED
app.config['GOOGLE_OAUTH_ENABLED'] = GOOGLE_OAUTH_ENABLED
app.config['APPLE_OAUTH_ENABLED'] = APPLE_OAUTH_ENABLED

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
    """Funzione generica per inviare email con diagnostiche avanzate."""
    print(f"[EMAIL DEBUG] Tentativo invio email a: {to_email}")
    print(f"[EMAIL DEBUG] Oggetto: {subject}")
    print(f"[EMAIL DEBUG] Server SMTP: {app.config['EMAIL_HOST']}:{app.config['EMAIL_PORT']}")
    print(f"[EMAIL DEBUG] Account mittente: {app.config['EMAIL_USER']}")
    
    msg = MIMEMultipart()
    msg['From'] = app.config['EMAIL_USER']
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        print("[EMAIL DEBUG] Connessione al server SMTP...")
        server = smtplib.SMTP(app.config['EMAIL_HOST'], app.config['EMAIL_PORT'])
        server.set_debuglevel(1)  # Abilita debug SMTP
        
        print("[EMAIL DEBUG] Avvio TLS...")
        server.starttls()
        
        print("[EMAIL DEBUG] Login al server...")
        server.login(app.config['EMAIL_USER'], app.config['EMAIL_PASSWORD'])
        
        print("[EMAIL DEBUG] Invio messaggio...")
        server.send_message(msg)
        
        print("[EMAIL DEBUG] Chiusura connessione...")
        server.quit()
        
        print(f"[EMAIL SUCCESS] Email inviata con successo a {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"[EMAIL ERROR] Errore di autenticazione SMTP: {e}")
        print("[EMAIL ERROR] Possibili cause:")
        print("- Password dell'app Gmail scaduta o non valida")
        print("- Autenticazione a 2 fattori non configurata correttamente")
        print("- Account Gmail bloccato o sospeso")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"[EMAIL ERROR] Errore di connessione SMTP: {e}")
        print("[EMAIL ERROR] Possibili cause:")
        print("- Problemi di rete")
        print("- Server SMTP Gmail non raggiungibile")
        print("- Porta SMTP bloccata dal firewall")
        return False
        
    except smtplib.SMTPRecipientsRefused as e:
        print(f"[EMAIL ERROR] Destinatario rifiutato: {e}")
        print("[EMAIL ERROR] L'indirizzo email del destinatario non è valido")
        return False
        
    except smtplib.SMTPException as e:
        print(f"[EMAIL ERROR] Errore SMTP generico: {e}")
        return False
        
    except Exception as e:
        print(f"[EMAIL ERROR] Errore sconosciuto nell'invio dell'email: {e}")
        print(f"[EMAIL ERROR] Tipo errore: {type(e).__name__}")
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
    
    def __init__(self, id=None, nome=None, cognome=None, email=None, password_hash=None, is_verified=0, 
                 verification_token=None, token_created_at=None, reset_token=None, reset_token_created_at=None, 
                 role='user', oauth_provider=None, oauth_id=None, avatar_url=None, created_at=None):
        self.id = id
        self.nome = nome
        self.cognome = cognome
        self.email = email
        self.password_hash = password_hash
        self.is_verified = is_verified
        self.verification_token = verification_token
        self.token_created_at = token_created_at
        self.reset_token = reset_token
        self.reset_token_created_at = reset_token_created_at
        self.role = role
        self.oauth_provider = oauth_provider
        self.oauth_id = oauth_id
        self.avatar_url = avatar_url
        self.created_at = created_at
    
    @property
    def full_name(self):
        """Restituisce nome completo (nome + cognome)."""
        return f"{self.nome} {self.cognome}" if self.nome and self.cognome else ""

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
                nome=safe_get(user_data, 'nome'),
                cognome=safe_get(user_data, 'cognome'),
                email=user_data['email'],
                password_hash=safe_get(user_data, 'password_hash'),
                is_verified=safe_get(user_data, 'is_verified', 0),
                verification_token=safe_get(user_data, 'verification_token'),
                token_created_at=safe_get(user_data, 'token_created_at'),
                reset_token=safe_get(user_data, 'reset_token'),
                reset_token_created_at=safe_get(user_data, 'reset_token_created_at'),
                role=safe_get(user_data, 'role', 'user'),
                oauth_provider=safe_get(user_data, 'oauth_provider'),
                oauth_id=safe_get(user_data, 'oauth_id'),
                avatar_url=safe_get(user_data, 'avatar_url'),
                created_at=safe_get(user_data, 'created_at')
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
                nome=safe_get(user_data, 'nome'),
                cognome=safe_get(user_data, 'cognome'),
                email=user_data['email'],
                password_hash=safe_get(user_data, 'password_hash'),
                is_verified=safe_get(user_data, 'is_verified', 0),
                verification_token=safe_get(user_data, 'verification_token'),
                token_created_at=safe_get(user_data, 'token_created_at'),
                reset_token=safe_get(user_data, 'reset_token'),
                reset_token_created_at=safe_get(user_data, 'reset_token_created_at'),
                role=safe_get(user_data, 'role', 'user'),
                oauth_provider=safe_get(user_data, 'oauth_provider'),
                oauth_id=safe_get(user_data, 'oauth_id'),
                avatar_url=safe_get(user_data, 'avatar_url'),
                created_at=safe_get(user_data, 'created_at')
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
                nome=safe_get(user_data, 'nome'),
                cognome=safe_get(user_data, 'cognome'),
                email=user_data['email'],
                password_hash=safe_get(user_data, 'password_hash'),
                is_verified=safe_get(user_data, 'is_verified', 0),
                verification_token=safe_get(user_data, 'verification_token'),
                token_created_at=safe_get(user_data, 'token_created_at'),
                role=safe_get(user_data, 'role', 'user'),
                oauth_provider=safe_get(user_data, 'oauth_provider'),
                oauth_id=safe_get(user_data, 'oauth_id'),
                avatar_url=safe_get(user_data, 'avatar_url'),
                created_at=safe_get(user_data, 'created_at')
            )
        return None

    @staticmethod
    def get_by_oauth(oauth_provider, oauth_id):
        """Recupera un utente dal database tramite provider OAuth e ID."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE oauth_provider = ? AND oauth_id = ?', (oauth_provider, oauth_id))
        user_data = cursor.fetchone()
        if user_data:
            return User(
                id=user_data['id'],
                nome=safe_get(user_data, 'nome'),
                cognome=safe_get(user_data, 'cognome'),
                email=user_data['email'],
                password_hash=safe_get(user_data, 'password_hash'),
                is_verified=safe_get(user_data, 'is_verified', 0),
                verification_token=safe_get(user_data, 'verification_token'),
                token_created_at=safe_get(user_data, 'token_created_at'),
                reset_token=safe_get(user_data, 'reset_token'),
                reset_token_created_at=safe_get(user_data, 'reset_token_created_at'),
                role=safe_get(user_data, 'role', 'user'),
                oauth_provider=safe_get(user_data, 'oauth_provider'),
                oauth_id=safe_get(user_data, 'oauth_id'),
                avatar_url=safe_get(user_data, 'avatar_url'),
                created_at=safe_get(user_data, 'created_at')
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
                nome=safe_get(user_data, 'nome'),
                cognome=safe_get(user_data, 'cognome'),
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_verified=safe_get(user_data, 'is_verified', 0),
                reset_token=safe_get(user_data, 'reset_token'),
                reset_token_created_at=safe_get(user_data, 'reset_token_created_at'),
                role=safe_get(user_data, 'role', 'user')
            )
        return None

        return None

    def save(self):
        """Salva un nuovo utente nel database o aggiorna un utente esistente."""
        db = get_db()
        cursor = db.cursor()

        if self.id is None:
            # INSERT per un nuovo utente
            cursor.execute(
                '''INSERT INTO users (nome, cognome, email, password_hash, is_verified, verification_token, 
                   token_created_at, oauth_provider, oauth_id, avatar_url) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (self.nome, self.cognome, self.email, self.password_hash, self.is_verified, 
                 self.verification_token, self.token_created_at, self.oauth_provider, 
                 self.oauth_id, self.avatar_url)
            )
            self.id = cursor.lastrowid
        else:
            # UPDATE per un utente esistente
            cursor.execute(
                '''UPDATE users SET nome = ?, cognome = ?, email = ?, password_hash = ?, is_verified = ?, 
                   verification_token = ?, token_created_at = ?, oauth_provider = ?, oauth_id = ?, 
                   avatar_url = ? WHERE id = ?''',
                (self.nome, self.cognome, self.email, self.password_hash, self.is_verified, 
                 self.verification_token, self.token_created_at, self.oauth_provider, 
                 self.oauth_id, self.avatar_url, self.id)
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
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        errors = []

        # Validazione input
        if not nome or len(nome) < 2 or len(nome) > 50:
            errors.append("Il nome deve avere tra 2 e 50 caratteri.")
        if not cognome or len(cognome) < 2 or len(cognome) > 50:
            errors.append("Il cognome deve avere tra 2 e 50 caratteri.")
        if not email:
            errors.append("L'email è richiesta.")
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            errors.append("L'indirizzo email non è valido.")
        if not password or len(password) < 12 or len(password) > 60:
            errors.append("La password deve avere tra 12 e 60 caratteri.")
        if password != confirm_password:
            errors.append("Le password non corrispondono.")

        # Check for existing email
        if User.get_by_email(email):
            errors.append('Un account con questa email esiste già. Prova ad accedere.')

        if not errors:
            try:
                # Genera un token di verifica
                verification_token = secrets.token_urlsafe(32)
                token_created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Salva l'utente con il token
                hashed_password = generate_password_hash(password)
                new_user = User(
                    id=None, 
                    nome=nome, 
                    cognome=cognome,
                    email=email, 
                    password_hash=hashed_password,
                    is_verified=0,
                    verification_token=verification_token,
                    token_created_at=token_created_at
                )
                new_user.save()
                
                # Invia l'email di verifica
                full_name = f"{nome} {cognome}"
                if send_verification_email(email, full_name, verification_token):
                    flash('Registrazione completata! Ti abbiamo inviato un\'email di verifica. Per favore, controlla la tua casella di posta.', 'success')
                else:
                    flash('Registrazione completata, ma non è stato possibile inviare l\'email di verifica. Prova a richiederne un\'altra.', 'warning')
                
                return redirect(url_for('login'))
                
            except Exception as e:
                print(f"Errore durante la registrazione: {e}")
                if "UNIQUE constraint failed: users.email" in str(e):
                    flash('Un account con questa email esiste già. Prova ad accedere.', 'danger')
                else:
                    flash('Si è verificato un errore durante la registrazione. Riprova più tardi.', 'danger')
                return render_template('register.html', title='Registrazione',
                                      nome_val=nome, cognome_val=cognome, email_val=email)
        else:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', title='Registrazione',
                                  nome_val=nome, cognome_val=cognome, email_val=email)

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
            session['user_full_name'] = user.full_name
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
        if send_verification_email(email, user.full_name, verification_token):
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
    session.pop('user_full_name', None)
    flash('Ti sei disconnesso.', 'info')
    return redirect(url_for('home'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Gestisce il recupero della password dimenticata."""
    if 'user_id' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        print(f"[FORGOT PASSWORD] Richiesta reset per email: {email}")
        
        user = User.get_by_email(email)
        
        if user:
            print(f"[FORGOT PASSWORD] Utente trovato: {user.full_name} (ID: {user.id})")
            reset_token = user.set_reset_token()
            print(f"[FORGOT PASSWORD] Token reset generato per utente {user.id}")
            
            print(f"[FORGOT PASSWORD] Tentativo invio email a: {user.email}")
            email_sent = send_reset_password_email(user.email, user.full_name, reset_token)
            
            if email_sent:
                print(f"[FORGOT PASSWORD] ✅ Email inviata con successo a {user.email}")
                flash('Ti abbiamo inviato un\'email con le istruzioni per reimpostare la tua password.', 'success')
            else:
                print(f"[FORGOT PASSWORD] ❌ Errore nell'invio email a {user.email}")
                flash('Si è verificato un errore nell\'invio dell\'email. Riprova più tardi.', 'danger')
        else:
            print(f"[FORGOT PASSWORD] ⚠️ Email non trovata nel database: {email}")
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

# =============== OAUTH AUTHENTICATION ROUTES ===============

@app.route('/auth/<provider>')
def oauth_login(provider):
    """Inizia il processo di autenticazione OAuth."""
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    # Check specific provider availability
    if provider == 'google':
        if not GOOGLE_OAUTH_ENABLED or not google:
            flash('Google OAuth non è attualmente configurato. Usa il login tradizionale.', 'warning')
            return redirect(url_for('login'))
        redirect_uri = url_for('oauth_callback', provider='google', _external=True)
        return google.authorize_redirect(redirect_uri)
        
    elif provider == 'apple':
        if not APPLE_OAUTH_ENABLED or not apple:
            flash('Apple OAuth non è attualmente configurato. Usa il login tradizionale.', 'warning')
            return redirect(url_for('login'))
        redirect_uri = url_for('oauth_callback', provider='apple', _external=True)
        return apple.authorize_redirect(redirect_uri)
        
    else:
        flash(f'Provider OAuth "{provider}" non supportato.', 'danger')
        return redirect(url_for('login'))

@app.route('/auth/<provider>/callback')
def oauth_callback(provider):
    """Gestisce il callback OAuth e crea/autentica l'utente."""
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    # Check if OAuth is enabled
    if not OAUTH_ENABLED:
        flash('OAuth non è configurato.', 'danger')
        return redirect(url_for('login'))
    
    try:
        if provider == 'google' and google:
            token = google.authorize_access_token()
            user_info = token.get('userinfo')
            if user_info:
                return handle_oauth_user(
                    provider='google',
                    oauth_id=user_info['sub'],
                    email=user_info['email'],
                    nome=user_info.get('given_name', ''),
                    cognome=user_info.get('family_name', ''),
                    avatar_url=user_info.get('picture', '')
                )
        
        elif provider == 'apple' and apple:
            token = apple.authorize_access_token()
            # Apple fornisce i dati dell'utente solo al primo login
            if request.form.get('user'):
                user_data = json.loads(request.form.get('user'))
                nome = user_data.get('name', {}).get('firstName', '')
                cognome = user_data.get('name', {}).get('lastName', '')
            else:
                nome = ''
                cognome = ''
            
            # Apple fornisce sempre l'email nell'ID token
            claims = token.get('id_token_claims', {})
            return handle_oauth_user(
                provider='apple',
                oauth_id=claims.get('sub'),
                email=claims.get('email', ''),
                nome=nome,
                cognome=cognome,
                avatar_url=''
            )
        
        else:
            flash('Provider OAuth non supportato.', 'danger')
            return redirect(url_for('login'))
            
    except Exception as e:
        print(f"[OAUTH ERROR] {provider}: {str(e)}")
        flash('Errore durante l\'autenticazione. Riprova più tardi.', 'danger')
        return redirect(url_for('login'))

def handle_oauth_user(provider, oauth_id, email, nome, cognome, avatar_url):
    """Gestisce la creazione o login di un utente OAuth."""
    try:
        # Cerca utente esistente tramite OAuth ID
        user = User.get_by_oauth(provider, oauth_id)
        
        if user:
            # Utente esistente, effettua login
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_full_name'] = user.full_name
            flash(f'Accesso effettuato con successo tramite {provider.title()}!', 'success')
            return redirect(url_for('home'))
        
        # Verifica se esiste già un utente con questa email
        existing_user = User.get_by_email(email)
        if existing_user:
            # Collega l'account OAuth all'utente esistente
            existing_user.oauth_provider = provider
            existing_user.oauth_id = oauth_id
            if avatar_url:
                existing_user.avatar_url = avatar_url
            existing_user.save()
            
            session['user_id'] = existing_user.id
            session['user_email'] = existing_user.email
            session['user_full_name'] = existing_user.full_name
            flash(f'Account collegato con successo a {provider.title()}!', 'success')
            return redirect(url_for('home'))
        
        # Crea nuovo utente
        # Se nome/cognome non sono forniti, usa l'email come fallback
        if not nome and not cognome:
            email_name = email.split('@')[0]
            nome = email_name.capitalize()
            cognome = 'User'
        elif not cognome:
            cognome = 'User'
        elif not nome:
            nome = 'User'
        
        new_user = User(
            nome=nome,
            cognome=cognome,
            email=email,
            password_hash=None,  # OAuth users don't have passwords
            is_verified=1,  # OAuth emails are pre-verified
            oauth_provider=provider,
            oauth_id=oauth_id,
            avatar_url=avatar_url
        )
        new_user.save()
        
        session['user_id'] = new_user.id
        session['user_email'] = new_user.email
        session['user_full_name'] = new_user.full_name
        flash(f'Account creato con successo tramite {provider.title()}! Benvenuto!', 'success')
        return redirect(url_for('home'))
        
    except Exception as e:
        print(f"[OAUTH USER HANDLE ERROR] {provider}: {str(e)}")
        flash('Errore durante la gestione dell\'account. Riprova più tardi.', 'danger')
        return redirect(url_for('login'))

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
    return render_template('services.html', title='Servizi')



@app.route('/quote')
def quote():
    """Pagina per richiedere un preventivo."""
    return render_template('quote.html', title='Preventivo')

@app.route('/gallery')
def gallery():
    """Pagina della galleria di immagini."""
    return render_template('gallery.html', title='Galleria')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Pagina dei contatti e gestione invio modulo."""
    if request.method == 'POST':
        try:
            # Check if it's a JSON request (AJAX)
            if request.is_json:
                data = request.get_json()
                nome = data.get('nome', '').strip()
                email = data.get('email', '').strip()
                telefono = data.get('telefono', '').strip()
                servizio = data.get('servizio', '')
                messaggio = data.get('messaggio', '').strip()
            else:
                # Regular form submission
                nome = request.form.get('nome', '').strip()
                email = request.form.get('email', '').strip()
                telefono = request.form.get('telefono', '').strip()
                servizio = request.form.get('servizio', '')
                messaggio = request.form.get('messaggio', '').strip()
            
            # Validazione base
            errors = []
            if not nome:
                errors.append('Il nome è obbligatorio')
            if not email:
                errors.append('L\'email è obbligatoria')
            elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                errors.append('Formato email non valido')
            if not messaggio:
                errors.append('Il messaggio è obbligatorio')
                
            if errors:
                if request.is_json:
                    return jsonify({'success': False, 'errors': errors}), 400
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('contact'))
            
            # Salva il messaggio nel database
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO contact_messages (nome, email, telefono, servizio, messaggio, data_invio)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, email, telefono, servizio, messaggio, datetime.now()))
            db.commit()
            
            # Risposta di successo
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Messaggio inviato con successo! Ti contatteremo presto.'
                })
            
            # Risposta per form submission normale
            flash('Messaggio inviato con successo! Ti contatteremo presto.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Errore nel sistema. Riprova più tardi.'}), 500
            flash('Errore nel sistema. Riprova più tardi.', 'error')
            return redirect(url_for('contact'))
    
    return render_template('contact.html', title='Contatti')


# =============== CHAT AI CON OPENROUTER ===============

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint per gestire le richieste della chat con OpenRouter."""
    if not request.is_json:
        return jsonify({'error': 'La richiesta deve essere in formato JSON'}), 400
    
    data = request.json
    user_message = data.get('message', '')
    chat_history = data.get('history', [])
    message_analysis = data.get('analysis', {})  # Analysis from frontend
    
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
    
    # Enhanced system prompt based on message analysis
    system_context = f"""Sei l'assistente virtuale ufficiale di Ristrutturazioni Morcianesi, azienda fondata nel 2003 a Morciano di Romagna (RN) e specializzata in ristrutturazioni edilizie di alta qualità. 

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

CONTEXT ANALYSIS:"""
    
    # Add context based on message analysis
    if message_analysis:
        intent = message_analysis.get('intent', '')
        keywords = message_analysis.get('keywords', [])
        urgency = message_analysis.get('urgency', 'normal')
        
        if intent:
            system_context += f"\n- Intento rilevato: {intent}"
        if keywords:
            system_context += f"\n- Parole chiave: {', '.join(keywords)}"
        if urgency == 'high':
            system_context += "\n- ALTA PRIORITÀ: Richiesta urgente, fornisci informazioni di contatto diretto"
    
    system_context += f"""

ISTRUZIONI IMPORTANTI:
- L'ora attuale è {now.strftime('%H:%M')} e oggi è {now.strftime('%A %d %B %Y')}
- Se l'utente saluta con "ciao", "salve", "buongiorno", ecc., rispondi sempre con "{time_greeting}" seguito dalla tua risposta
- Quando chiedi informazioni di contatto, menziona gli orari di lavoro dell'azienda
- Fornisci sempre informazioni accurate sugli orari, sui contatti e sui servizi
- Usa emoji appropriati per rendere la conversazione più friendly
- Formatta i numeri e i prezzi in modo chiaro
- Suggerisci sempre i nostri contatti quando appropriato

Il tuo compito è aiutare i clienti a ottenere informazioni sui servizi, stimare costi e tempi approssimativi per lavori di ristrutturazione, e raccogliere le informazioni necessarie per un preventivo dettagliato. Quando un utente chiede un preventivo, cerca di ottenere: tipo di lavoro, metratura, ubicazione, e tempistiche desiderate. 

Rispondi sempre in modo professionale, cordiale e conciso, rappresentando al meglio l'immagine di Ristrutturazioni Morcianesi."""
    
    # Preparazione dei messaggi per OpenRouter
    messages = [{"role": "system", "content": system_context}]
    
    # Aggiungi la cronologia della chat
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Aggiungi il messaggio dell'utente
    messages.append({"role": "user", "content": user_message})
    
    # Usa gpt-3.5-turbo con parametri ottimizzati
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 600,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }
    
    headers = {
        "Authorization": f"Bearer {app.config['OPENROUTER_API_KEY']}",
        "HTTP-Referer": request.host_url,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(app.config['OPENROUTER_URL'], headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Debug
        print(f"Risposta API: {json.dumps(result, indent=2)}")
        
        # Enhanced response processing
        if "choices" in result and len(result["choices"]) > 0:
            if "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                ai_message = result["choices"][0]["message"]["content"]
                
                # Generate smart suggestions based on the conversation
                suggestions = generate_smart_suggestions(user_message, ai_message, chat_history)
                
                # Enhanced response with additional context
                response_data = {
                    'message': ai_message,
                    'suggestions': suggestions,
                    'timestamp': now.isoformat(),
                    'context': {
                        'intent': message_analysis.get('intent', ''),
                        'urgent': message_analysis.get('urgency') == 'high'
                    }
                }
                
                return jsonify(response_data)
            else:
                ai_message = str(result.get("choices", [{}])[0])
        else:
            ai_message = "Mi dispiace, non sono riuscito a elaborare la tua richiesta. Puoi contattarci direttamente?"
        
        return jsonify({'message': ai_message})
        
    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta all'API: {e}")
        return jsonify({'error': 'Errore del servizio AI. Riprova più tardi.'}), 500
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        return jsonify({'error': 'Si è verificato un errore imprevisto.'}), 500

def generate_smart_suggestions(user_message, ai_response, chat_history):
    """Genera suggerimenti intelligenti basati sulla conversazione."""
    suggestions = []
    
    # Analizza il contenuto per generare suggerimenti pertinenti
    user_lower = user_message.lower()
    ai_lower = ai_response.lower()
    
    # Suggerimenti basati sul tipo di richiesta
    if any(word in user_lower for word in ['preventivo', 'costo', 'prezzo', 'quanto']):
        if 'bagno' in user_lower:
            suggestions.extend([
                "Che dimensioni ha il bagno?",
                "Preferisci doccia o vasca?",
                "Hai già i materiali in mente?"
            ])
        elif 'cucina' in user_lower:
            suggestions.extend([
                "Che stile di cucina preferisci?",
                "Quanti metri quadri ha la cucina?",
                "Vuoi cambiare anche gli elettrodomestici?"
            ])
        elif 'appartamento' in user_lower or 'casa' in user_lower:
            suggestions.extend([
                "Quanti metri quadri è l'appartamento?",
                "Quante stanze da ristrutturare?",
                "Quando vorresti iniziare i lavori?"
            ])
        else:
            suggestions.extend([
                "Puoi darmi più dettagli sul lavoro?",
                "In che zona si trova l'immobile?",
                "Hai un budget di riferimento?"
            ])
    
    elif any(word in user_lower for word in ['contatto', 'telefono', 'chiamare']):
        suggestions.extend([
            "Quali sono gli orari di lavoro?",
            "Posso avere un preventivo scritto?",
            "Fate sopralluoghi gratuiti?"
        ])
    
    elif any(word in user_lower for word in ['tempo', 'giorni', 'settimane']):
        suggestions.extend([
            "Dipende anche dalla stagione?",
            "Posso rimanere in casa durante i lavori?",
            "Come organizzate il cantiere?"
        ])
    
    # Suggerimenti generali se non ne abbiamo di specifici
    if not suggestions:
        suggestions = [
            "Richiedi un preventivo gratuito",
            "Vedi la nostra galleria di lavori",
            "Contattaci per un sopralluogo"
        ]
    
    # Limita a 3 suggerimenti
    return suggestions[:3]

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
            p.id, p.nome, p.email, p.telefono, p.indirizzo, 
            COALESCE(p.tipologia, p.tipo_lavoro) as tipologia, 
            p.descrizione, p.foto_paths, p.data_richiesta, p.stato, 
            p.risposta, p.data_risposta, (u.nome || ' ' || u.cognome) as richiesto_da
        FROM preventivi p
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.data_richiesta DESC
    """)
    preventivi = []
    rows = cursor.fetchall()
    
    # Processiamo i risultati per gestire i percorsi delle foto
    for row in rows:
        preventivo = dict(row)
        # Convertiamo i percorsi delle foto da JSON a list
        if preventivo.get('foto_paths'):
            try:
                preventivo['foto_paths'] = json.loads(preventivo['foto_paths'])
            except:
                preventivo['foto_paths'] = []
        else:
            preventivo['foto_paths'] = []
        preventivi.append(preventivo)
    
    return render_template('gestione_preventivi.html', title='Gestione Preventivi', preventivi=preventivi)


@app.route('/admin/cambia-stato-preventivo/<int:preventivo_id>', methods=['POST'])
@admin_required
def cambia_stato_preventivo(preventivo_id):
    """Endpoint per cambiare lo stato di un preventivo."""
    nuovo_stato = request.form.get('stato')
    
    if not nuovo_stato:
        flash('Stato mancante', 'error')
        return redirect(url_for('admin_preventivi'))
    
    # Controlla che lo stato sia valido
    stati_validi = ['Nuovo', 'In lavorazione', 'Risposto']
    if nuovo_stato not in stati_validi:
        flash('Stato non valido', 'error')
        return redirect(url_for('admin_preventivi'))
    
    # Aggiorna lo stato del preventivo
    db = get_db()
    try:
        db.execute(
            'UPDATE preventivi SET stato = ? WHERE id = ?',
            (nuovo_stato, preventivo_id)
        )
        db.commit()
        flash(f'Stato del preventivo aggiornato a {nuovo_stato}', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Si è verificato un errore: {str(e)}', 'error')
    
    return redirect(url_for('admin_preventivi'))


@app.route('/admin/rispondi-preventivo/<int:preventivo_id>', methods=['POST'])
@admin_required
def rispondi_preventivo(preventivo_id):
    """API endpoint per rispondere a un preventivo."""
    risposta = request.form.get('risposta')
    if not risposta:
        flash('La risposta non può essere vuota.', 'error')
        return redirect(url_for('admin_preventivi'))
    
    db = get_db()
    try:
        # Aggiorna il preventivo con la risposta e cambia lo stato
        db.execute(
            'UPDATE preventivi SET risposta = ?, data_risposta = ?, stato = ? WHERE id = ?',
            (risposta, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Risposto', preventivo_id)
        )
        db.commit()
        
        # Ottieni i dettagli del preventivo per inviare email
        cursor = db.cursor()
        cursor.execute(
            'SELECT nome, email FROM preventivi WHERE id = ?',
            (preventivo_id,)
        )
        preventivo = cursor.fetchone()
        
        if preventivo:
            # Invia email al cliente
            try:
                msg = Message("Risposta al tuo preventivo",
                             sender=app.config.get('MAIL_DEFAULT_SENDER', 'info@ristrutturazionimorcianesi.it'),
                             recipients=[preventivo['email']])
                msg.body = f"""
                Gentile {preventivo['nome']},
                
                Abbiamo elaborato la tua richiesta di preventivo e di seguito trovi la nostra risposta:
                
                {risposta}
                
                Per qualsiasi domanda, non esitare a contattarci.
                
                Cordiali saluti,
                Il team di Ristrutturazioni Morcianesi
                """
                mail.send(msg)
            except Exception as e:
                # Logga l'errore ma continua l'esecuzione
                print(f"Errore nell'invio dell'email: {str(e)}")
        
        flash('Risposta inviata con successo.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Si è verificato un errore: {str(e)}', 'error')
    
    return redirect(url_for('admin_preventivi'))

@app.route('/admin/contact-messages')
@admin_required
def admin_contact_messages():
    """Pagina admin per visualizzare i messaggi di contatto."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, nome, email, telefono, servizio, messaggio, data_invio, stato, risposta, data_risposta
        FROM contact_messages 
        ORDER BY data_invio DESC
    ''')
    messages = cursor.fetchall()
    
    return render_template('admin/contact_messages.html', title='Messaggi di Contatto', messages=messages)

@app.route('/admin/contact-messages/<int:message_id>/respond', methods=['POST'])
@admin_required
def admin_respond_contact(message_id):
    """Risponde a un messaggio di contatto."""
    response_text = request.form.get('risposta', '').strip()
    
    if not response_text:
        flash('La risposta non può essere vuota', 'error')
        return redirect(url_for('admin_contact_messages'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE contact_messages 
        SET risposta = ?, data_risposta = ?, stato = 'risposto'
        WHERE id = ?
    ''', (response_text, datetime.now(), message_id))
    db.commit()
    
    flash('Risposta inviata con successo', 'success')
    return redirect(url_for('admin_contact_messages'))

@app.route('/chat')
def chat_page():
    """Pagina della chat standalone."""
    return render_template('chat.html', title='Chat Preventivi')

# =============== TEST EMAIL SYSTEM ===============

@app.route('/test-email')
@admin_required
def test_email_system():
    """Endpoint per testare il sistema email (solo admin)."""
    return render_template('admin/test_email.html', title='Test Sistema Email')

@app.route('/test-email/send', methods=['POST'])
@admin_required
def send_test_email():
    """Invia un'email di test per verificare la configurazione."""
    test_email = request.form.get('test_email')
    
    if not test_email:
        return jsonify({'success': False, 'error': 'Email di test richiesta'})
    
    # Contenuto email di test
    subject = "Test Sistema Email - Ristrutturazioni Morcianesi"
    html_content = f'''
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h2 style="color: #1B9DD1;">Test Sistema Email</h2>
            <p>Questo è un messaggio di test per verificare il funzionamento del sistema email.</p>
            <p><strong>Data invio:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p><strong>Configurazione:</strong></p>
            <ul>
                <li>Server SMTP: {app.config['EMAIL_HOST']}</li>
                <li>Porta: {app.config['EMAIL_PORT']}</li>
                <li>Account: {app.config['EMAIL_USER']}</li>
            </ul>
            <p>Se ricevi questa email, il sistema funziona correttamente!</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="font-size: 0.9em; color: #777;">Test inviato dal pannello amministrativo<br>Ristrutturazioni Morcianesi</p>
        </div>
    </body>
    </html>
    '''
    
    # Tenta l'invio
    success = send_email(test_email, subject, html_content)
    
    if success:
        return jsonify({'success': True, 'message': f'Email di test inviata con successo a {test_email}'})
    else:
        return jsonify({'success': False, 'error': 'Errore nell\'invio dell\'email di test. Controlla i log del server.'})

@app.route('/load_chats', methods=['GET'])
@login_required
def load_chats():
    """Carica le chat salvate dell'utente."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Utente non autenticato'})
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT id, title, content, created_at 
            FROM user_chats 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (session['user_id'],))
        
        chats = []
        for row in cursor.fetchall():
            chats.append({
                'id': row['id'],
                'title': row['title'],
                'content': json.loads(row['content']) if row['content'] else [],
                'created_at': row['created_at']
            })
        
        return jsonify({'success': True, 'chats': chats})
        
    except Exception as e:
        print(f"Errore nel caricamento chat: {e}")
        return jsonify({'success': False, 'error': 'Errore nel caricamento'})

# =============== AVVIO DEL SERVER ===============

if __name__ == '__main__':
    print("🚀 Avvio del server Flask...")
    print("📁 Database:", app.config['DATABASE'])
    
    # Verifica database
    if not os.path.exists(app.config['DATABASE']):
        print("❌ Database non trovato! Esegui 'python init_db.py' per crearlo.")
        exit(1)
    else:
        print("✅ Database trovato")
    
    print("🌐 Server in avvio su http://127.0.0.1:5007")
    print("📧 Email server: " + app.config['EMAIL_HOST'])
    print("👤 Email account: " + app.config['EMAIL_USER'])
    print("🔧 Modalità: Produzione (debug disabilitato per stabilità)")
    
    app.run(
        debug=False,
        port=5007,
        host='127.0.0.1',
        threaded=True,
        use_reloader=False
    )