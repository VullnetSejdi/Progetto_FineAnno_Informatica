// WORKING Counter Animation - Final Version
console.log('🔢 Counter animation script loaded');

function animateNumber(element, target, duration = 2000) {
    console.log(`🎯 Animating ${element.textContent} to ${target}`);
    
    let startTime = null;
    const startValue = 0;
    
    // Reset to 0
    element.textContent = '0';
    
    function animate(currentTime) {
        if (!startTime) startTime = currentTime;
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Simple easing
        const easeProgress = 1 - Math.pow(1 - progress, 2);
        const current = Math.round(startValue + (target - startValue) * easeProgress);
        
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            element.textContent = target;
            console.log(`✅ Animation complete: ${target}`);
        }
    }
    
    requestAnimationFrame(animate);
}

function startCounters() {
    console.log('🚀 Starting counter animations...');
    
    const counters = document.querySelectorAll('.stat-number[data-target]');
    console.log(`Found ${counters.length} counters with data-target`);
    
    if (counters.length === 0) {
        console.error('❌ No stat-number elements with data-target found!');
        return;
    }
    
    counters.forEach((counter, index) => {
        const target = parseInt(counter.getAttribute('data-target'));
        console.log(`Counter ${index + 1}: target = ${target}`);
        
        if (target && target > 0) {
            // Stagger the animations
            setTimeout(() => {
                animateNumber(counter, target, 2000);
            }, index * 400);
        }
    });
}

// Multiple ways to start the animation
function initCounters() {
    console.log('🔄 Initializing counters...');
    
    // Check if elements exist
    const statNumbers = document.querySelectorAll('.stat-number');
    const heroStats = document.querySelector('.hero-stats');
    
    console.log(`Found ${statNumbers.length} stat numbers`);
    console.log(`Hero stats container: ${heroStats ? 'Found' : 'NOT FOUND'}`);
    
    if (statNumbers.length > 0) {
        startCounters();
    } else {
        console.warn('⚠️ No stat numbers found, retrying in 1 second...');
        setTimeout(initCounters, 1000);
    }
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('📄 DOM loaded, starting counters in 1 second...');
        setTimeout(initCounters, 1000);
    });
} else {
    console.log('📄 DOM already ready, starting counters...');
    setTimeout(initCounters, 500);
}

// Global functions for testing
window.startCounters = startCounters;
window.animateCounters = startCounters;
window.initCounters = initCounters;
