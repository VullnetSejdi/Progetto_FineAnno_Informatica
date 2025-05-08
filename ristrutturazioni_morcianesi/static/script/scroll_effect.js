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