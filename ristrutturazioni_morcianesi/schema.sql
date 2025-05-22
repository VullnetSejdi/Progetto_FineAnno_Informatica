-- Schema del database per Ristrutturazioni Morcianesi

-- Pulizia delle tabelle esistenti
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS quotes;
DROP TABLE IF EXISTS contact_requests;
DROP TABLE IF EXISTS quote_requests;
DROP TABLE IF EXISTS saved_chats;
DROP TABLE IF EXISTS preventivi;

-- Tabella utenti per autenticazione e gestione account
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_verified INTEGER DEFAULT 0,
    verification_token TEXT,
    token_created_at TEXT,
    reset_token TEXT,
    reset_token_created_at TEXT,
    role TEXT DEFAULT 'user'
);

-- Tabella per preventivi generati
CREATE TABLE quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_type TEXT NOT NULL,
    square_meters TEXT NOT NULL,
    description TEXT,
    services TEXT,
    budget TEXT,
    quote_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id);

-- Tabella per richieste di contatto dal form
CREATE TABLE contact_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contact_requests_email ON contact_requests(email);

-- Tabella per richieste di preventivo dal form
CREATE TABLE quote_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT,
    service_type TEXT NOT NULL,
    area TEXT,
    details TEXT,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quote_requests_email ON quote_requests(email);

-- Tabella per conversazioni chat salvate dagli utenti
CREATE TABLE saved_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    messages TEXT NOT NULL, -- JSON serializzato contenente i messaggi
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_saved_chats_user_id ON saved_chats(user_id);

-- Tabella per i messaggi della chat
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT NOT NULL,
    response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Tabella per i preventivi
CREATE TABLE IF NOT EXISTS preventivi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    telefono TEXT NOT NULL,
    tipo_lavoro TEXT NOT NULL,
    descrizione TEXT,
    indirizzo TEXT,
    metratura TEXT,
    data_richiesta DATETIME DEFAULT CURRENT_TIMESTAMP,
    stato TEXT DEFAULT 'in attesa', -- Nuovi stati: 'in attesa', 'in elaborazione', 'completato', 'rifiutato'
    risposta TEXT,
    data_risposta DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);