#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/vullnetsejdi/Progetto_FineAnno_Informatica/ristrutturazioni_morcianesi')

from app import app

if __name__ == '__main__':
    print("🚀 Avvio del server Flask...")
    print("📁 Database:", app.config['DATABASE'])
    
    # Verifica database
    if not os.path.exists(app.config['DATABASE']):
        print("❌ Database non trovato!")
        sys.exit(1)
    else:
        print("✅ Database trovato")
    
    # Avvia server
    try:
        print("🌐 Server in avvio su http://127.0.0.1:5004")
        app.run(
            debug=False,
            port=5004,
            host='127.0.0.1',
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ Errore nell'avvio del server: {e}")
        sys.exit(1)
