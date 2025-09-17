/**
 * Responsive Lazy Image Loading for Flask App
 * Optimizes image loading without changing layout
 */

class ResponsiveLazyImages {
    constructor() {
        this.imageObserver = null;
        this.images = [];
        this.init();
    }

    init() {
        console.log('🖼️ Initializing responsive lazy image loading');
        
        try {
            // Create intersection observer for lazy loading
            this.createObserver();
            
            // Find all images that should be lazy loaded
            this.setupLazyImages();
            
            // Setup responsive image listeners
            this.setupResponsiveImages();
            
            console.log('✅ Lazy image loading initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize lazy loading:', error);
        }
    }

    createObserver() {
        if ('IntersectionObserver' in window) {
            this.imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.loadImage(img);
                        observer.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });
        }
    }

    setupLazyImages() {
        try {
            // Find images that should be lazy loaded (not critical above-the-fold)
            const lazyImages = document.querySelectorAll('img[data-src]');
            console.log(`Found ${lazyImages.length} images with data-src attribute`);
            
            lazyImages.forEach(img => {
                const src = img.getAttribute('data-src');
                if (src && src !== 'undefined' && src !== '') {
                    if (this.imageObserver) {
                        this.imageObserver.observe(img);
                    } else {
                        // Fallback for browsers without IntersectionObserver
                        this.loadImage(img);
                    }
                } else {
                    console.warn('Skipping image with invalid data-src:', src);
                }
            });

            // Convert existing images to lazy loading format (skip for now to prevent issues)
            // We'll only handle images that are explicitly marked with data-src
            
            console.log('Lazy image setup completed');
        } catch (error) {
            console.error('Error in setupLazyImages:', error);
        }
    }

    shouldMakeLazy(img) {
        // Don't lazy load critical images
        const criticalClasses = ['prepforge-logo', 'hero-image'];
        const criticalElements = ['header', 'nav'];
        
        // Check if image has critical class
        if (criticalClasses.some(cls => img.classList.contains(cls))) {
            return false;
        }
        
        // Check if image is in critical elements
        const parent = img.closest(criticalElements.join(','));
        if (parent) {
            return false;
        }
        
        // Check if image is above the fold (rough estimate)
        const rect = img.getBoundingClientRect();
        const isAboveFold = rect.top < window.innerHeight;
        
        return !isAboveFold;
    }

    convertToLazy(img) {
        // Only convert if not already converted
        if (img.hasAttribute('data-src')) return;
        
        const originalSrc = img.src;
        
        // Don't convert if src is invalid
        if (!originalSrc || originalSrc === 'undefined' || originalSrc === '' || originalSrc.includes('undefined')) {
            console.warn('Skipping lazy conversion for invalid src:', originalSrc);
            return;
        }
        
        img.setAttribute('data-src', originalSrc);
        
        // Create placeholder
        img.src = this.createPlaceholder(img);
        img.classList.add('lazy-image');
        
        if (this.imageObserver) {
            this.imageObserver.observe(img);
        }
    }

    createPlaceholder(img) {
        // Create a small SVG placeholder that maintains aspect ratio
        const width = img.getAttribute('width') || img.offsetWidth || 300;
        const height = img.getAttribute('height') || img.offsetHeight || 200;
        
        return `data:image/svg+xml;base64,${btoa(`
            <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#f8f9fa"/>
                <text x="50%" y="50%" font-family="system-ui,sans-serif" font-size="14" 
                      fill="#6c757d" text-anchor="middle" dominant-baseline="middle">
                    Loading...
                </text>
            </svg>
        `)}`;
    }

    createErrorPlaceholder(img) {
        // Create an error SVG placeholder
        const width = img.getAttribute('width') || img.offsetWidth || 300;
        const height = img.getAttribute('height') || img.offsetHeight || 200;
        
        return `data:image/svg+xml;base64,${btoa(`
            <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#f8f9fa" stroke="#dc3545" stroke-width="2"/>
                <text x="50%" y="50%" font-family="system-ui,sans-serif" font-size="12" 
                      fill="#dc3545" text-anchor="middle" dominant-baseline="middle">
                    ⚠ Image failed to load
                </text>
            </svg>
        `)}`;
    }

    loadImage(img) {
        const src = img.getAttribute('data-src');
        if (!src || src === 'undefined' || src === '') {
            console.warn('Invalid image source:', src, 'for image:', img);
            return;
        }

        // Validate URL format
        try {
            const url = new URL(src, window.location.origin);
            if (!url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
                console.warn('Invalid image extension for:', src);
                return;
            }
        } catch (e) {
            console.warn('Invalid URL format:', src);
            return;
        }

        // Create a new image to preload
        const imageLoader = new Image();
        
        imageLoader.onload = () => {
            img.src = src;
            img.classList.add('lazy-loaded');
            img.classList.remove('lazy-loading');
            
            // Remove data-src to prevent reloading
            img.removeAttribute('data-src');
        };
        
        imageLoader.onerror = () => {
            img.classList.add('lazy-error');
            img.classList.remove('lazy-loading');
            console.warn('Failed to load image:', src);
            
            // Set a fallback placeholder
            img.src = this.createErrorPlaceholder(img);
        };
        
        img.classList.add('lazy-loading');
        imageLoader.src = src;
    }

    setupResponsiveImages() {
        // Handle window resize for responsive images
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.updateResponsiveImages();
            }, 250);
        });
    }

    updateResponsiveImages() {
        const images = document.querySelectorAll('img[data-responsive]');
        images.forEach(img => {
            this.setResponsiveSource(img);
        });
    }

    setResponsiveSource(img) {
        const screenWidth = window.innerWidth;
        const pixelRatio = window.devicePixelRatio || 1;
        
        let size = 'medium';
        if (screenWidth <= 480) {
            size = 'small';
        } else if (screenWidth <= 768) {
            size = 'medium';
        } else if (screenWidth <= 1200) {
            size = 'large';
        } else {
            size = 'xlarge';
        }
        
        // Adjust for high DPI screens
        if (pixelRatio > 1.5) {
            const sizeMap = {
                'small': 'medium',
                'medium': 'large',
                'large': 'xlarge',
                'xlarge': 'xlarge'
            };
            size = sizeMap[size];
        }
        
        const baseSrc = img.getAttribute('data-responsive');
        if (baseSrc) {
            const responsiveSrc = this.getResponsiveUrl(baseSrc, size);
            
            if (img.hasAttribute('data-src')) {
                img.setAttribute('data-src', responsiveSrc);
            } else {
                img.src = responsiveSrc;
            }
        }
    }

    getResponsiveUrl(baseSrc, size) {
        // Convert image path to responsive version
        // Example: /static/assets/image.jpg -> /static/assets/image-medium.jpg
        const lastDot = baseSrc.lastIndexOf('.');
        if (lastDot === -1) return baseSrc;
        
        const name = baseSrc.substring(0, lastDot);
        const ext = baseSrc.substring(lastDot);
        
        return `${name}-${size}${ext}`;
    }

    // Public method to manually trigger image loading
    loadImagesInContainer(container) {
        const images = container.querySelectorAll('img[data-src]');
        images.forEach(img => this.loadImage(img));
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.lazyImages = new ResponsiveLazyImages();
    });
} else {
    window.lazyImages = new ResponsiveLazyImages();
}

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ResponsiveLazyImages;
}