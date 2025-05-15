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
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for, flash, 
    session, g, jsonify, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

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
    DEBUG=True
)

csrf = CSRFProtect(app)

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

# =============== ROUTE PRINCIPALI DEL SITO ===============

@app.route('/')
def home():
    """Pagina principale del sito."""
    return render_template('home.html', title='Ristrutturazioni Morcianesi - Home')

@app.route('/chat')
def standalone_chat():
    """Pagina dedicata per la chat preventivi."""
    return render_template('chat.html', title='Chat Preventivi - Ristrutturazioni Morcianesi')

@app.route('/chi-siamo')
def about():
    """Pagina Chi Siamo."""
    return render_template('about.html', title='Chi Siamo - Ristrutturazioni Morcianesi')

@app.route('/servizi')
def services():
    """Pagina dei servizi offerti."""
    return render_template('services.html', title='Servizi - Ristrutturazioni Morcianesi')

@app.route('/galleria')
def gallery():
    """Galleria dei lavori realizzati."""
    return render_template('gallery.html', title='Galleria - Ristrutturazioni Morcianesi')

@app.route('/contatti', methods=['GET', 'POST'])
def contact():
    """Pagina dei contatti con form di richiesta informazioni."""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        # Validazione input
        if not name or not email or not message:
            flash('Per favore, completa tutti i campi obbligatori.', 'danger')
            return render_template('contact.html', title='Contatti - Ristrutturazioni Morcianesi',
                                  name_val=name, email_val=email, phone_val=phone, message_val=message)
        
        # Salva la richiesta nel database
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO contact_requests (name, email, phone, message, created_at) VALUES (?, ?, ?, ?, ?)',
            (name, email, phone, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        db.commit()
        
        # Invia email di notifica agli amministratori
        admin_email = app.config['EMAIL_USER']
        subject = f'Nuova richiesta di contatto da {name}'
        
        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #1B9DD1;">Nuova richiesta di contatto</h2>
                <p><strong>Nome:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Telefono:</strong> {phone or 'Non fornito'}</p>
                <p><strong>Messaggio:</strong></p>
                <p style="background-color: #f9f9f9; padding: 10px; border-radius: 5px;">{message}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 0.9em; color: #777;">Questa email è stata generata automaticamente dal sito Ristrutturazioni Morcianesi.</p>
            </div>
        </body>
        </html>
        '''
        
        send_email(admin_email, subject, html_content)
        
        # Invia email di conferma al cliente
        client_subject = 'Abbiamo ricevuto la tua richiesta - Ristrutturazioni Morcianesi'
        
        client_html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #1B9DD1;">Grazie per averci contattato!</h2>
                <p>Gentile {name},</p>
                <p>Abbiamo ricevuto la tua richiesta e ti ringraziamo per averci contattato.</p>
                <p>Un nostro operatore ti risponderà il prima possibile all'indirizzo email {email}.</p>
                <p>Ecco un riepilogo della tua richiesta:</p>
                <p style="background-color: #f9f9f9; padding: 10px; border-radius: 5px;">{message}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 0.9em; color: #777;">Cordiali saluti,<br>Il team di Ristrutturazioni Morcianesi</p>
            </div>
        </body>
        </html>
        '''
        
        send_email(email, client_subject, client_html_content)
        
        flash('Grazie per il tuo messaggio! Ti risponderemo al più presto.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html', title='Contatti - Ristrutturazioni Morcianesi')

@app.route('/preventivo', methods=['GET', 'POST'])
def quote():
    """Pagina per la richiesta di un preventivo."""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        service_type = request.form.get('service_type')
        area = request.form.get('area')
        details = request.form.get('details')
        
        # Validazione input
        if not name or not email or not phone or not service_type:
            flash('Per favore, completa tutti i campi obbligatori.', 'danger')
            return render_template('quote.html', title='Richiedi Preventivo - Ristrutturazioni Morcianesi')
        
        # Salva la richiesta di preventivo nel database
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO quote_requests (name, email, phone, address, service_type, area, details, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (name, email, phone, address, service_type, area, details, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        db.commit()
        
        # Invia email di notifica agli amministratori
        admin_email = app.config['EMAIL_USER']
        subject = f'Nuova richiesta di preventivo da {name}'
        
        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #1B9DD1;">Nuova richiesta di preventivo</h2>
                <p><strong>Nome:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Telefono:</strong> {phone}</p>
                <p><strong>Indirizzo:</strong> {address or 'Non fornito'}</p>
                <p><strong>Tipo di servizio:</strong> {service_type}</p>
                <p><strong>Metratura:</strong> {area or 'Non fornita'} mq</p>
                <p><strong>Dettagli aggiuntivi:</strong></p>
                <p style="background-color: #f9f9f9; padding: 10px; border-radius: 5px;">{details or 'Nessun dettaglio fornito'}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 0.9em; color: #777;">Questa email è stata generata automaticamente dal sito Ristrutturazioni Morcianesi.</p>
            </div>
        </body>
        </html>
        '''
        
        send_email(admin_email, subject, html_content)
        
        # Invia email di conferma al cliente
        client_subject = 'Richiesta di preventivo ricevuta - Ristrutturazioni Morcianesi'
        
        client_html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #1B9DD1;">Grazie per la tua richiesta di preventivo!</h2>
                <p>Gentile {name},</p>
                <p>Abbiamo ricevuto la tua richiesta di preventivo e ti ringraziamo per averci scelto.</p>
                <p>Un nostro tecnico valuterà la tua richiesta e ti contatterà entro 48 ore lavorative per un preventivo dettagliato.</p>
                <p>Ecco un riepilogo della tua richiesta:</p>
                <ul>
                    <li><strong>Tipo di servizio:</strong> {service_type}</li>
                    <li><strong>Metratura:</strong> {area or 'Non fornita'} mq</li>
                    <li><strong>Indirizzo:</strong> {address or 'Non fornito'}</li>
                </ul>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 0.9em; color: #777;">Cordiali saluti,<br>Il team di Ristrutturazioni Morcianesi</p>
            </div>
        </body>
        </html>
        '''
        
        send_email(email, client_subject, client_html_content)
        
        flash('Grazie per la richiesta di preventivo! Ti contatteremo il prima possibile.', 'success')
        return redirect(url_for('quote'))
        
    return render_template('quote.html', title='Richiedi Preventivo - Ristrutturazioni Morcianesi')

# =============== PAGINE DI ERRORE PERSONALIZZATE ===============

@app.errorhandler(404)
def page_not_found(e):
    """Gestione errore 404: Pagina non trovata."""
    return render_template('errors/404.html', title='Pagina non trovata'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Gestione errore 500: Errore interno del server."""
    return render_template('errors/500.html', title='Errore del server'), 500

# =============== AVVIO APPLICAZIONE ===============

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])