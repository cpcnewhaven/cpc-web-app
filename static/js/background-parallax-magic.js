// Background parallax and image effects
document.addEventListener('DOMContentLoaded', function() {
    // Parallax scrolling effect
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.splash-image, .mid-image');
        
        parallaxElements.forEach(element => {
            const speed = 0.5; // Adjust speed as needed
            element.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading animation
    const loadingElements = document.querySelectorAll('.loading');
    loadingElements.forEach(element => {
        element.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; padding: 2rem;">
                <div style="
                    width: 40px;
                    height: 40px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <span style="margin-left: 1rem;">Loading...</span>
            </div>
        `;
    });
    
    // Add CSS for loading animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
});
