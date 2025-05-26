// Script per le funzionalità delle pagine di autenticazione - Versione Robusta

document.addEventListener('DOMContentLoaded', () => {
    console.log('🔄 Script di autenticazione caricato');
    
    // SIMPLIFIED PASSWORD TOGGLE - FIX THAT WORKS
    setupPasswordToggles();
    
    // Altre funzionalità del form di registrazione
    initializeRegistrationForm();
});

function setupPasswordToggles() {
    console.log('👁️ Setting up password toggles...');
    
    // Get all password toggle buttons
    const toggleBtns = document.querySelectorAll('.toggle-password');
    console.log(`Found ${toggleBtns.length} toggle buttons`);
    
    // Add click event to each button
    toggleBtns.forEach((btn, index) => {
        console.log(`Setting up button ${index + 1}`);
        
        btn.onclick = function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            console.log(`Button ${index + 1} clicked!`);
            
            // Find the password input in the same container
            const container = this.closest('.password-container');
            if (!container) {
                console.error('No password container found!');
                return;
            }
            
            const input = container.querySelector('input');
            if (!input) {
                console.error('No input found!');
                return;
            }
            
            console.log(`Current input type: ${input.type}`);
            
            // Toggle password visibility
            if (input.type === 'password') {
                input.type = 'text';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
                console.log('✅ Password shown');
            } else {
                input.type = 'password';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
                console.log('✅ Password hidden');
            }
        };
        
        console.log(`✅ Button ${index + 1} setup complete`);
    });
}

function initializeRegistrationForm() {
    const registerForm = document.getElementById('register-form') || document.querySelector('form');
    if (registerForm) {
        const passwordInput = document.getElementById('password');
        const confirmInput = document.getElementById('confirm_password');
        const meterFill = document.querySelector('.password-strength .meter-fill');
        const passwordMatchIndicator = document.getElementById('password-match-indicator');
        const submitButton = registerForm.querySelector('button[type="submit"]');
        
        // Validazione in tempo reale dei campi
        const nameInput = document.getElementById('nome');
        const surnameInput = document.getElementById('cognome');
        const emailInput = document.getElementById('email');
        
        // Validazione nome e cognome
        [nameInput, surnameInput].forEach(input => {
            if (input) {
                input.addEventListener('input', () => {
                    validateNameField(input);
                });
                input.addEventListener('blur', () => {
                    validateNameField(input);
                });
            }
        });
        
        // Validazione email
        if (emailInput) {
            emailInput.addEventListener('input', () => {
                validateEmailField(emailInput);
            });
            emailInput.addEventListener('blur', () => {
                validateEmailField(emailInput);
            });
        }
        
        // Validazione della forza della password
        if (passwordInput && meterFill) {
            passwordInput.addEventListener('input', () => {
                updatePasswordStrength(passwordInput, meterFill);
                checkPasswordMatch();
            });
        }
        
        // Validazione conferma password
        if (confirmInput) {
            confirmInput.addEventListener('input', checkPasswordMatch);
            confirmInput.addEventListener('blur', checkPasswordMatch);
        }
        
        function validateNameField(input) {
            const value = input.value.trim();
            const isValid = value.length >= 2 && value.length <= 50 && /^[a-zA-ZÀ-ÿ\s']{2,50}$/.test(value);
            
            updateFieldValidation(input, isValid);
            return isValid;
        }
        
        function validateEmailField(input) {
            const value = input.value.trim();
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            const isValid = emailRegex.test(value);
            
            updateFieldValidation(input, isValid);
            return isValid;
        }
        
        function updateFieldValidation(input, isValid) {
            if (input.value.trim() === '') {
                input.style.borderColor = '';
                return;
            }
            
            if (isValid) {
                input.style.borderColor = 'var(--success-color)';
                input.style.boxShadow = '0 0 0 3px rgba(72, 187, 120, 0.1)';
            } else {
                input.style.borderColor = 'var(--danger-color)';
                input.style.boxShadow = '0 0 0 3px rgba(245, 101, 101, 0.1)';
            }
        }
        
        function updatePasswordStrength(input, meterFill) {
            const value = input.value;
            let strength = 0;
            
            // Criteri di valutazione
            if (value.length >= 8) strength += 1;
            if (value.length >= 12) strength += 1;
            if (/[A-Z]/.test(value)) strength += 1;
            if (/[a-z]/.test(value)) strength += 1;
            if (/[0-9]/.test(value)) strength += 1;
            if (/[^A-Za-z0-9]/.test(value)) strength += 1;
            
            // Aggiorna il meter visivo
            const percentage = Math.min((strength / 6) * 100, 100);
            meterFill.style.width = percentage + '%';
            
            // Feedback sulla password
            const hintElement = document.querySelector('.password-strength .hint');
            if (hintElement) {
                if (value.length === 0) {
                    hintElement.textContent = 'La password deve contenere almeno 12 caratteri';
                    hintElement.style.color = 'var(--text-light)';
                } else if (strength < 3) {
                    hintElement.textContent = 'Password debole - Aggiungi caratteri speciali, numeri e maiuscole';
                    hintElement.style.color = 'var(--danger-color)';
                } else if (strength < 5) {
                    hintElement.textContent = 'Password media - Considera di renderla più lunga';
                    hintElement.style.color = 'var(--warning-color)';
                } else {
                    hintElement.textContent = 'Password forte!';
                    hintElement.style.color = 'var(--success-color)';
                }
            }
            
            return strength >= 4;
        }
        
        function checkPasswordMatch() {
            if (!passwordInput || !confirmInput || !passwordMatchIndicator) return;
            
            const password = passwordInput.value;
            const confirm = confirmInput.value;
            
            if (confirm.length === 0) {
                passwordMatchIndicator.classList.add('hidden');
                confirmInput.style.borderColor = '';
                return false;
            }
            
            const isMatch = password === confirm && password.length > 0;
            
            if (isMatch) {
                passwordMatchIndicator.classList.remove('hidden');
                passwordMatchIndicator.style.backgroundColor = 'var(--alert-success-background)';
                passwordMatchIndicator.style.color = 'var(--alert-success-text)';
                passwordMatchIndicator.style.borderColor = 'var(--alert-success-border)';
                passwordMatchIndicator.querySelector('span').textContent = 'Le password corrispondono';
                passwordMatchIndicator.querySelector('i').className = 'fas fa-check-circle';
                
                confirmInput.style.borderColor = 'var(--success-color)';
                confirmInput.style.boxShadow = '0 0 0 3px rgba(72, 187, 120, 0.1)';
            } else {
                passwordMatchIndicator.classList.remove('hidden');
                passwordMatchIndicator.style.backgroundColor = 'var(--alert-danger-background)';
                passwordMatchIndicator.style.color = 'var(--alert-danger-text)';
                passwordMatchIndicator.style.borderColor = 'var(--alert-danger-border)';
                passwordMatchIndicator.querySelector('span').textContent = 'Le password non corrispondono';
                passwordMatchIndicator.querySelector('i').className = 'fas fa-times-circle';
                
                confirmInput.style.borderColor = 'var(--danger-color)';
                confirmInput.style.boxShadow = '0 0 0 3px rgba(245, 101, 101, 0.1)';
            }
            
            return isMatch;
        }
        
        // Validazione submit del form
        registerForm.addEventListener('submit', (e) => {
            let isValid = true;
            
            // Valida tutti i campi
            if (nameInput && !validateNameField(nameInput)) isValid = false;
            if (surnameInput && !validateNameField(surnameInput)) isValid = false;
            if (emailInput && !validateEmailField(emailInput)) isValid = false;
            
            // Valida password
            const passwordStrong = updatePasswordStrength(passwordInput, meterFill);
            if (!passwordStrong) {
                isValid = false;
                showFormError('La password deve essere più forte');
            }
            
            // Valida corrispondenza password
            if (!checkPasswordMatch()) {
                isValid = false;
                showFormError('Le password non corrispondono');
            }
            
            if (!isValid) {
                e.preventDefault();
                submitButton.style.animation = 'shake 0.5s ease-in-out';
                setTimeout(() => {
                    submitButton.style.animation = '';
                }, 500);
            } else {
                // Mostra loading sul pulsante
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creazione account...';
                submitButton.disabled = true;
            }
        });
        
        function showFormError(message) {
            // Rimuovi eventuali errori precedenti
            const existingError = registerForm.querySelector('.form-error');
            if (existingError) {
                existingError.remove();
            }
            
            // Crea nuovo messaggio di errore
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger form-error';
            errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
            
            // Inserisci l'errore prima del pulsante submit
            const submitGroup = registerForm.querySelector('.form-group:last-of-type');
            submitGroup.parentNode.insertBefore(errorDiv, submitGroup);
            
            // Rimuovi l'errore dopo 5 secondi
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.remove();
                }
            }, 5000);
        }
    }
    
    // Animazioni di miglioramento UX
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.style.transform = 'scale(1.02)';
            input.parentElement.style.transition = 'transform 0.2s ease';
        });
        
        input.addEventListener('blur', () => {
            input.parentElement.style.transform = 'scale(1)';
        });
    });
    
    // Aggiungi animazione shake per errori
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
    `;
    document.head.appendChild(style);

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