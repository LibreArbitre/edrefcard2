/**
 * EDRefCard Lightbox
 * 
 * Simple lightbox implementation for viewing reference cards in full size.
 */

document.addEventListener('DOMContentLoaded', () => {
    // create lightbox elements
    const lightbox = document.createElement('div');
    lightbox.id = 'lightbox';
    lightbox.className = 'lightbox hidden';

    const lightboxImg = document.createElement('img');
    lightboxImg.className = 'lightbox-content';

    const closeBtn = document.createElement('span');
    closeBtn.className = 'lightbox-close';
    closeBtn.innerHTML = '&times;';

    lightbox.appendChild(lightboxImg);
    lightbox.appendChild(closeBtn);
    document.body.appendChild(lightbox);

    // Function to open lightbox
    const openLightbox = (src, alt) => {
        lightboxImg.src = src;
        lightboxImg.alt = alt || 'Reference Card';
        lightbox.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    };

    // Function to close lightbox
    const closeLightbox = () => {
        lightbox.classList.add('hidden');
        document.body.style.overflow = ''; // Restore scrolling
        setTimeout(() => {
            lightboxImg.src = ''; // Clear source after transition
        }, 300);
    };

    // Add click listeners to all triggers
    const triggers = document.querySelectorAll('.lightbox-trigger');
    triggers.forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            openLightbox(trigger.src, trigger.alt);
        });
    });

    // Close events
    closeBtn.addEventListener('click', closeLightbox);

    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            closeLightbox();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !lightbox.classList.contains('hidden')) {
            closeLightbox();
        }
    });
});
