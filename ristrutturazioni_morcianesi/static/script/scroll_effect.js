// Gestisce l'effetto parallax e l'animazione del testo
window.addEventListener('scroll', () => {
    const parallaxSection = document.querySelector('.parallax-section');
    const parallaxBackground = document.querySelector('.parallax-background');
    const sectionPosition = parallaxSection.getBoundingClientRect();

    // Effetto parallax per l'immagine di sfondo
    if (sectionPosition.top < window.innerHeight && sectionPosition.bottom > 0) {
        const offset = window.scrollY - parallaxSection.offsetTop;
        parallaxBackground.style.transform = `translateY(${offset * 0.5}px)`;
    }

    // Mostra il contenuto quando la sezione è visibile
    if (sectionPosition.top < window.innerHeight - 200 && sectionPosition.bottom > 0) {
        parallaxSection.classList.add('visible');
    } else {
        parallaxSection.classList.remove('visible');
    }
});

// Gestisce la riduzione della barra di navigazione durante lo scrolling
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) { // Quando l'utente scorre oltre 50px
        navbar.classList.add('shrink');
    } else {
        navbar.classList.remove('shrink');
    }
});

// Gestisce il menu hamburger
const hamburger = document.querySelector('.hamburger');
const navbar = document.querySelector('.navbar');

hamburger.addEventListener('click', () => {
    navbar.classList.toggle('active');
});

// Evidenzia la sezione corrente nella navbar durante lo scroll
document.addEventListener('DOMContentLoaded', function() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.navbar nav a');

    function highlightNavigation() {
        let scrollPosition = window.scrollY;

        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href').endsWith(sectionId)) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }

    window.addEventListener('scroll', highlightNavigation);
});