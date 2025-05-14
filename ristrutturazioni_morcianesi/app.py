from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import sqlite3
import os
import re
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Gobettidegasperiano' 
csrf = CSRFProtect(app)

# Configurazione email
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'ristruttura.morcianesi.verifica@gmail.com'
EMAIL_PASSWORD = 'mgtcrlketbprtoin'

# Percorso del database
DATABASE = os.path.join(app.root_path, 'database.db')

# --- Funzioni per la gestione del database ---
def get_db():
    """Connessione al database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
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
    print('Database inizializzato.')

# --- Helper function ---
def safe_get(row, key, default=None):
    """Helper per ottenere valori da sqlite3.Row con default per colonne mancanti."""
    try:
        return row[key]
    except (IndexError, KeyError):
        return default

# --- Funzione per inviare email ---
def send_email(to_email, subject, html_content):
    """Funzione generica per inviare email."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
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
    <body>
        <h2>Benvenuto su Ristrutturazioni Morcianesi, {username}!</h2>
        <p>Grazie per esserti registrato. Per completare la registrazione, verifica il tuo indirizzo email cliccando sul link qui sotto:</p>
        <p><a href="{verification_url}">Verifica il tuo account</a></p>
        <p>Oppure copia questo link nel tuo browser:</p>
        <p>{verification_url}</p>
        <p>Il link scadrà tra 24 ore.</p>
        <p>Se non hai richiesto questa registrazione, ignora questa email.</p>
        <p>Cordiali saluti,<br>Il team di Ristrutturazioni Morcianesi</p>
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
    <body>
        <h2>Reset Password - Ristrutturazioni Morcianesi</h2>
        <p>Ciao {username},</p>
        <p>Hai richiesto il reset della tua password. Clicca sul link qui sotto per impostare una nuova password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>Oppure copia questo link nel tuo browser:</p>
        <p>{reset_url}</p>
        <p>Il link scadrà tra 1 ora.</p>
        <p>Se non hai richiesto il reset della password, ignora questa email.</p>
        <p>Cordiali saluti,<br>Il team di Ristrutturazioni Morcianesi</p>
    </body>
    </html>
    '''
    
    return send_email(user_email, subject, html_content)

# --- Classe User per gestire gli utenti ---
class User:
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

# --- Context Processor per l'anno nel footer e stato utente ---
@app.context_processor
def inject_global_vars():
    user_id = session.get('user_id')
    user = None
    if user_id:
        user = User.get_by_id(user_id)
    return {
        'year': datetime.utcnow().year,
        'logged_in_user': user
    }

# --- Route Principali ---
@app.route('/')
def home():
    return render_template('home.html', title="Home")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        errors = []

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
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_username', None)
    flash('Ti sei disconnesso.', 'info')
    return redirect(url_for('home'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
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

# --- Pagine principali del sito ---
@app.route('/services')
def services():
    return render_template('services.html', title="I Nostri Servizi")

@app.route('/gallery')
def gallery():
    return render_template('gallery.html', title="Galleria Progetti")

@app.route('/contact')
def contact():
    return render_template('contact.html', title="Contattaci")

@app.route('/quote')
def quote():
    if 'user_id' not in session:
        flash("Per richiedere un preventivo, per favore accedi o crea un account.", "info")
        return redirect(url_for('login', next=request.url))
    
    return render_template('quote.html', title="Richiedi Preventivo")

if __name__ == '__main__':
    app.run(debug=True)