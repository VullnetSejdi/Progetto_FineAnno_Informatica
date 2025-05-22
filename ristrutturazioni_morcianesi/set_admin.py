import sqlite3
import os
import sys

def set_admin_role(email):
    """
    Assegna il ruolo 'admin' a un utente specificato tramite email.
    
    Args:
        email (str): L'indirizzo email dell'utente da promuovere ad admin
    """
    # Percorso del database
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    
    # Connessione al database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica se l'utente esiste
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"Errore: Nessun utente trovato con l'email {email}")
        conn.close()
        return False
    
    # Aggiorna il ruolo dell'utente
    try:
        cursor.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
        conn.commit()
        print(f"Utente {email} promosso a admin con successo!")
        conn.close()
        return True
    except Exception as e:
        print(f"Errore durante l'aggiornamento del ruolo: {str(e)}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python set_admin.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    set_admin_role(email)