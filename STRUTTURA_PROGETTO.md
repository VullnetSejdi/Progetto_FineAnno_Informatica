# Struttura del Progetto - Piattaforma Web Aziendale

## Struttura del Progetto

```
webapp-project/
├── main-application/                      # Applicazione principale
│   ├── app.py                            # Server Python Flask
│   ├── database.db                       # Database utenti e dati
│   ├── requirements.txt                  # Librerie necessarie
│   │
│   ├── templates/                        # Pagine HTML
│   │   ├── base.html                     # Template base comune
│   │   ├── home.html                     # Homepage
│   │   ├── login.html                    # Pagina login
│   │   ├── register.html                 # Pagina registrazione
│   │   ├── chat.html                     # Pagina messaggi
│   │   ├── request_form.html             # Modulo richiesta preventivi
│   │   ├── gallery.html                  # Galleria progetti
│   │   ├── contact.html                  # Modulo contatti
│   │   └── admin/                        # Pagine amministrazione
│   │
│   ├── static/                           # File statici
│   │   ├── style/                        # Fogli di stile CSS
│   │   │   ├── main.css                  # CSS principale
│   │   │   ├── auth.css                  # CSS autenticazione
│   │   │   └── modules/                  # CSS organizzato in moduli
│   │   │
│   │   ├── script/                       # File JavaScript
│   │   │   ├── forms.js                  # Controllo moduli
│   │   │   ├── gallery.js                # Galleria immagini
│   │   │   └── [altri script...]         # Altri script per il sito
│   │   │
│   │   ├── images/                       # Immagini del sito
│   │   │   ├── logo_aziendale.png        # Logo principale
│   │   │   ├── progetti_gallery/         # Foto progetti realizzati
│   │   │   └── icone_social.png          # Icone social media
│   │   │
│   │   ├── favicon/                      # Icone del sito
│   │   │   ├── favicon.ico               # Icona del browser
│   │   │   ├── phone.ico                 # Icona telefono
│   │   │   └── map.ico                   # Icona mappa
│   │   │
│   │   └── uploads/                      # File caricati dagli utenti
│   │
│   ├── admin_tools/                      # Strumenti amministrazione
│   └── scripts/                          # Script di utilità
│
└── README.md                             # Guida del progetto
```

## Architettura del Sistema

```
[UTENTE] → [PAGINE HTML] → [SERVER PYTHON] → [DATABASE]
           (templates/)     (app.py)         (database.db)
```

**Tecnologie:**
- **Backend:** Python + Flask
- **Frontend:** HTML5 + CSS3 + JavaScript
- **Database:** SQLite

---
