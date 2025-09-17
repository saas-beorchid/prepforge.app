// Landing Page Animations and Interactions

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize scroll animations
    initScrollAnimations();
    
    // Initialize staggered animations
    initStaggeredAnimations();
    
    // Add smooth scrolling for anchor links
    initSmoothScrolling();
    
    // Initialize typed text animations
    initTypedTextAnimations();
    
    // Initialize progress counters
    initProgressCounters();
    
    // Initialize ripple effects
    initRippleEffects();
});

// Scroll Animations
function initScrollAnimations() {
    // Select all elements with animation classes
    const fadeElements = document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right, .fade-in-up, .scale-in');
    
    // Create a new Intersection Observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            // If element is in viewport
            if (entry.isIntersecting) {
                // Add visible class to trigger animation
                entry.target.classList.add('visible');
                // Stop observing after animation is triggered
                observer.unobserve(entry.target);
            }
        });
    }, {
        root: null, // viewport
        threshold: 0.05, // trigger when 5% of element is visible
        rootMargin: '0px 0px -30px 0px' // negative margin to trigger earlier
    });
    
    // Start observing elements
    fadeElements.forEach(element => {
        observer.observe(element);
    });
}

// Staggered Animations
function initStaggeredAnimations() {
    // Get all stagger parent elements
    const staggerContainers = document.querySelectorAll('.stagger-container');
    
    staggerContainers.forEach(container => {
        // Get all stagger items within this container
        const staggerItems = container.querySelectorAll('.stagger-item');
        
        // Create observer for this container
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                // Apply staggered animations with delay
                staggerItems.forEach((item, index) => {
                    setTimeout(() => {
                        item.classList.add('stagger-visible');
                    }, 100 * index); // 100ms delay between each item
                });
                
                // Stop observing after triggering
                observer.unobserve(container);
            }
        }, {
            threshold: 0.1
        });
        
        // Start observing the container
        observer.observe(container);
    });
}

// Smooth Scrolling
function initSmoothScrolling() {
    // Select all anchor links that point to an ID on the page
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Prevent default anchor behavior
            e.preventDefault();
            
            // Get the target element
            const targetId = this.getAttribute('href');
            if (targetId === '#') return; // Skip if href is just "#"
            
            const targetElement = document.querySelector(targetId);
            if (!targetElement) return; // Skip if target doesn't exist
            
            // Smooth scroll to target
            window.scrollTo({
                top: targetElement.offsetTop - 80, // Offset for header
                behavior: 'smooth'
            });
        });
    });
}

// Helper function for throttling scroll events
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Typed Text Animations
function initTypedTextAnimations() {
    const typedElements = document.querySelectorAll('.typed-text');
    
    typedElements.forEach(element => {
        const text = element.textContent;
        const strings = [text];
        
        // Clear the element
        element.textContent = '';
        
        // Add typing cursor class
        element.classList.add('typing-cursor');
        
        // Simple typing effect
        let charIndex = 0;
        const typeSpeed = 50;
        
        function typeChar() {
            if (charIndex < text.length) {
                element.textContent += text.charAt(charIndex);
                charIndex++;
                setTimeout(typeChar, typeSpeed);
            } else {
                // Remove cursor after typing is complete
                setTimeout(() => {
                    element.classList.remove('typing-cursor');
                }, 1000);
            }
        }
        
        // Start typing when element is visible
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                setTimeout(typeChar, 500);
                observer.unobserve(element);
            }
        });
        
        observer.observe(element);
    });
}

// Progress Counters
function initProgressCounters() {
    const counters = document.querySelectorAll('.counter');
    
    const animateCounter = (counter) => {
        const target = parseInt(counter.getAttribute('data-count'));
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.textContent = Math.floor(current).toLocaleString();
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target.toLocaleString();
            }
        };
        
        updateCounter();
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    });
    
    counters.forEach(counter => {
        observer.observe(counter);
    });
}

// Ripple Effects
function initRippleEffects() {
    const rippleButtons = document.querySelectorAll('.ripple');
    
    rippleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple-effect');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// Parallax Effect (optional)
function initParallaxEffect() {
    const parallaxElements = document.querySelectorAll('.parallax');
    
    window.addEventListener('scroll', throttle(function() {
        const scrollTop = window.pageYOffset;
        
        parallaxElements.forEach(element => {
            const speed = element.getAttribute('data-speed') || 0.2;
            element.style.transform = `translateY(${scrollTop * speed}px)`;
        });
    }, 10));
}
