// Mobile menu toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const hamburgerMenu = document.getElementById('hamburgerMenu');
    const mobileNavigation = document.getElementById('mobileNavigation');
    const closeMenuButton = document.getElementById('closeMenuButton');

    if (hamburgerMenu && mobileNavigation) {
        hamburgerMenu.addEventListener('click', function() {
            mobileNavigation.classList.add('active');
        });
    }

    if (closeMenuButton && mobileNavigation) {
        closeMenuButton.addEventListener('click', function() {
            mobileNavigation.classList.remove('active');
        });
    }

    // Close menu when clicking on a link
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-links a');
    mobileNavLinks.forEach(link => {
        link.addEventListener('click', function() {
            mobileNavigation.classList.remove('active');
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        if (mobileNavigation.classList.contains('active') && 
            !mobileNavigation.contains(event.target) && 
            !hamburgerMenu.contains(event.target)) {
            mobileNavigation.classList.remove('active');
        }
    });
});
