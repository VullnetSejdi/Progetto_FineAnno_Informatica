/*---------------------------------------
  SERVICES PAGE - INTERACTIVE FUNCTIONALITY
----------------------------------------*/

// Animation and Interaction Controller
class ServicesController {
    constructor() {
        // Run startup inspection to diagnose potential issues
        this.inspectElementStatus();
        
        this.init();
        this.setupIntersectionObserver();
        this.setupCounterAnimations();
        this.setupParallaxEffects();
        this.setupServiceCardInteractions();
        this.setupModalSystem();
        this.setupAdvancedInteractions();
        this.setupResponsiveFeatures();
    }
    
    // Startup inspection to diagnose issues
    inspectElementStatus() {
        console.log('=== SERVICES PAGE STARTUP INSPECTION ===');
        console.log('Document ready state:', document.readyState);
        
        // Check hero elements
        const titleLines = document.querySelectorAll('.title-line');
        const subtitle = document.querySelector('.hero-subtitle');
        const heroStats = document.querySelector('.hero-stats');
        const statNumbers = document.querySelectorAll('.stat-number');
        
        console.log(`Found ${titleLines.length} title lines`);
        console.log(`Subtitle found: ${subtitle ? true : false}`);
        console.log(`Hero stats found: ${heroStats ? true : false}`);
        console.log(`Found ${statNumbers.length} stat numbers`);
        
        if (titleLines.length > 0) {
            const firstLine = titleLines[0];
            const styles = window.getComputedStyle(firstLine);
            console.log(`First title line initial state: opacity=${styles.opacity}, transform=${styles.transform}`);
        }
        
        if (subtitle) {
            const styles = window.getComputedStyle(subtitle);
            console.log(`Subtitle initial state: opacity=${styles.opacity}, transform=${styles.transform}`);
        }
        
        if (heroStats) {
            const styles = window.getComputedStyle(heroStats);
            console.log(`Hero stats initial state: opacity=${styles.opacity}, transform=${styles.transform}`);
        }
        
        if (statNumbers.length > 0) {
            statNumbers.forEach((stat, index) => {
                const target = stat.getAttribute('data-target');
                console.log(`Stat ${index}: data-target="${target}", text="${stat.textContent.trim()}"`);
            });
        }
        
        console.log('=== INSPECTION COMPLETE ===');
    }

    init() {
        // Initialize page
        console.log('Services Page Initialized');
        console.log('Document ready state:', document.readyState);
        
        // Start animations IMMEDIATELY - no delay!
        this.animateHeroElements();
        
        // Also trigger counter animations independently to ensure they work
        setTimeout(() => {
            console.log('Starting independent counter animations...');
            this.triggerCounterAnimations();
        }, 10000); // Ritardo di 10 secondi
        
        this.setupMouseParallax();
    }

    // Hero Section Animations
    animateHeroElements() {
        console.log('Starting hero animations'); // Debug log
        
        // Start animations IMMEDIATELY - no delays!
        this.animateTitleLines();
        this.animateSubtitle();
        this.animateHeroStats();
    }

    animateTitleLines() {
        // Animate title lines with staggered timing - IMMEDIATELY!
        const titleLines = document.querySelectorAll('.title-line');
        console.log('Found', titleLines.length, 'title lines'); // Debug log
        
        if (titleLines.length === 0) {
            console.warn('No title lines found!');
            return;
        }
        
        titleLines.forEach((line, index) => {
            console.log(`Setting up title line ${index}:`, line.textContent);
            
            // Force initial state with !important
            line.style.setProperty('opacity', '0', 'important');
            line.style.setProperty('transform', 'translateY(50px)', 'important');
            line.style.setProperty('transition', 'opacity 1s ease-out, transform 1s ease-out', 'important');
            
            setTimeout(() => {
                line.style.setProperty('opacity', '1', 'important');
                line.style.setProperty('transform', 'translateY(0)', 'important');
                console.log('Animated title line', index); // Debug log
            }, index * 150); // Start IMMEDIATELY with fast stagger
        });
    }

    animateSubtitle() {
        const subtitle = document.querySelector('.hero-subtitle');
        if (subtitle) {
            console.log('Found subtitle, animating:', subtitle.textContent.substring(0, 50) + '...'); // Debug log
            
            // Force initial state
            subtitle.style.setProperty('opacity', '0', 'important');
            subtitle.style.setProperty('transform', 'translateY(30px)', 'important');
            subtitle.style.setProperty('transition', 'opacity 1s ease-out, transform 1s ease-out', 'important');
            
            setTimeout(() => {
                subtitle.style.setProperty('opacity', '1', 'important');
                subtitle.style.setProperty('transform', 'translateY(0)', 'important');
                console.log('Animated subtitle'); // Debug log
            }, 600); // Start quickly after title lines
        } else {
            console.warn('No subtitle found!');
        }
    }

    animateHeroStats() {
        const heroStats = document.querySelector('.hero-stats');
        if (heroStats) {
            console.log('Found hero stats, animating'); // Debug log
            
            // Force initial state
            heroStats.style.setProperty('opacity', '0', 'important');
            heroStats.style.setProperty('transform', 'translateY(30px)', 'important');
            heroStats.style.setProperty('transition', 'opacity 1s ease-out, transform 1s ease-out', 'important');
            
            setTimeout(() => {
                heroStats.style.setProperty('opacity', '1', 'important');
                heroStats.style.setProperty('transform', 'translateY(0)', 'important');
                console.log('Animated hero stats container'); // Debug log
                
                // Trigger counter animations after stats container animation starts
                setTimeout(() => {
                    console.log('Triggering counter animations from hero animation'); // Debug log
                    this.triggerCounterAnimations();
                }, 9200); // Stats appear at 800ms, counters at 10000ms total
            }, 800); // Start quickly after subtitle
        } else {
            console.warn('No hero stats found!');
        }
    }

    // Enhanced Mouse/Touch Parallax Effect for Floating Shapes
    setupMouseParallax() {
        const shapes = document.querySelectorAll('.shape');
        const isTouchDevice = 'ontouchstart' in window;
        const isMobile = window.innerWidth <= 768;
        const isTablet = window.innerWidth <= 1024 && window.innerWidth > 768;
        
        if (!isTouchDevice && !isMobile) {
            // Desktop mouse parallax - enhanced smoothness
            let mouseX = 0, mouseY = 0;
            let currentX = 0, currentY = 0;
            
            document.addEventListener('mousemove', (e) => {
                mouseX = e.clientX / window.innerWidth;
                mouseY = e.clientY / window.innerHeight;
            });
            
            // Smooth animation loop for desktop
            const animate = () => {
                currentX += (mouseX - currentX) * 0.1;
                currentY += (mouseY - currentY) * 0.1;
                
                shapes.forEach((shape, index) => {
                    const speed = (index + 1) * 0.5;
                    const x = (currentX - 0.5) * speed * 50;
                    const y = (currentY - 0.5) * speed * 50;
                    
                    shape.style.transform = `translate3d(${x}px, ${y}px, 0) rotate(${currentX * 360}deg)`;
                });
                
                requestAnimationFrame(animate);
            };
            animate();
        } else if (isTablet) {
            // Tablet touch parallax - more responsive
            this.setupTabletInteractions();
        } else {
            // Mobile - subtle effects only
            this.optimizeForMobile();
        }
    }

    // Tablet-specific touch interactions
    setupTabletInteractions() {
        const shapes = document.querySelectorAll('.shape');
        let touchStartX = 0, touchStartY = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }, { passive: true });
        
        document.addEventListener('touchmove', (e) => {
            if (e.touches.length === 1) {
                const touchX = e.touches[0].clientX;
                const touchY = e.touches[0].clientY;
                const deltaX = (touchX - touchStartX) / window.innerWidth;
                const deltaY = (touchY - touchStartY) / window.innerHeight;
                
                shapes.forEach((shape, index) => {
                    const multiplier = (index + 1) * 15;
                    const x = deltaX * multiplier;
                    const y = deltaY * multiplier;
                    
                    shape.style.transform = `translate3d(${x}px, ${y}px, 0) rotate(${deltaX * 180}deg)`;
                });
            }
        }, { passive: true });
        
        // Enhanced touch feedback for tablets
        const cards = document.querySelectorAll('.service-card');
        cards.forEach(card => {
            card.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
                // Haptic feedback if available
                if (navigator.vibrate) {
                    navigator.vibrate(10);
                }
            }, { passive: true });
            
            card.addEventListener('touchend', function() {
                this.style.transform = 'scale(1)';
            }, { passive: true });
        });
    }

    // Mobile optimizations
    optimizeForMobile() {
        // Reduce animations for better performance on mobile
        const shapes = document.querySelectorAll('.shape');
        shapes.forEach(shape => {
            shape.style.animation = 'float 6s ease-in-out infinite';
        });
        
        // Optimize touch interactions for mobile
        const cards = document.querySelectorAll('.service-card');
        cards.forEach(card => {
            card.addEventListener('touchstart', function() {
                this.classList.add('mobile-touch-active');
            }, { passive: true });
            
            card.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.classList.remove('mobile-touch-active');
                }, 150);
            }, { passive: true });
        });
    }

    // Intersection Observer for scroll animations
    setupIntersectionObserver() {
        const options = {
            threshold: 0.3,
            rootMargin: '0px 0px -100px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    
                    // Trigger counter animations for stat numbers
                    if (entry.target.classList.contains('stat-number')) {
                        console.log('Triggering counter for:', entry.target); // Debug log
                        if (!entry.target.hasAttribute('data-animated')) {
                            this.animateCounter(entry.target);
                        }
                    }
                    
                    // Also trigger for stat-item containers
                    if (entry.target.classList.contains('stat-item')) {
                        const statNumber = entry.target.querySelector('.stat-number');
                        if (statNumber && !statNumber.hasAttribute('data-animated')) {
                            console.log('Triggering counter for stat-item:', statNumber); // Debug log
                            this.animateCounter(statNumber);
                        }
                    }
                    
                    // Trigger animations for hero stats container
                    if (entry.target.classList.contains('hero-stats')) {
                        console.log('Hero stats container is visible, triggering counters'); // Debug log
                        setTimeout(() => {
                            this.triggerCounterAnimations();
                        }, 300);
                    }
                }
            });
        }, options);

        // Observe elements
        const elementsToObserve = document.querySelectorAll(
            '.service-card, .stat-item, .stat-number, .process-step, .testimonial-card, .hero-stats, .section-title'
        );
        
        console.log('Setting up intersection observer for', elementsToObserve.length, 'elements'); // Debug log
        
        elementsToObserve.forEach(element => {
            observer.observe(element);
        });
    }

    // Trigger counter animations manually
    triggerCounterAnimations() {
        const counters = document.querySelectorAll('.stat-number');
        console.log('triggerCounterAnimations found', counters.length, 'counters'); // Debug log
        
        counters.forEach((counter, index) => {
            if (!counter.hasAttribute('data-animated')) {
                console.log('Triggering counter animation for index', index, 'target:', counter.getAttribute('data-target')); // Debug log
                setTimeout(() => {
                    this.animateCounter(counter);
                }, index * 200);
            } else {
                console.log('Counter already animated:', counter); // Debug log
            }
        });
    }

    // Counter Animation
    animateCounter(element) {
        console.log('animateCounter called for element:', element);
        
        // Prevent duplicate animations
        if (element.hasAttribute('data-animated')) {
            console.log('Element already animated, skipping:', element);
            return;
        }
        
        // Mark as animated to prevent duplicate animations
        element.setAttribute('data-animated', 'true');

        // First try data-target attribute
        let target = NaN;
        const dataTarget = element.getAttribute('data-target');
        if (dataTarget !== null) {
            target = parseInt(dataTarget);
            console.log('Found data-target attribute:', dataTarget);
        }
        
        // If data-target is not present or invalid, try text content
        if (isNaN(target)) {
            const textContent = element.textContent.trim();
            console.log('Trying to parse from text content:', textContent);
            target = parseInt(textContent.replace(/[^0-9]/g, ''));
        }
        
        // Final check for valid target
        if (isNaN(target) || target === 0) {
            console.warn('Counter target value not found or invalid:', element);
            return;
        }

        console.log('Animating counter to:', target); // Debug log

        const duration = 2000;
        const start = performance.now();
        const startValue = 0;

        // Reset element text to show animation
        element.textContent = '0';
        
        // Make sure element is visible
        element.style.setProperty('opacity', '1', 'important');

        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function - smoother animation
            const easeOutQuart = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(startValue + (target - startValue) * easeOutQuart);
            
            element.textContent = current.toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = target.toLocaleString();
                console.log('Counter animation completed for target:', target);
            }
        };

        requestAnimationFrame(animate);
    }

    // Manual testing functions for debugging
    testAnimations() {
        console.log('=== MANUAL ANIMATION TEST ===');
        this.animateHeroElements();
    }

    testCounters() {
        console.log('=== MANUAL COUNTER TEST ===');
        this.triggerCounterAnimations();
    }

    resetAnimations() {
        console.log('=== RESETTING ANIMATIONS ===');
        const titleLines = document.querySelectorAll('.title-line');
        const subtitle = document.querySelector('.hero-subtitle');
        const heroStats = document.querySelector('.hero-stats');
        const counters = document.querySelectorAll('.stat-number');

        titleLines.forEach(line => {
            line.style.setProperty('opacity', '0', 'important');
            line.style.setProperty('transform', 'translateY(50px)', 'important');
        });

        if (subtitle) {
            subtitle.style.setProperty('opacity', '0', 'important');
            subtitle.style.setProperty('transform', 'translateY(30px)', 'important');
        }

        if (heroStats) {
            heroStats.style.setProperty('opacity', '0', 'important');
            heroStats.style.setProperty('transform', 'translateY(30px)', 'important');
        }

        counters.forEach(counter => {
            counter.removeAttribute('data-animated');
            counter.textContent = '0';
        });

        console.log('Animations reset. Call testAnimations() to restart.');
    }

    // Enhanced counter animations with stagger effect
    setupCounterAnimations() {
        console.log('Setting up counter animations...');
        const counters = document.querySelectorAll('.stat-number');
        console.log('Found counters:', counters.length);
        
        // Force trigger animations immediately
        counters.forEach((counter, index) => {
            console.log(`Setting up counter ${index}:`, counter);
            // Force trigger animation immediately
            setTimeout(() => {
                this.animateCounter(counter);
            }, 500 + (index * 300));
        });
        
        counters.forEach((counter, index) => {
            setTimeout(() => {
                counter.style.opacity = '1';
                counter.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    // Parallax Effects for sections
    setupParallaxEffects() {
        const parallaxElements = document.querySelectorAll('.parallax-bg, .shape');
        
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            
            parallaxElements.forEach((element, index) => {
                const speed = (index + 1) * 0.2;
                element.style.transform = `translate3d(0, ${rate * speed}px, 0)`;
            });
        });
    }

    // Service Cards Enhanced Interactions
    setupServiceCardInteractions() {
        const cards = document.querySelectorAll('.service-card');
        
        cards.forEach((card, index) => {
            // Magnetic effect for desktop
            if (window.innerWidth > 1024) {
                card.addEventListener('mousemove', (e) => {
                    const rect = card.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    
                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;
                    
                    const rotateX = (y - centerY) / 10;
                    const rotateY = (centerX - x) / 10;
                    
                    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`;
                });
                
                card.addEventListener('mouseleave', () => {
                    card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
                });
            }
            
            // Enhanced click/tap interaction
            card.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Add ripple effect
                const ripple = document.createElement('div');
                ripple.classList.add('ripple-effect');
                
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                
                card.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.remove();
                }, 600);
                
                // Open modal
                const serviceId = card.getAttribute('data-service');
                if (serviceId) {
                    this.openServiceModal(serviceId);
                }
            });
        });
    }

    // Modal System
    setupModalSystem() {
        // Service data matching the HTML button calls
        this.serviceData = {
            complete: {
                title: "🏡 Ristrutturazioni Complete Chiavi in Mano",
                description: "Realizziamo la casa dei tuoi sogni, partendo dalla progettazione fino alla consegna finale. Ogni fase del lavoro è seguita con attenzione ai dettagli, professionalità e materiali di alta qualità.",
                features: [
                    "Progettazione tecnica e consulenza completa",
                    "Studio degli spazi e pratiche edilizie",
                    "Demolizioni e ricostruzioni strutturali",
                    "Nuovi impianti elettrici a norma",
                    "Impianti idraulici moderni ed efficienti",
                    "Finiture di pregio con materiali selezionati",
                    "Direzione lavori professionale",
                    "Consegna chiavi in mano"
                ],
                gallery: [
                    "/static/images/complete1.jpg",
                    "/static/images/complete2.jpg", 
                    "/static/images/complete3.jpg"
                ]
            },
            bathroom: {
                title: "🚿 Rifacimento Bagni",
                description: "Trasformiamo il tuo bagno in un ambiente moderno, funzionale e raffinato. Offriamo soluzioni su misura per ogni esigenza, con finiture di alta gamma.",
                features: [
                    "Box doccia su misura in vetro temperato, cristallo o walk-in",
                    "Rivestimenti ceramici dal classico al moderno",
                    "Grandi formati fino a 120x320 cm",
                    "Sanitari di design sospesi e salvaspazio",
                    "Tecnologie per il risparmio idrico",
                    "Illuminazione LED integrata in specchi e controsoffitti",
                    "Mobili su misura",
                    "Impianto di riscaldamento a pavimento"
                ],
                gallery: [
                    "/static/images/bathroom1.jpg",
                    "/static/images/bathroom2.jpg",
                    "/static/images/bathroom3.jpg"
                ]
            },
            systems: {
                title: "⚙️ Impianti Tecnologici",
                description: "Offriamo soluzioni impiantistiche moderne e innovative per garantire il massimo comfort abitativo, l'efficienza energetica e la gestione intelligente della casa. Ogni impianto è progettato su misura.",
                features: [
                    "Climatizzazione estiva e invernale: split, multisplit, pompe di calore",
                    "Alta efficienza e risparmio energetico garantiti",
                    "Domotica e automazione per luci, tapparelle, sicurezza",
                    "Climatizzazione e irrigazione automatica",
                    "Controllo remoto via smartphone o tablet",
                    "Sistemi smart home con dispositivi connessi",
                    "Assistenti vocali e sensori intelligenti",
                    "Interfacce user-friendly"
                ],
                gallery: [
                    "/static/images/systems1.jpg",
                    "/static/images/systems2.jpg",
                    "/static/images/systems3.jpg"
                ]
            },
            structural: {
                title: "🔨 Opere Murarie e Strutturali",
                description: "Interventi strutturali e opere murarie eseguiti da tecnici specializzati con demolizioni, ricostruzioni e consolidamenti.",
                features: [
                    "Demolizione di pareti, infissi, porte e solai con smaltimento",
                    "Realizzazione di nuove murature e pareti divisorie",
                    "Opere in cemento armato: cerchiature e consolidamenti",
                    "Installazione di soglie e controtelai",
                    "Rifacimento intonaci interni",
                    "Assistenza muraria per impianti elettrici e idraulici"
                ],
                gallery: [
                    "/static/images/structural1.jpg",
                    "/static/images/structural2.jpg",
                    "/static/images/structural3.jpg"
                ]
            },
            insulation: {
                title: "🛡️ Isolamenti e Impermeabilizzazioni",
                description: "Soluzioni avanzate per l'isolamento termico e acustico, oltre a impermeabilizzazioni per proteggere la tua casa.",
                features: [
                    "Isolamento termico con pannelli in polistirene",
                    "Isolamento acustico con lana di roccia",
                    "Impermeabilizzazioni per bagni e piatti doccia",
                    "Murature contro terra protette",
                    "Realizzazione di barriere e freni al vapore",
                    "Materiali certificati e duraturi"
                ],
                gallery: [
                    "/static/images/insulation1.jpg",
                    "/static/images/insulation2.jpg",
                    "/static/images/insulation3.jpg"
                ]
            },
            flooring: {
                title: "🏢 Pavimenti e Rivestimenti",
                description: "Installazione professionale di pavimenti e rivestimenti con materiali di qualità e tecniche moderne.",
                features: [
                    "Rimozione di pavimenti e sottofondi esistenti",
                    "Sottofondi alleggeriti in calcestruzzo cellulare",
                    "Massetti armati o fibrati",
                    "Posa di parquet, laminati, ceramica",
                    "Dal mosaico alle grandi lastre 120x320 cm",
                    "Installazione di gradini, scale e battiscopa"
                ],
                gallery: [
                    "/static/images/flooring1.jpg",
                    "/static/images/flooring2.jpg",
                    "/static/images/flooring3.jpg"
                ]
            },
            drywall: {
                title: "📦 Cartongesso",
                description: "Realizzazione di strutture in cartongesso per dividere spazi, creare controsoffitti e arredi su misura.",
                features: [
                    "Pareti, contropareti e controsoffitti",
                    "Lastra singola o doppia",
                    "Volte, velette e compartimentazioni antincendio",
                    "Arredi su misura: mensole, librerie, mobili",
                    "Isolamento acustico integrato",
                    "Finiture personalizzate"
                ],
                gallery: [
                    "/static/images/drywall1.jpg",
                    "/static/images/drywall2.jpg",
                    "/static/images/drywall3.jpg"
                ]
            },
            painting: {
                title: "🎨 Tinteggiature e Verniciature",
                description: "Tinteggiature professionali con materiali eco-sostenibili per dare nuova vita ai tuoi ambienti.",
                features: [
                    "Sverniciatura e raschiatura di vecchie pitture",
                    "Rasature lisce o effetto intonaco armate",
                    "Trattamenti antimuffa e fungicidi",
                    "Pitture all'acqua: tempera, traspirante, lavabile",
                    "Pitture minerali: calce, silicato e termiche",
                    "Finiture decorative: stucco veneziano, marmorino",
                    "Verniciatura su legno e ferro",
                    "Colori personalizzati"
                ],
                gallery: [
                    "/static/images/painting1.jpg",
                    "/static/images/painting2.jpg",
                    "/static/images/painting3.jpg"
                ]
            },
            doors: {
                title: "🚪 Porte e Finestre",
                description: "Installazione di porte interne e infissi di qualità in diversi materiali e stili.",
                features: [
                    "Installazione di porte interne",
                    "Infissi in legno, PVC o alluminio",
                    "Montaggio di portoni blindati",
                    "Serramenti su misura",
                    "Vetrate e finestre panoramiche",
                    "Sistemi di sicurezza integrati"
                ],
                gallery: [
                    "/static/images/doors1.jpg",
                    "/static/images/doors2.jpg",
                    "/static/images/doors3.jpg"
                ]
            },
            scaffolding: {
                title: "🏗️ Ponteggi",
                description: "Noleggio e installazione di ponteggi per lavori in quota con la massima sicurezza.",
                features: [
                    "Ponteggi fissi prefabbricati",
                    "Ponteggi autosollevanti",
                    "Piattaforme aeree per lavori in quota",
                    "Installazione professionale",
                    "Manutenzione e assistenza",
                    "Certificazioni di sicurezza"
                ],
                gallery: [
                    "/static/images/scaffolding1.jpg",
                    "/static/images/scaffolding2.jpg",
                    "/static/images/scaffolding3.jpg"
                ]
            },
            "external-masonry": {
                title: "🏢 Murature Esterne",
                description: "Interventi su murature esterne con demolizioni, ripristini e nuove costruzioni.",
                features: [
                    "Demolizione di tetti, balconi, intonaci e pavimentazioni",
                    "Smaltimento completo delle macerie",
                    "Ripristino intonaci con malte fibrate",
                    "Recupero strutture in cemento armato con malte R3 e R4",
                    "Scavi, rinterri e nuove fondazioni",
                    "Costruzione di parapetti, balconi, rampe e solai"
                ],
                gallery: [
                    "/static/images/external-masonry1.jpg",
                    "/static/images/external-masonry2.jpg",
                    "/static/images/external-masonry3.jpg"
                ]
            },
            "external-insulation": {
                title: "🛡️ Isolamenti e Impermeabilizzazioni Esterne",
                description: "Sistemi di isolamento termico e impermeabilizzazione per l'esterno dell'edificio.",
                features: [
                    "Cappotti termici con EPS, lana di roccia, sughero",
                    "Isolamento con fibra di legno",
                    "Impermeabilizzazioni con guaine bituminose e cementizie",
                    "Resine liquide e membrane in polietilene",
                    "Barriere contro umidità per murature interrate",
                    "Coibentazioni coperture con materiali certificati"
                ],
                gallery: [
                    "/static/images/external-insulation1.jpg",
                    "/static/images/external-insulation2.jpg",
                    "/static/images/external-insulation3.jpg"
                ]
            },
            "external-flooring": {
                title: "🛤️ Pavimentazioni Esterne e Coprimuro",
                description: "Realizzazione di pavimentazioni esterne durevoli e esteticamente gradevoli.",
                features: [
                    "Demolizione e rifacimento di pavimenti esterni",
                    "Solette armate, marciapiedi, massetti",
                    "Posa di ceramiche, porfido, autobloccanti",
                    "Pavimenti flottanti per esterni",
                    "Coprimuri in marmo o marmoresina",
                    "Scale, gradini e battiscopa esterni"
                ],
                gallery: [
                    "/static/images/external-flooring1.jpg",
                    "/static/images/external-flooring2.jpg",
                    "/static/images/external-flooring3.jpg"
                ]
            },
            roofing: {
                title: "🏠 Coperture e Tetti",
                description: "Costruzione e ristrutturazione di tetti con materiali moderni e sistemi di sicurezza.",
                features: [
                    "Coperture con tegole in laterizio o cemento",
                    "Pannelli sandwich in lamiera coibentata",
                    "Montaggio di lucernai e finestre da tetto",
                    "Costruzione di camini",
                    "Progettazione e installazione di linea vita",
                    "Sistemi di raccolta acque piovane"
                ],
                gallery: [
                    "/static/images/roofing1.jpg",
                    "/static/images/roofing2.jpg",
                    "/static/images/roofing3.jpg"
                ]
            },
            "external-painting": {
                title: "🎨 Tinteggiature Esterne",
                description: "Tinteggiature e verniciature esterne per proteggere e abbellire la facciata dell'edificio.",
                features: [
                    "Sverniciatura e lavaggi ad alta pressione",
                    "Rasature effetto intonaco armate",
                    "Trattamenti antimuffa e fungicidi specifici",
                    "Pitture esterne acriliche, silossaniche, minerali",
                    "Pitture termiche per efficienza energetica",
                    "Verniciature su ferro: ringhiere, infissi, tubazioni"
                ],
                gallery: [
                    "/static/images/external-painting1.jpg",
                    "/static/images/external-painting2.jpg",
                    "/static/images/external-painting3.jpg"
                ]
            },
            fibrocemento: {
                title: "🏗️ Fibrocemento e Polistirene",
                description: "Elementi architettonici decorativi e funzionali in fibrocemento e polistirene per migliorare l'estetica dell'edificio.",
                features: [
                    "Cornici, modanature e marcapiani in polistirene EPS",
                    "Elementi architettonici in fibrocemento",
                    "Cassonetti, parapetti, controsoffitti",
                    "Installazione professionale",
                    "Materiali resistenti alle intemperie",
                    "Finiture personalizzabili"
                ],
                gallery: [
                    "/static/images/fibrocemento1.jpg",
                    "/static/images/fibrocemento2.jpg",
                    "/static/images/fibrocemento3.jpg"
                ]
            }
        };
        
        // Create modal if it doesn't exist
        if (!document.getElementById('serviceModal')) {
            this.createModal();
        }
        
        // Setup modal controls
        this.setupModalControls();
    }

    createModal() {
        const modalHTML = `
            <div id="serviceModal" class="modal-overlay">
                <div class="modal-container">
                    <button class="modal-close">&times;</button>
                    <div class="modal-header">
                        <h2 id="modalTitle"></h2>
                    </div>
                    <div class="modal-body">
                        <div class="modal-gallery">
                            <div class="gallery-main">
                                <img id="modalMainImage" src="" alt="" />
                            </div>
                            <div class="gallery-thumbnails">
                                <!-- Thumbnails will be populated dynamically -->
                            </div>
                        </div>
                        <div class="modal-content">
                            <p id="modalDescription"></p>
                            <div class="modal-features">
                                <h3>Caratteristiche:</h3>
                                <ul id="modalFeatures"></ul>
                            </div>
                            <div class="modal-actions">
                                <button class="btn btn-primary" onclick="openContactForm()">
                                    Richiedi Preventivo
                                </button>
                                <button class="btn btn-secondary" onclick="openGallery()">
                                    Vedi Galleria
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    setupModalControls() {
        const modal = document.getElementById('serviceModal');
        const closeBtn = document.querySelector('.modal-close');
        
        // Close modal events
        closeBtn.addEventListener('click', () => this.closeModal());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeModal();
        });
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                this.closeModal();
            }
        });
    }

    openServiceModal(serviceId) {
        const service = this.serviceData[serviceId];
        if (!service) return;
        
        const modal = document.getElementById('serviceModal');
        
        // Populate modal content
        document.getElementById('modalTitle').textContent = service.title;
        document.getElementById('modalDescription').textContent = service.description;
        
        // Set main image
        const mainImage = document.getElementById('modalMainImage');
        mainImage.src = service.gallery[0];
        mainImage.alt = service.title;
        
        // Populate features
        const featuresList = document.getElementById('modalFeatures');
        featuresList.innerHTML = '';
        service.features.forEach(feature => {
            const li = document.createElement('li');
            li.textContent = feature;
            featuresList.appendChild(li);
        });
        
        // Create thumbnails
        const thumbnailsContainer = document.querySelector('.gallery-thumbnails');
        thumbnailsContainer.innerHTML = '';
        service.gallery.forEach((image, index) => {
            const thumb = document.createElement('img');
            thumb.src = image;
            thumb.alt = `${service.title} ${index + 1}`;
            thumb.classList.add('thumbnail');
            if (index === 0) thumb.classList.add('active');
            
            thumb.addEventListener('click', () => {
                mainImage.src = image;
                document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
                thumb.classList.add('active');
            });
            
            thumbnailsContainer.appendChild(thumb);
        });
        
        // Show modal with animation
        modal.style.display = 'block';
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Animate modal entrance (use .modal-content instead of .modal-container)
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            setTimeout(() => {
                modalContent.style.transform = 'scale(1)';
                modalContent.style.opacity = '1';
            }, 10);
        }
        
        console.log('✅ Modal opened successfully:', service.title);
    }

    closeModal() {
        const modal = document.getElementById('serviceModal');
        if (!modal) return;
        
        const container = modal.querySelector('.modal-content');
        
        // Animate modal exit
        if (container) {
            container.style.transform = 'scale(0.9)';
            container.style.opacity = '0';
        }
        
        setTimeout(() => {
            modal.style.display = 'none';
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }, 300);
    }

    // Advanced Interactions
    setupAdvancedInteractions() {
        this.setupScrollIndicator();
        this.setupParticleSystem();
        this.setupMagneticButtons();
        this.setupHoverEffects();
    }

    setupScrollIndicator() {
        const scrollIndicator = document.createElement('div');
        scrollIndicator.className = 'scroll-indicator';
        scrollIndicator.innerHTML = `
            <div class="scroll-line"></div>
            <div class="scroll-thumb"></div>
        `;
        document.body.appendChild(scrollIndicator);
        
        window.addEventListener('scroll', () => {
            const scrollPercent = (window.pageYOffset / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
            scrollIndicator.querySelector('.scroll-thumb').style.top = scrollPercent + '%';
        });
    }

    setupParticleSystem() {
        if (window.innerWidth <= 768) return; // Skip on mobile for performance
        
        const canvas = document.createElement('canvas');
        canvas.className = 'particle-canvas';
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '1';
        canvas.style.opacity = '0.1';
        
        document.body.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const particles = [];
        const particleCount = 50;
        
        // Create particles
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1
            });
        }
        
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            particles.forEach(particle => {
                particle.x += particle.vx;
                particle.y += particle.vy;
                
                // Wrap around edges
                if (particle.x < 0) particle.x = canvas.width;
                if (particle.x > canvas.width) particle.x = 0;
                if (particle.y < 0) particle.y = canvas.height;
                if (particle.y > canvas.height) particle.y = 0;
                
                // Draw particle
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                ctx.fillStyle = '#007bff';
                ctx.fill();
            });
            
            requestAnimationFrame(animate);
        }
        
        animate();
        
        // Resize handler
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
    }

    setupMagneticButtons() {
        if (window.innerWidth <= 1024) return; // Desktop only
        
        const magneticElements = document.querySelectorAll('.btn, .service-card, .magnetic');
        
        magneticElements.forEach(element => {
            element.addEventListener('mousemove', (e) => {
                const rect = element.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                
                element.style.transform = `translate3d(${x * 0.1}px, ${y * 0.1}px, 0) scale(1.02)`;
            });
            
            element.addEventListener('mouseleave', () => {
                element.style.transform = 'translate3d(0, 0, 0) scale(1)';
            });
        });
    }

    setupHoverEffects() {
        const cards = document.querySelectorAll('.service-card');
        
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.boxShadow = '0 20px 60px rgba(0, 123, 255, 0.3)';
                card.style.borderColor = '#007bff';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.boxShadow = '';
                card.style.borderColor = '';
            });
        });
    }

    // Responsive Features
    setupResponsiveFeatures() {
        // Device detection
        const isMobile = window.innerWidth <= 768;
        const isTablet = window.innerWidth <= 1024 && window.innerWidth > 768;
        const isDesktop = window.innerWidth > 1024;
        
        if (isMobile) {
            this.enableMobileOptimizations();
        } else if (isTablet) {
            this.enableTabletOptimizations();
        } else {
            this.enableDesktopOptimizations();
        }
        
        // Orientation change handler
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });
        
        // Resize handler with debounce
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });
    }

    enableMobileOptimizations() {
        // Reduce animations
        document.body.classList.add('mobile-optimized');
        
        // Touch-friendly interactions
        const cards = document.querySelectorAll('.service-card');
        cards.forEach(card => {
            card.addEventListener('touchstart', () => {
                card.classList.add('touch-active');
            }, { passive: true });
            
            card.addEventListener('touchend', () => {
                setTimeout(() => {
                    card.classList.remove('touch-active');
                }, 150);
            }, { passive: true });
        });
        
        // Simplified parallax
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const shapes = document.querySelectorAll('.shape');
            shapes.forEach((shape, index) => {
                const speed = 0.1 * (index + 1);
                shape.style.transform = `translateY(${scrolled * speed}px)`;
            });
        }, { passive: true });
    }

    enableTabletOptimizations() {
        document.body.classList.add('tablet-optimized');
        
        // Enhanced touch interactions
        this.setupTabletInteractions();
        
        // Medium complexity animations
        const cards = document.querySelectorAll('.service-card');
        cards.forEach(card => {
            card.addEventListener('touchstart', () => {
                card.style.transform = 'scale(0.98)';
                if (navigator.vibrate) {
                    navigator.vibrate([10]);
                }
            }, { passive: true });
            
            card.addEventListener('touchend', () => {
                card.style.transform = 'scale(1)';
            }, { passive: true });
        });
    }

    enableDesktopOptimizations() {
        document.body.classList.add('desktop-optimized');
        
        // Full feature set
        this.setupAdvancedInteractions();
        this.setupMagneticButtons();
        
        // Advanced hover effects
        const cards = document.querySelectorAll('.service-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-10px) scale(1.02)';
                card.style.boxShadow = '0 25px 50px rgba(0, 123, 255, 0.25)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
                card.style.boxShadow = '';
            });
        });
    }

    handleOrientationChange() {
        // Recalculate dimensions
        setTimeout(() => {
            const canvas = document.querySelector('.particle-canvas');
            if (canvas) {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }
            
            // Re-setup interactions based on new dimensions
            this.setupResponsiveFeatures();
        }, 500);
    }

    handleResize() {
        // Update responsive features
        const isMobile = window.innerWidth <= 768;
        const isTablet = window.innerWidth <= 1024 && window.innerWidth > 768;
        
        // Remove all optimization classes
        document.body.classList.remove('mobile-optimized', 'tablet-optimized', 'desktop-optimized');
        
        // Re-apply appropriate optimizations
        if (isMobile) {
            this.enableMobileOptimizations();
        } else if (isTablet) {
            this.enableTabletOptimizations();
        } else {
            this.enableDesktopOptimizations();
        }
    }
}

// Global function for modal opening (called from HTML buttons)
window.openServiceModal = function(serviceId) {
    console.log('Global openServiceModal called with serviceId:', serviceId);
    if (window.servicesController && window.servicesController.openServiceModal) {
        window.servicesController.openServiceModal(serviceId);
    } else {
        console.error('ServicesController not available or openServiceModal method not found');
        console.log('Available controller:', window.servicesController);
    }
};

// Global function to close service modal
window.closeServiceModal = function() {
    console.log('🔘 Closing service modal');
    const modal = document.getElementById('serviceModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
        
        // Remove any body scroll lock if present
        document.body.style.overflow = '';
    } else {
        console.warn('Service modal not found');
    }
};

// Global functions for testing counters (called from HTML buttons)
window.testCounters = function() {
    console.log('Global testCounters called');
    if (window.servicesController && window.servicesController.triggerCounterAnimations) {
        // Reset counters first
        const statNumbers = document.querySelectorAll('.stat-number[data-target]');
        statNumbers.forEach(element => {
            element.textContent = '0';
        });
        
        // Trigger animation
        setTimeout(() => {
            window.servicesController.triggerCounterAnimations();
        }, 100);
    } else {
        console.error('ServicesController not available');
        // Fallback - direct animation
        directCounterFallback();
    }
};

window.resetCounters = function() {
    console.log('Global resetCounters called');
    const statNumbers = document.querySelectorAll('.stat-number[data-target]');
    statNumbers.forEach(element => {
        element.textContent = '0';
    });
};

// Fallback counter animation function
function directCounterFallback() {
    console.log('🔄 Using fallback counter animation');
    const statNumbers = document.querySelectorAll('.stat-number[data-target]');
    
    statNumbers.forEach((element, index) => {
        const target = parseInt(element.getAttribute('data-target'));
        if (!target) return;
        
        let start = null;
        const duration = 2000;
        
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = Math.min((timestamp - start) / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(target * easeProgress);
            
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }
        
        setTimeout(() => {
            requestAnimationFrame(animate);
        }, index * 200);
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing ServicesController');
    try {
        const controller = new ServicesController();
        console.log('ServicesController initialized successfully:', controller);
        window.servicesController = controller; // Store reference for debugging
        
        // Force counter animations to start after proper delay
        setTimeout(() => {
            console.log('Force triggering counter animations...');
            controller.triggerCounterAnimations();
        }, 10000); // Ritardo di 10 secondi
        
    } catch (error) {
        console.error('Error initializing ServicesController:', error);
    }
});

// Also try immediate initialization if DOM is already loaded
if (document.readyState === 'loading') {
    console.log('Document still loading, waiting for DOMContentLoaded');
} else {
    console.log('Document already loaded, initializing immediately');
    setTimeout(() => {
        try {
            const controller = new ServicesController();
            console.log('ServicesController initialized immediately:', controller);
            window.servicesController = controller;
        } catch (error) {
            console.error('Error in immediate initialization:', error);
        }
    }, 100);
}

// Export for global access
window.ServicesController = ServicesController;

// Global testing functions for browser console
window.testServicesAnimations = function() {
    console.log('=== TESTING SERVICES ANIMATIONS FROM CONSOLE ===');
    if (window.servicesController) {
        window.servicesController.testAnimations();
    } else {
        console.log('Creating new ServicesController for testing...');
        const controller = new ServicesController();
        window.servicesController = controller;
        setTimeout(() => {
            controller.testAnimations();
        }, 100);
    }
};

// testCounters function moved earlier in the file

window.resetAnimations = function() {
    console.log('=== RESETTING ANIMATIONS FROM CONSOLE ===');
    if (window.servicesController) {
        window.servicesController.resetAnimations();
    } else {
        console.log('No ServicesController found');
    }
};

// Debug info function
window.debugServices = function() {
    console.log('=== SERVICES DEBUG INFO ===');
    console.log('ServicesController available:', typeof window.ServicesController);
    console.log('Controller instance:', window.servicesController);
    console.log('Document ready state:', document.readyState);
    
    // Check elements
    const titleLines = document.querySelectorAll('.title-line');
    const subtitle = document.querySelector('.hero-subtitle');
    const heroStats = document.querySelector('.hero-stats');
    const statNumbers = document.querySelectorAll('.stat-number');
    
    console.log('Title lines found:', titleLines.length);
    console.log('Subtitle found:', subtitle ? 'YES' : 'NO');
    console.log('Hero stats found:', heroStats ? 'YES' : 'NO');
    console.log('Stat numbers found:', statNumbers.length);
    
    if (titleLines.length > 0) {
        titleLines.forEach((line, index) => {
            const styles = window.getComputedStyle(line);
            console.log(`Title line ${index} (${line.textContent}): opacity=${styles.opacity}, transform=${styles.transform}`);
        });
    }
    
    console.log('Available test functions: testServicesAnimations(), testCounters(), resetAnimations()');
};
