// Script per le funzionalità delle pagine di autenticazione

document.addEventListener('DOMContentLoaded', () => {
    // Funzionalità per mostrare/nascondere password
    const toggleButtons = document.querySelectorAll('.toggle-password');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', () => {
            const input = button.previousElementSibling;
            if (input.type === 'password') {
                input.type = 'text';
                button.classList.remove('fa-eye');
                button.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                button.classList.remove('fa-eye-slash');
                button.classList.add('fa-eye');
            }
        });
    });

    // Validazione per il form di registrazione
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        const passwordInput = document.getElementById('password');
        const confirmInput = document.getElementById('confirm_password');
        const meter = document.querySelector('.password-strength .meter');
        
        // Validazione della forza della password
        passwordInput.addEventListener('input', () => {
            const value = passwordInput.value;
            let strength = 0;
            
            if (value.length >= 6) strength += 1;
            if (value.length >= 8) strength += 1;
            if (/[A-Z]/.test(value)) strength += 1;
            if (/[0-9]/.test(value)) strength += 1;
            if (/[^A-Za-z0-9]/.test(value)) strength += 1;
            
            // Aggiorna il meter visivo
            const colors = ['#ddd', '#f44336', '#ff9800', '#4caf50', '#2196f3', '#673ab7'];
            const widths = ['0%', '20%', '40%', '60%', '80%', '100%'];
            
            meter.style.width = widths[strength];
            meter.style.backgroundColor = colors[strength];
        });
        
        // Validazione submit del form
        registerForm.addEventListener('submit', (e) => {
            if (passwordInput.value !== confirmInput.value) {
                e.preventDefault();
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-danger';
                errorDiv.textContent = 'Le password non coincidono. Riprova.';
                
                // Rimuovi messaggi di errore precedenti se presenti
                const existingAlerts = registerForm.querySelectorAll('.alert');
                existingAlerts.forEach(alert => alert.remove());
                
                // Inserisci il nuovo messaggio di errore all'inizio del form
                registerForm.insertBefore(errorDiv, registerForm.firstChild);
                
                // Scorri in alto per vedere l'errore
                window.scrollTo(0, 0);
            }
        });
    }

    // Funzione per cambiare tema
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }

    // Funzione per impostare il tema in base alle preferenze di sistema
    function setThemeBasedOnSystemPreferences() {
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('theme');

        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        } else {
            document.documentElement.setAttribute('data-theme', prefersDarkScheme ? 'dark' : 'light');
        }
    }

    // Ascolta i cambiamenti nelle preferenze di sistema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        const newTheme = e.matches ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    // Imposta il tema iniziale in base al valore salvato in localStorage
    (function setInitialTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
    })();

    // Aggiungi un listener al pulsante per cambiare tema
    const themeToggleButton = document.getElementById('theme-toggle');
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', toggleTheme);
    }
});