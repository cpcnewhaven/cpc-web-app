// Background image fetching and management
document.addEventListener('DOMContentLoaded', function() {
    const splashImageSection = document.getElementById('home-image');
    const midImageSection = document.getElementById('mid-image');
    
    // Real church images from gallery
    const defaultImages = [
        'https://storage.googleapis.com/cpc-public-website/media-gallery/womans-fall-brunch-2024/605c1ade-b21e-4713-ad4e-d9bb2d6709ad.JPG',
        'https://storage.googleapis.com/cpc-public-website/media-gallery/womans-fall-brunch-2024/89c3ea3b-e196-4318-bee8-08b5e66e728d.JPG',
        'https://storage.googleapis.com/cpc-public-website/media-gallery/womans-fall-brunch-2024/IMG_3661.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Hill%20Christmas%20Store%202023/IMG_0244.JPG',
        'https://storage.googleapis.com/cpc-public-website/events/Hill%20Christmas%20Store%202023/IMG_0251.JPG',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/2.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/3.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/4.jpg'
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
