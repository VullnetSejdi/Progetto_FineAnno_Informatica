import os
import sqlite3

# Percorso del database e dello schema
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def main():
    """Crea il database e le tabelle leggendo lo schema SQL"""
    print(f"Inizializzazione database in: {DB_PATH}")
    
    # Rimuovi il database se esiste
    if os.path.exists(DB_PATH):
        print(f"Rimozione database esistente: {DB_PATH}")
        os.remove(DB_PATH)
    
    # Leggi lo schema SQL
    print(f"Lettura dello schema da: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()
    
    # Crea una nuova connessione e applica lo schema
    print("Creazione del nuovo database...")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.commit()
    conn.close()
    
    print("Database inizializzato con successo!")
    
    # Verifica che il database sia stato creato
    if os.path.exists(DB_PATH):
        print(f"Verifica: il file database.db è stato creato ({os.path.getsize(DB_PATH)} bytes)")
        
        # Verifica le tabelle
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tabelle create: {[table[0] for table in tables]}")
        conn.close()
    else:
        print("ERRORE: Il database non è stato creato!")

if __name__ == "__main__":
    main()