/**
 * Global Error Handler for Console Errors
 * Prevents common JavaScript errors and provides fallbacks
 */

class ErrorHandler {
    constructor() {
        this.init();
    }

    init() {
        // Handle uncaught JavaScript errors
        window.addEventListener('error', (event) => {
            this.logError('JavaScript Error', {
                message: event.error?.message || event.message,
                filename: event.filename,
                line: event.lineno,
                column: event.colno,
                stack: event.error?.stack
            });
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Promise Rejection', {
                reason: event.reason
            });
        });

        // Add image error handling
        this.setupImageErrorHandling();
        
        // Add form validation
        this.setupFormValidation();
    }

    logError(type, details) {
        console.group(`🚨 ${type}`);
        console.error('Details:', details);
        console.groupEnd();
        
        // Optionally send to analytics (without exposing sensitive data)
        if (window.mixpanel && typeof window.mixpanel.track === 'function') {
            try {
                window.mixpanel.track('JavaScript Error', {
                    error_type: type,
                    message: details.message?.substring(0, 100), // Limit message length
                    url: window.location.pathname
                });
            } catch (e) {
                // Fail silently if mixpanel isn't available
            }
        }
    }

    setupImageErrorHandling() {
        // Add global image error handler
        document.addEventListener('error', (event) => {
            if (event.target.tagName === 'IMG') {
                const img = event.target;
                const src = img.src || img.getAttribute('data-src');
                
                if (src && (src.includes('undefined') || src === 'undefined')) {
                    console.warn('Removing image with undefined source:', img);
                    img.style.display = 'none';
                    return;
                }
                
                // Create error placeholder for broken images
                this.createImageErrorPlaceholder(img);
            }
        }, true);
    }

    createImageErrorPlaceholder(img) {
        const width = img.offsetWidth || 150;
        const height = img.offsetHeight || 100;
        
        const errorSrc = `data:image/svg+xml;base64,${btoa(`
            <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="1"/>
                <text x="50%" y="50%" font-family="system-ui,sans-serif" font-size="12" 
                      fill="#6c757d" text-anchor="middle" dominant-baseline="middle">
                    Image not available
                </text>
            </svg>
        `)}`;
        
        img.src = errorSrc;
        img.classList.add('image-error');
    }

    setupFormValidation() {
        // Add form validation helpers
        document.addEventListener('submit', (event) => {
            const form = event.target;
            if (!form.checkValidity) return;
            
            // Custom validation for select elements
            const selects = form.querySelectorAll('select[required]');
            selects.forEach(select => {
                if (!select.value || select.value === '') {
                    select.setCustomValidity('Please select an option');
                    select.classList.add('is-invalid');
                } else {
                    select.setCustomValidity('');
                    select.classList.remove('is-invalid');
                }
            });
        });
    }

    // Utility method to validate URLs
    static isValidImageUrl(url) {
        if (!url || url === 'undefined' || url === '') return false;
        
        try {
            const urlObj = new URL(url, window.location.origin);
            return urlObj.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i) !== null;
        } catch (e) {
            return false;
        }
    }

    // Utility method for safe DOM queries
    static safeQuerySelector(selector) {
        try {
            return document.querySelector(selector);
        } catch (e) {
            console.warn('Invalid selector:', selector);
            return null;
        }
    }

    // Utility method for safe event listeners
    static safeAddEventListener(element, event, handler) {
        if (element && typeof element.addEventListener === 'function') {
            try {
                element.addEventListener(event, handler);
                return true;
            } catch (e) {
                console.warn('Failed to add event listener:', e);
                return false;
            }
        }
        return false;
    }
}

// Initialize error handler when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.errorHandler = new ErrorHandler();
    });
} else {
    window.errorHandler = new ErrorHandler();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}