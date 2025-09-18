// Background image fetching and management
document.addEventListener('DOMContentLoaded', function() {
    const splashImageSection = document.getElementById('home-image');
    const midImageSection = document.getElementById('mid-image');
    
    // Default placeholder images
    const defaultImages = [
        'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1920&h=1080&fit=crop',
        'https://images.unsplash.com/photo-1515378791036-0648a814c963?w=1920&h=1080&fit=crop',
        'https://images.unsplash.com/photo-1511895426328-dc8714191300?w=1920&h=1080&fit=crop',
        'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&h=1080&fit=crop',
        'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1920&h=1080&fit=crop'
    ];
    
    function getRandomImage() {
        return defaultImages[Math.floor(Math.random() * defaultImages.length)];
    }
    
    function setBackgroundImage(element, imageUrl) {
        if (element) {
            element.style.backgroundImage = `linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url(${imageUrl})`;
            element.style.backgroundSize = 'cover';
            element.style.backgroundPosition = 'center';
            element.style.backgroundAttachment = 'fixed';
        }
    }
    
    // Set initial background images
    if (splashImageSection) {
        setBackgroundImage(splashImageSection, getRandomImage());
    }
    
    if (midImageSection) {
        setBackgroundImage(midImageSection, getRandomImage());
    }
    
    // Optional: Change images periodically
    setInterval(function() {
        if (splashImageSection) {
            setBackgroundImage(splashImageSection, getRandomImage());
        }
    }, 30000); // Change every 30 seconds
    
    // Preload images for better performance
    function preloadImages() {
        defaultImages.forEach(imageUrl => {
            const img = new Image();
            img.src = imageUrl;
        });
    }
    
    preloadImages();
});
