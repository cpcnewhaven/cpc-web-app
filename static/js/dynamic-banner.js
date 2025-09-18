// Dynamic banner functionality
document.addEventListener('DOMContentLoaded', function() {
    const warningBanner = document.getElementById('warningBanner');
    
    // Example banner content - you can modify this
    const bannerContent = {
        message: "Welcome to our new website! We're excited to share our updated online presence with you.",
        type: "info", // info, warning, success, error
        show: false // Set to true to show the banner
    };
    
    if (warningBanner && bannerContent.show) {
        warningBanner.textContent = bannerContent.message;
        warningBanner.className = `warning-banner ${bannerContent.type}`;
        warningBanner.style.display = 'block';
        
        // Add close button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.style.cssText = `
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: inherit;
        `;
        
        closeButton.addEventListener('click', function() {
            warningBanner.style.display = 'none';
        });
        
        warningBanner.style.position = 'relative';
        warningBanner.style.padding = '10px 40px 10px 20px';
        warningBanner.style.textAlign = 'center';
        warningBanner.style.backgroundColor = bannerContent.type === 'warning' ? '#f39c12' : 
                                            bannerContent.type === 'error' ? '#e74c3c' :
                                            bannerContent.type === 'success' ? '#27ae60' : '#3498db';
        warningBanner.style.color = 'white';
        warningBanner.style.fontWeight = 'bold';
        
        warningBanner.appendChild(closeButton);
    }
});
