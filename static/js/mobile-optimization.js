/**
 * Mobile optimization utilities for PrepForge
 * Handles touch interactions, responsive behavior, and mobile-specific performance
 */

class MobileOptimizer {
    constructor() {
        this.isMobile = this.detectMobile();
        this.isTouch = this.detectTouch();
        this.viewport = this.getViewportInfo();
        
        this.init();
    }
    
    init() {
        if (this.isMobile) {
            this.setupMobileOptimizations();
            this.optimizeTouchInteractions();
            this.setupMobileNavigation();
            this.optimizeForSmallScreens();
        }
        
        this.setupResponsiveImages();
        this.optimizeInputs();
        this.handleOrientationChange();
        
        console.log('📱 Mobile optimizer initialized', {
            isMobile: this.isMobile,
            isTouch: this.isTouch,
            viewport: this.viewport
        });
    }
    
    detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth <= 768;
    }
    
    detectTouch() {
        return 'ontouchstart' in window || 
               navigator.maxTouchPoints > 0 || 
               navigator.msMaxTouchPoints > 0;
    }
    
    getViewportInfo() {
        return {
            width: window.innerWidth,
            height: window.innerHeight,
            ratio: window.devicePixelRatio || 1
        };
    }
    
    setupMobileOptimizations() {
        // Prevent zoom on double tap
        document.addEventListener('touchstart', function(e) {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        });
        
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(e) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Optimize scrolling
        if (CSS.supports('scroll-behavior', 'smooth')) {
            document.documentElement.style.scrollBehavior = 'smooth';
        }
    }
    
    optimizeTouchInteractions() {
        // Add touch feedback to interactive elements
        const interactiveElements = document.querySelectorAll('button, .btn, .option, .nav-link, a');
        
        interactiveElements.forEach(element => {
            // Ensure minimum touch target size (44px x 44px)
            const rect = element.getBoundingClientRect();
            if (rect.width < 44 || rect.height < 44) {
                element.style.minWidth = '44px';
                element.style.minHeight = '44px';
                element.style.display = element.style.display || 'inline-flex';
                element.style.alignItems = 'center';
                element.style.justifyContent = 'center';
            }
            
            // Add touch feedback
            element.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            }, { passive: true });
            
            element.addEventListener('touchend', function() {
                setTimeout(() => this.classList.remove('touch-active'), 150);
            }, { passive: true });
            
            element.addEventListener('touchcancel', function() {
                this.classList.remove('touch-active');
            }, { passive: true });
        });
    }
    
    setupMobileNavigation() {
        // Enhanced mobile navigation
        const navToggle = document.querySelector('.nav-toggle, .mobile-menu-toggle');
        const navMenu = document.querySelector('.nav-menu, .main-nav');
        
        if (navToggle && navMenu) {
            navToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const isOpen = navMenu.classList.contains('active');
                
                if (isOpen) {
                    this.closeNav(navMenu, navToggle);
                } else {
                    this.openNav(navMenu, navToggle);
                }
            });
            
            // Close nav when clicking outside
            document.addEventListener('click', (e) => {
                if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
                    this.closeNav(navMenu, navToggle);
                }
            });
            
            // Close nav on link click
            navMenu.addEventListener('click', (e) => {
                if (e.target.tagName === 'A') {
                    this.closeNav(navMenu, navToggle);
                }
            });
        }
    }
    
    openNav(navMenu, navToggle) {
        navMenu.classList.add('active');
        navToggle.classList.add('active');
        navToggle.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden'; // Prevent background scroll
    }
    
    closeNav(navMenu, navToggle) {
        navMenu.classList.remove('active');
        navToggle.classList.remove('active');
        navToggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = ''; // Restore scroll
    }
    
    optimizeForSmallScreens() {
        // Optimize question display for mobile
        const questionContainers = document.querySelectorAll('.question-container');
        questionContainers.forEach(container => {
            container.style.padding = this.isMobile ? '1rem' : '2rem';
            container.style.margin = this.isMobile ? '0.5rem 0' : '1rem 0';
        });
        
        // Optimize option spacing
        const options = document.querySelectorAll('.option');
        options.forEach(option => {
            if (this.viewport.width < 400) {
                option.style.padding = '0.75rem';
                option.style.fontSize = '0.9rem';
            }
        });
        
        // Optimize form elements
        const formControls = document.querySelectorAll('.form-control, input, select, textarea');
        formControls.forEach(control => {
            control.style.fontSize = this.isMobile ? '16px' : '14px'; // Prevent zoom on iOS
        });
    }
    
    setupResponsiveImages() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            // Add responsive attributes
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
            
            // Optimize for mobile
            if (this.isMobile && !img.hasAttribute('sizes')) {
                img.setAttribute('sizes', '100vw');
            }
            
            // Add error handling
            img.addEventListener('error', function() {
                this.style.display = 'none';
                console.warn('Failed to load image:', this.src);
            });
        });
    }
    
    optimizeInputs() {
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            // Prevent zoom on iOS by ensuring font-size is at least 16px
            if (this.isMobile && parseFloat(getComputedStyle(input).fontSize) < 16) {
                input.style.fontSize = '16px';
            }
            
            // Add proper input modes for mobile keyboards
            if (input.type === 'email' && !input.hasAttribute('inputmode')) {
                input.setAttribute('inputmode', 'email');
            }
            if (input.type === 'tel' && !input.hasAttribute('inputmode')) {
                input.setAttribute('inputmode', 'tel');
            }
            if (input.type === 'number' && !input.hasAttribute('inputmode')) {
                input.setAttribute('inputmode', 'numeric');
            }
        });
    }
    
    handleOrientationChange() {
        window.addEventListener('orientationchange', () => {
            // Update viewport info
            setTimeout(() => {
                this.viewport = this.getViewportInfo();
                this.optimizeForSmallScreens();
                
                // Trigger resize event for other components
                window.dispatchEvent(new Event('resize'));
            }, 100);
        });
        
        window.addEventListener('resize', () => {
            this.viewport = this.getViewportInfo();
            
            // Update mobile detection based on new size
            const wasMobile = this.isMobile;
            this.isMobile = this.detectMobile();
            
            if (wasMobile !== this.isMobile) {
                this.optimizeForSmallScreens();
            }
        });
    }
    
    // Question-specific optimizations
    optimizeQuestionDisplay() {
        const questionText = document.querySelector('.question-text, #question-text');
        const optionsContainer = document.querySelector('.question-options, .options-container');
        
        if (questionText) {
            questionText.style.fontSize = this.isMobile ? '1rem' : '1.1rem';
            questionText.style.lineHeight = '1.6';
            questionText.style.marginBottom = this.isMobile ? '1rem' : '1.5rem';
        }
        
        if (optionsContainer) {
            const options = optionsContainer.querySelectorAll('.option');
            options.forEach(option => {
                option.style.padding = this.isMobile ? '0.75rem' : '1rem';
                option.style.marginBottom = this.isMobile ? '0.5rem' : '0.75rem';
                
                // Ensure touch targets are adequate
                const rect = option.getBoundingClientRect();
                if (rect.height < 44) {
                    option.style.minHeight = '44px';
                }
            });
        }
    }
    
    // Performance monitoring for mobile
    measureMobilePerformance() {
        const startTime = performance.now();
        
        return {
            measureInteraction: (name) => {
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                // Log slow interactions on mobile
                if (duration > 100) {
                    console.warn(`Slow mobile interaction: ${name} took ${duration.toFixed(2)}ms`);
                }
                
                return duration;
            }
        };
    }
    
    // CSS Custom Properties for mobile
    setCSSVariables() {
        const root = document.documentElement;
        
        root.style.setProperty('--vh', `${this.viewport.height * 0.01}px`);
        root.style.setProperty('--vw', `${this.viewport.width * 0.01}px`);
        root.style.setProperty('--is-mobile', this.isMobile ? '1' : '0');
        root.style.setProperty('--is-touch', this.isTouch ? '1' : '0');
    }
    
    // Public API for other components
    getMobileStatus() {
        return {
            isMobile: this.isMobile,
            isTouch: this.isTouch,
            viewport: this.viewport
        };
    }
    
    // Cleanup
    destroy() {
        document.body.style.overflow = '';
        // Remove event listeners if needed
    }
}

// CSS for mobile optimizations
const mobileCSS = `
.touch-active {
    opacity: 0.7 !important;
    transform: scale(0.98) !important;
}

@media (max-width: 600px) {
    .question-container {
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    
    .option {
        padding: 0.75rem !important;
        margin-bottom: 0.5rem !important;
        min-height: 44px !important;
    }
    
    .btn {
        min-height: 44px !important;
        min-width: 44px !important;
        padding: 0.75rem 1rem !important;
    }
}

@media (max-width: 360px) {
    .container {
        padding: 0 0.75rem !important;
    }
    
    .question-text {
        font-size: 0.95rem !important;
    }
    
    .option {
        padding: 0.5rem !important;
    }
}
`;

// Inject mobile CSS
const styleEl = document.createElement('style');
styleEl.textContent = mobileCSS;
document.head.appendChild(styleEl);

// Initialize mobile optimizer
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.mobileOptimizer = new MobileOptimizer();
    });
} else {
    window.mobileOptimizer = new MobileOptimizer();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileOptimizer;
}