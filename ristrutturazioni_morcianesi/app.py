from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Gobettidegasperiano' 

# Percorso del database
DATABASE = os.path.join(app.root_path, 'database.db')

# --- Funzioni per la gestione del database ---
def get_db():
    """Connessione al database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Per ottenere i risultati come dizionari
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

# --- Classe User per gestire gli utenti ---
class User:
    def __init__(self, id=None, username=None, email=None, password_hash=None):

        self.id = id
        self.username = usernacaucame
        self.email = email
        self.password_hash = password_hash
    

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
                password_hash=user_data['password_hash']
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
                password_hash=user_data['password_hash']
            )
        return None

    def save(self):
        """Salva un nuovo utente nel database o aggiorna un utente esistente."""
        db = get_db()
        cursor = db.cursor()

        if self.id is None:
            # INSERT per un nuovo utente
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (self.username, self.email, self.password_hash)
            )
            self.id = cursor.lastrowid
        else:
            # UPDATE per un utente esistente
            cursor.execute(
                'UPDATE users SET username = ?, email = ?, password_hash = ? WHERE id = ?',
                (self.username, self.email, self.password_hash, self.id)
            )

        db.commit()
        return self

# --- Context Processor per l'anno nel footer e stato utente ---
@app.context_processor
def inject_global_vars():
    user_id = session.get('user_id')
    user = None
    if user_id:
        user = User.get_by_id(user_id) # Recupera l'oggetto utente se loggato
    return {
        'year': datetime.utcnow().year,
        'logged_in_user': user # Rende l'utente (o None) disponibile ai template
    }

# --- Route Principali ---
@app.route('/')
def home():
    return render_template('home.html', title="Home")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: # Controlla se l'utente è già loggato
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
        # Aggiungere una validazione email più robusta (es. regex) se necessario
        if not password or len(password) < 6 or len(password) > 60:
            errors.append("La password deve avere tra 6 e 60 caratteri.")
        if password != confirm_password:
            errors.append("Le password non corrispondono.")

        if User.get_by_email(email):
            errors.append('Un account con questa email esiste già. Prova ad accedere.')

        if not errors:
            hashed_password = generate_password_hash(password)
            new_user = User(id=None, username=username, email=email, password_hash=hashed_password)
            new_user.save()
            flash(f'Account creato con successo per {username}! Ora puoi accedere.', 'success')
            return redirect(url_for('login'))
        else:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', title='Registrazione',
                                   username_val=username, email_val=email)

    return render_template('register.html', title='Registrazione')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: # Controlla se l'utente è già loggato
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # remember = True if request.form.get('remember') else False
        errors = []

        if not email:
            errors.append("L'email è richiesta.")
        if not password:
            errors.append("La password è richiesta.")

        user = User.get_by_email(email)

        if not user or not check_password_hash(user.password_hash, password):
            if not errors:
                errors.append('Accesso non riuscito. Controlla email e password.')
        
        if not errors and user:
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_username'] = user.username
            flash('Accesso effettuato con successo!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page == url_for('quote_redirect', _external=False):
                 return redirect(url_for('pagina_preventivo_ai'))
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            for error in errors:
                flash(error, 'danger')
            return render_template('login.html', title='Accesso', email_val=email)

    return render_template('login.html', title='Accesso')

@app.route('/logout')
def logout():
    # Rimuovi le informazioni utente dalla sessione
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_username', None)
    # session.clear() # In alternativa, per pulire tutta la sessione
    flash('Ti sei disconnesso.', 'info')
    return redirect(url_for('home'))

@app.route('/quote')
def quote_redirect():
    if 'user_id' in session: # Controlla se l'utente è loggato
        return redirect(url_for('pagina_preventivo_ai'))
    else:
        flash('Per richiedere un preventivo, per favore accedi o crea un account.', 'info')
        return redirect(url_for('login', next=url_for('quote_redirect')))

@app.route('/pagina-preventivo-ai')
def pagina_preventivo_ai():
    if 'user_id' not in session: # Protezione manuale della route
        flash("Devi essere loggato per accedere a questa pagina.", "warning")
        return redirect(url_for('login', next=request.url))
    # L'utente è loggato, puoi recuperare i suoi dati dalla sessione se necessario
    # user_email = session.get('user_email')
    # user_username = session.get('user_username')
    return render_template('preventivo_ai_form.html', title="Richiedi Preventivo AI")

# --- Placeholder per le altre pagine della navbar ---
@app.route('/services')
def services():
    return "Pagina Servizi (placeholder)", 200

@app.route('/gallery')
def gallery():
    return "Pagina Galleria (placeholder)", 200

@app.route('/contact')
def contact():
    return "Pagina Contatti (placeholder)", 200

if __name__ == '__main__':
    app.run(debug=True)