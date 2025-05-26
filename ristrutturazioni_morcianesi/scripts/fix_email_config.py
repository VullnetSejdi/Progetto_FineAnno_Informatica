#!/usr/bin/env python3
"""
Script per verificare e aggiornare la configurazione email Gmail
"""

import sys
import os
from datetime import datetime

def check_gmail_app_password():
    """Guida per verificare la password dell'app Gmail."""
    print("🔐 VERIFICA PASSWORD APP GMAIL")
    print("=" * 50)
    
    print("📋 STEPS per verificare/aggiornare la password dell'app Gmail:")
    print()
    print("1️⃣ Vai su https://myaccount.google.com/")
    print("2️⃣ Clicca su 'Sicurezza' nel menu laterale")
    print("3️⃣ Sotto 'Accesso a Google', clicca su 'Password per le app'")
    print("4️⃣ Se non vedi l'opzione, attiva prima la 'Verifica in due passaggi'")
    print("5️⃣ Seleziona 'App' > 'Mail'")
    print("6️⃣ Seleziona 'Dispositivo' > 'Altro' > scrivi 'Ristrutturazioni Morcianesi'")
    print("7️⃣ Clicca 'Genera'")
    print("8️⃣ Copia la password di 16 caratteri (senza spazi)")
    print()
    print("⚠️  IMPORTANTE:")
    print("- La password dell'app è diversa dalla password Gmail normale")
    print("- Deve essere di 16 caratteri senza spazi")
    print("- L'autenticazione a 2 fattori deve essere ATTIVA")

def show_current_config():
    """Mostra la configurazione email attuale."""
    print("\n📊 CONFIGURAZIONE EMAIL ATTUALE")
    print("=" * 50)
    
    sys.path.insert(0, '/Users/vullnetsejdi/Progetto_FineAnno_Informatica/ristrutturazioni_morcianesi')
    
    try:
        from app import app
        
        with app.app_context():
            print(f"📧 Server SMTP: {app.config['EMAIL_HOST']}")
            print(f"🔌 Porta: {app.config['EMAIL_PORT']}")
            print(f"👤 Account: {app.config['EMAIL_USER']}")
            print(f"🔑 Password attuale: {app.config['EMAIL_PASSWORD'][:4]}...{app.config['EMAIL_PASSWORD'][-4:]}")
            print(f"📏 Lunghezza password: {len(app.config['EMAIL_PASSWORD'])} caratteri")
            
            # Verifica formato password app
            password = app.config['EMAIL_PASSWORD']
            if len(password) == 16 and password.isalnum():
                print("✅ Formato password app: CORRETTO")
            else:
                print("❌ Formato password app: POTREBBE ESSERE ERRATO")
                print("   (Dovrebbe essere 16 caratteri alfanumerici)")
                
    except Exception as e:
        print(f"❌ Errore nel leggere la configurazione: {e}")

def update_email_config():
    """Guida per aggiornare la configurazione email."""
    print("\n🔧 AGGIORNAMENTO CONFIGURAZIONE")
    print("=" * 50)
    
    print("Per aggiornare la configurazione email:")
    print()
    print("1️⃣ Apri il file app.py")
    print("2️⃣ Cerca la sezione 'app.config.update('")
    print("3️⃣ Aggiorna questi valori:")
    print("   - EMAIL_USER: 'tua-email@gmail.com'")
    print("   - EMAIL_PASSWORD: 'password-app-16-caratteri'")
    print("   - MAIL_USERNAME: 'tua-email@gmail.com' (stesso di EMAIL_USER)")
    print("   - MAIL_PASSWORD: 'password-app-16-caratteri' (stesso di EMAIL_PASSWORD)")
    print("   - MAIL_DEFAULT_SENDER: 'tua-email@gmail.com' (stesso di EMAIL_USER)")
    print()
    print("4️⃣ Salva il file e riavvia il server")

def test_quick_connection():
    """Test rapido della connessione email."""
    print("\n⚡ TEST RAPIDO CONNESSIONE")
    print("=" * 50)
    
    sys.path.insert(0, '/Users/vullnetsejdi/Progetto_FineAnno_Informatica/ristrutturazioni_morcianesi')
    
    try:
        from app import app
        import smtplib
        
        with app.app_context():
            print("🔌 Tentativo connessione SMTP...")
            
            server = smtplib.SMTP(app.config['EMAIL_HOST'], app.config['EMAIL_PORT'])
            server.starttls()
            
            print("🔐 Tentativo autenticazione...")
            server.login(app.config['EMAIL_USER'], app.config['EMAIL_PASSWORD'])
            
            server.quit()
            print("✅ CONNESSIONE E AUTENTICAZIONE RIUSCITE!")
            print("📧 Il sistema email è configurato correttamente")
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ ERRORE DI AUTENTICAZIONE: {e}")
        print("\n🔧 SOLUZIONI:")
        print("- Rigenera una nuova password per app Gmail")
        print("- Verifica che l'autenticazione a 2 fattori sia attiva")
        print("- Controlla che l'account non sia bloccato")
        
    except Exception as e:
        print(f"❌ ERRORE: {e}")
        print(f"Tipo: {type(e).__name__}")

def common_issues_and_solutions():
    """Lista dei problemi comuni e soluzioni."""
    print("\n🩺 PROBLEMI COMUNI E SOLUZIONI")
    print("=" * 50)
    
    problems = [
        {
            "problem": "❌ SMTPAuthenticationError (535, '5.7.8 Username and Password not accepted')",
            "solutions": [
                "Rigenera una nuova password per app Gmail",
                "Verifica che l'autenticazione a 2 fattori sia attiva",
                "Controlla che l'email sia scritta correttamente"
            ]
        },
        {
            "problem": "❌ Le email non arrivano (ma nessun errore)",
            "solutions": [
                "Controlla la cartella spam del destinatario",
                "Verifica che Gmail non abbia limiti giornalieri",
                "Aspetta qualche minuto (a volte c'è ritardo)"
            ]
        },
        {
            "problem": "❌ Connessione timeout",
            "solutions": [
                "Verifica la connessione internet",
                "Controlla se il firewall blocca la porta 587",
                "Prova a cambiare rete (es. hotspot mobile)"
            ]
        },
        {
            "problem": "❌ Password non accettata nonostante sia corretta",
            "solutions": [
                "L'account potrebbe essere temporaneamente bloccato",
                "Accedi a Gmail da browser per verificare",
                "Attendi qualche ora e riprova"
            ]
        }
    ]
    
    for i, item in enumerate(problems, 1):
        print(f"\n{i}. {item['problem']}")
        for solution in item['solutions']:
            print(f"   • {solution}")

def main():
    """Funzione principale."""
    print("🔧 CONFIGURAZIONE EMAIL GMAIL")
    print("Ristrutturazioni Morcianesi")
    print("Data:", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    print("🔄" * 25)
    
    # Mostra configurazione attuale
    show_current_config()
    
    # Test rapido
    test_quick_connection()
    
    # Guida password app
    check_gmail_app_password()
    
    # Guida aggiornamento config
    update_email_config()
    
    # Problemi comuni
    common_issues_and_solutions()
    
    print(f"\n{'🔄' * 25}")
    print("🏁 GUIDA COMPLETATA")
    print("\n📞 Se i problemi persistono:")
    print("1. Prova con un altro account Gmail")
    print("2. Verifica le impostazioni di sicurezza dell'account")
    print("3. Contatta il supporto Google se necessario")

if __name__ == '__main__':
    main()
