"""
Script di migrazione del database
--------------------------------
Questo script aggiorna la struttura del database senza perdere i dati esistenti.
Aggiunge la tabella 'preventivi' e il campo 'role' agli utenti.
"""

import sqlite3
import os

DB_PATH = 'database.db'

def migrate_database():
    """Esegue la migrazione del database."""
    print("Avvio migrazione database...")
    
    # Connessione al database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Controllo se la colonna 'role' esiste nella tabella users
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'role' not in columns:
            print("Aggiunta colonna 'role' alla tabella 'users'...")
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            print("Colonna 'role' aggiunta con successo.")
        else:
            print("La colonna 'role' esiste già nella tabella 'users'.")
        
        # Controllo se la tabella preventivi esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='preventivi'")
        if not cursor.fetchone():
            print("Creazione tabella 'preventivi'...")
            cursor.execute('''
            CREATE TABLE preventivi (
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
                stato TEXT DEFAULT 'in attesa',
                risposta TEXT,
                data_risposta DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            print("Tabella 'preventivi' creata con successo.")
        else:
            print("La tabella 'preventivi' esiste già.")
            
        # Controllo se la tabella 'chat_messages' esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
        if not cursor.fetchone():
            print("Creazione tabella 'chat_messages'...")
            cursor.execute('''
            CREATE TABLE chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT NOT NULL,
                response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            print("Tabella 'chat_messages' creata con successo.")
        else:
            print("La tabella 'chat_messages' esiste già.")
            
        conn.commit()
        print("Migrazione completata con successo!")
        
    except Exception as e:
        conn.rollback()
        print(f"Errore durante la migrazione: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()