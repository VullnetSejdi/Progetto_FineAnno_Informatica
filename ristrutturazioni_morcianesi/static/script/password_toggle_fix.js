// Simple and Working Password Toggle Fix

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 Password toggle script loaded');
    
    // Find all password toggle buttons
    const toggleButtons = document.querySelectorAll('.toggle-password');
    console.log(`Found ${toggleButtons.length} password toggle buttons`);
    
    // Add event listener to each button
    toggleButtons.forEach(function(button, index) {
        console.log(`Setting up button ${index + 1}`);
        
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log(`Password toggle button ${index + 1} clicked`);
            
            // Find the password container
            const container = this.closest('.password-container');
            if (!container) {
                console.error('Password container not found');
                return;
            }
            
            // Find the password input
            const input = container.querySelector('input');
            if (!input) {
                console.error('Password input not found');
                return;
            }
            
            // Toggle password visibility
            if (input.type === 'password') {
                input.type = 'text';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
                console.log('Password shown');
            } else {
                input.type = 'password';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
                console.log('Password hidden');
            }
        });
        
        console.log(`Button ${index + 1} event listener added successfully`);
    });
    
    console.log('✅ All password toggle buttons initialized');
});
