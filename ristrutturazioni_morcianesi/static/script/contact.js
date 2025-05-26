/*---------------------------------------
  CONTACT FORM JAVASCRIPT FUNCTIONALITY
----------------------------------------*/

document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        // Form validation
        const inputs = contactForm.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', clearErrorState);
        });
        
        // Form submission
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (validateForm()) {
                submitForm();
            }
        });
    }
    
    function validateField(e) {
        const field = e.target;
        const value = field.value.trim();
        const fieldType = field.type;
        const fieldName = field.name;
        
        clearErrorState(e);
        
        // Required field validation
        if (field.hasAttribute('required') && !value) {
            showFieldError(field, 'Questo campo è obbligatorio');
            return false;
        }
        
        // Email validation
        if (fieldType === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                showFieldError(field, 'Inserisci un indirizzo email valido');
                return false;
            }
        }
        
        // Phone validation
        if (fieldName === 'telefono' && value) {
            const phoneRegex = /^[\+]?[0-9\s\-\(\)]{8,}$/;
            if (!phoneRegex.test(value)) {
                showFieldError(field, 'Inserisci un numero di telefono valido');
                return false;
            }
        }
        
        return true;
    }
    
    function validateForm() {
        let isValid = true;
        const inputs = contactForm.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            if (!validateField({target: input})) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    function showFieldError(field, message) {
        field.classList.add('error');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        
        // Add new error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }
    
    function clearErrorState(e) {
        const field = e.target;
        field.classList.remove('error');
        
        const errorMessage = field.parentNode.querySelector('.error-message');
        if (errorMessage) {
            errorMessage.remove();
        }
    }
    
    function submitForm() {
        const submitBtn = contactForm.querySelector('.form-submit');
        const originalText = submitBtn.textContent;
        
        // Show loading state
        submitBtn.textContent = 'Invio in corso...';
        submitBtn.disabled = true;
        
        // Collect form data
        const formData = new FormData(contactForm);
        
        // Submit form via AJAX
        fetch('/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                nome: formData.get('nome'),
                email: formData.get('email'),
                telefono: formData.get('telefono'),
                servizio: formData.get('servizio'),
                messaggio: formData.get('messaggio')
            })
        })
        .then(response => response.json())
        .then(data => {
            // Reset button
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            
            if (data.success) {
                // Show success message
                showSuccessMessage(data.message);
                // Reset form
                contactForm.reset();
            } else {
                // Show error message
                showErrorMessage(data.message || 'Errore durante l\'invio del messaggio');
                
                // Show field-specific errors if available
                if (data.errors) {
                    data.errors.forEach(error => {
                        console.error('Validation error:', error);
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Reset button
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            
            // Show error message
            showErrorMessage('Errore di connessione. Riprova più tardi.');
        });
    }
    
    function showSuccessMessage(message = 'Messaggio inviato con successo! Ti contatteremo presto.') {
        // Remove existing messages
        const existingMessage = document.querySelector('.form-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // Create success message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'form-message success';
        messageDiv.innerHTML = `
            <i>✓</i>
            <span>${message}</span>
        `;
        
        contactForm.insertBefore(messageDiv, contactForm.firstChild);
        
        // Remove message after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
    
    function showErrorMessage(message) {
        // Remove existing messages
        const existingMessage = document.querySelector('.form-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // Create error message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'form-message error';
        messageDiv.innerHTML = `
            <i>✗</i>
            <span>${message}</span>
        `;
        
        contactForm.insertBefore(messageDiv, contactForm.firstChild);
        
        // Remove message after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
    
    // Animate form elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe contact items
    const contactItems = document.querySelectorAll('.contact-item, .contact-form, .business-hours');
    contactItems.forEach(item => {
        observer.observe(item);
    });
});
