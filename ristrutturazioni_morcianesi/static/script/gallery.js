/*---------------------------------------
  GALLERY JAVASCRIPT FUNCTIONALITY
----------------------------------------*/

document.addEventListener('DOMContentLoaded', function() {
    // Gallery filtering functionality
    const filterButtons = document.querySelectorAll('.filter-btn');
    const galleryItems = document.querySelectorAll('.gallery-item');

    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter gallery items
            galleryItems.forEach(item => {
                const category = item.getAttribute('data-category');
                
                if (filter === 'all' || category === filter) {
                    item.style.display = 'block';
                    // Add animation
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateY(0)';
                    }, 100);
                } else {
                    item.style.opacity = '0';
                    item.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        item.style.display = 'none';
                    }, 300);
                }
            });
        });
    });

    // Initialize gallery items with animation
    galleryItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, 100 * index);
    });

    // Lightbox functionality
    galleryItems.forEach(item => {
        item.addEventListener('click', function() {
            const img = this.querySelector('img');
            const overlay = this.querySelector('.gallery-overlay');
            
            if (img && overlay) {
                const title = overlay.querySelector('h3').textContent;
                const description = overlay.querySelector('p').textContent;
                openLightbox(img.src, title, description);
            }
        });
    });
    
    // Create lightbox
    function createLightbox() {
        const lightbox = document.createElement('div');
        lightbox.className = 'lightbox';
        lightbox.innerHTML = `
            <div class="lightbox-content">
                <button class="lightbox-close">&times;</button>
                <img class="lightbox-image" src="" alt="">
                <div class="lightbox-info">
                    <h3 class="lightbox-title"></h3>
                    <p class="lightbox-description"></p>
                </div>
                <button class="lightbox-prev">❮</button>
                <button class="lightbox-next">❯</button>
            </div>
        `;
        document.body.appendChild(lightbox);
        return lightbox;
    }
    
    // Get or create lightbox
    function getLightbox() {
        let lightbox = document.querySelector('.lightbox');
        if (!lightbox) {
            lightbox = createLightbox();
            
            // Add event listeners
            const closeBtn = lightbox.querySelector('.lightbox-close');
            const prevBtn = lightbox.querySelector('.lightbox-prev');
            const nextBtn = lightbox.querySelector('.lightbox-next');
            
            closeBtn.addEventListener('click', closeLightbox);
            lightbox.addEventListener('click', function(e) {
                if (e.target === lightbox) {
                    closeLightbox();
                }
            });
            
            prevBtn.addEventListener('click', showPrevImage);
            nextBtn.addEventListener('click', showNextImage);
            
            // Keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (lightbox.classList.contains('active')) {
                    if (e.key === 'Escape') {
                        closeLightbox();
                    } else if (e.key === 'ArrowLeft') {
                        showPrevImage();
                    } else if (e.key === 'ArrowRight') {
                        showNextImage();
                    }
                }
            });
        }
        return lightbox;
    }
    
    let currentImageIndex = 0;
    let visibleImages = [];
    
    function openLightbox(imageSrc, title, description) {
        const lightbox = getLightbox();
        const lightboxImage = lightbox.querySelector('.lightbox-image');
        const lightboxTitle = lightbox.querySelector('.lightbox-title');
        const lightboxDescription = lightbox.querySelector('.lightbox-description');
        
        // Get all visible images for navigation
        visibleImages = Array.from(document.querySelectorAll('.gallery-item'))
            .filter(item => item.style.display !== 'none')
            .map(item => ({
                src: item.querySelector('img').src,
                title: item.querySelector('.gallery-overlay h3').textContent,
                description: item.querySelector('.gallery-overlay p').textContent
            }));
        
        // Find current image index
        currentImageIndex = visibleImages.findIndex(img => img.src === imageSrc);
        
        lightboxImage.src = imageSrc;
        lightboxTitle.textContent = title;
        lightboxDescription.textContent = description;
        
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    function closeLightbox() {
        const lightbox = document.querySelector('.lightbox');
        if (lightbox) {
            lightbox.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    function showPrevImage() {
        if (visibleImages.length > 1) {
            currentImageIndex = (currentImageIndex - 1 + visibleImages.length) % visibleImages.length;
            updateLightboxImage();
        }
    }
    
    function showNextImage() {
        if (visibleImages.length > 1) {
            currentImageIndex = (currentImageIndex + 1) % visibleImages.length;
            updateLightboxImage();
        }
    }
    
    function updateLightboxImage() {
        const lightbox = document.querySelector('.lightbox');
        const currentImage = visibleImages[currentImageIndex];
        
        const lightboxImage = lightbox.querySelector('.lightbox-image');
        const lightboxTitle = lightbox.querySelector('.lightbox-title');
        const lightboxDescription = lightbox.querySelector('.lightbox-description');
        
        lightboxImage.src = currentImage.src;
        lightboxTitle.textContent = currentImage.title;
        lightboxDescription.textContent = currentImage.description;
    }
});
