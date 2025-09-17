/**
 * Performance optimization utilities for PrepForge
 * Handles lazy loading, image optimization, and performance monitoring
 */

class PerformanceManager {
    constructor() {
        this.lazyImages = new Set();
        this.performanceObserver = null;
        this.intersectionObserver = null;
        this.loadStartTime = performance.now();
        
        this.init();
    }
    
    init() {
        // Initialize lazy loading
        this.setupLazyLoading();
        
        // Monitor performance
        this.setupPerformanceMonitoring();
        
        // Optimize critical resources
        this.optimizeCriticalResources();
        
        // Setup mobile optimizations
        this.setupMobileOptimizations();
        
        console.log('🚀 Performance Manager initialized');
    }
    
    setupLazyLoading() {
        // Create intersection observer for lazy loading
        if ('IntersectionObserver' in window) {
            this.intersectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadLazyElement(entry.target);
                        this.intersectionObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });
            
            // Observe all lazy images
            this.observeLazyImages();
        } else {
            // Fallback for older browsers
            this.loadAllLazyImages();
        }
    }
    
    observeLazyImages() {
        const lazyImages = document.querySelectorAll('img[data-src], .lazy-image');
        lazyImages.forEach(img => {
            this.lazyImages.add(img);
            if (this.intersectionObserver) {
                this.intersectionObserver.observe(img);
            }
        });
    }
    
    loadLazyElement(element) {
        if (element.dataset.src) {
            // Load image
            const img = new Image();
            img.onload = () => {
                element.src = element.dataset.src;
                element.classList.add('loaded');
                element.removeAttribute('data-src');
                this.lazyImages.delete(element);
            };
            img.onerror = () => {
                console.warn('Failed to load lazy image:', element.dataset.src);
                element.classList.add('error');
            };
            img.src = element.dataset.src;
        } else if (element.classList.contains('lazy-image')) {
            // Handle other lazy content
            element.classList.add('loaded');
            this.lazyImages.delete(element);
        }
    }
    
    loadAllLazyImages() {
        // Fallback: load all images immediately
        this.lazyImages.forEach(img => this.loadLazyElement(img));
    }
    
    setupPerformanceMonitoring() {
        // Monitor Core Web Vitals
        if ('PerformanceObserver' in window) {
            // Largest Contentful Paint (LCP)
            this.observeMetric('largest-contentful-paint', (entries) => {
                const lastEntry = entries[entries.length - 1];
                console.log('LCP:', lastEntry.startTime);
                this.trackMetric('lcp', lastEntry.startTime);
            });
            
            // First Input Delay (FID)
            this.observeMetric('first-input', (entries) => {
                entries.forEach(entry => {
                    console.log('FID:', entry.processingStart - entry.startTime);
                    this.trackMetric('fid', entry.processingStart - entry.startTime);
                });
            });
            
            // Cumulative Layout Shift (CLS)
            this.observeMetric('layout-shift', (entries) => {
                let clsValue = 0;
                entries.forEach(entry => {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                });
                if (clsValue > 0) {
                    console.log('CLS:', clsValue);
                    this.trackMetric('cls', clsValue);
                }
            });
        }
        
        // Monitor page load time
        window.addEventListener('load', () => {
            const loadTime = performance.now() - this.loadStartTime;
            console.log('Page load time:', loadTime + 'ms');
            this.trackMetric('load_time', loadTime);
            
            // Check if we meet the <2s target
            if (loadTime < 2000) {
                console.log('✅ Page loaded under 2s target');
            } else {
                console.warn('⚠️ Page load time exceeds 2s target');
            }
        });
    }
    
    observeMetric(type, callback) {
        try {
            const observer = new PerformanceObserver((list) => {
                callback(list.getEntries());
            });
            observer.observe({ type: type, buffered: true });
        } catch (e) {
            console.warn('Performance observer not supported for:', type);
        }
    }
    
    trackMetric(name, value) {
        // Send metrics to analytics (if available)
        if (window.mixpanel && typeof window.mixpanel.track === 'function') {
            window.mixpanel.track('Performance Metric', {
                metric: name,
                value: value,
                page: window.location.pathname,
                user_agent: navigator.userAgent,
                timestamp: Date.now()
            });
        }
    }
    
    optimizeCriticalResources() {
        // Preload critical fonts
        this.preloadFont('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        // Optimize images
        this.optimizeImages();
        
        // Minimize reflows and repaints
        this.minimizeLayoutShifts();
    }
    
    preloadFont(fontUrl) {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = fontUrl;
        link.as = 'style';
        link.crossOrigin = 'anonymous';
        document.head.appendChild(link);
    }
    
    optimizeImages() {
        const images = document.querySelectorAll('img:not([data-src])');
        images.forEach(img => {
            // Add loading="lazy" for native lazy loading
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
            
            // Add decode="async" for better performance
            if (!img.hasAttribute('decode')) {
                img.setAttribute('decode', 'async');
            }
            
            // Optimize image sizes based on viewport
            this.optimizeImageSizes(img);
        });
    }
    
    optimizeImageSizes(img) {
        // Add responsive image sizes if not present
        if (!img.hasAttribute('sizes') && img.hasAttribute('srcset')) {
            img.setAttribute('sizes', '(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw');
        }
    }
    
    minimizeLayoutShifts() {
        // Add explicit dimensions to prevent layout shifts
        const images = document.querySelectorAll('img:not([width]):not([height])');
        images.forEach(img => {
            img.addEventListener('load', function() {
                if (!this.hasAttribute('width')) {
                    this.setAttribute('width', this.naturalWidth);
                    this.setAttribute('height', this.naturalHeight);
                }
            });
        });
        
        // Reserve space for dynamic content
        this.reserveSpaceForDynamicContent();
    }
    
    reserveSpaceForDynamicContent() {
        // Add minimum heights to prevent layout shifts
        const containers = document.querySelectorAll('.question-container, .options-container');
        containers.forEach(container => {
            if (!container.style.minHeight && !container.classList.contains('has-min-height')) {
                container.style.minHeight = container.scrollHeight + 'px';
                container.classList.add('has-min-height');
            }
        });
    }
    
    setupMobileOptimizations() {
        // Optimize touch interactions
        this.optimizeTouchTargets();
        
        // Reduce motion for better performance on mobile
        this.handleReducedMotion();
        
        // Optimize viewport
        this.optimizeViewport();
    }
    
    optimizeTouchTargets() {
        const touchTargets = document.querySelectorAll('.btn, .option, a, button');
        touchTargets.forEach(target => {
            const rect = target.getBoundingClientRect();
            if (rect.width < 44 || rect.height < 44) {
                target.style.minWidth = '44px';
                target.style.minHeight = '44px';
                target.style.display = 'inline-flex';
                target.style.alignItems = 'center';
                target.style.justifyContent = 'center';
            }
        });
    }
    
    handleReducedMotion() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        if (prefersReducedMotion.matches) {
            document.body.classList.add('reduce-motion');
        }
    }
    
    optimizeViewport() {
        // Ensure proper viewport configuration
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            viewport.content = 'width=device-width, initial-scale=1.0, viewport-fit=cover';
            document.head.appendChild(viewport);
        }
    }
    
    // Public methods for manual optimization
    optimizeQuestion(questionElement) {
        // Optimize a specific question element
        if (!questionElement) return;
        
        // Add loading state
        questionElement.classList.add('loading');
        
        // Optimize images within the question
        const images = questionElement.querySelectorAll('img');
        images.forEach(img => this.optimizeImageSizes(img));
        
        // Reserve space to prevent layout shifts
        if (!questionElement.style.minHeight) {
            questionElement.style.minHeight = '400px';
        }
        
        // Remove loading state after content is ready
        setTimeout(() => {
            questionElement.classList.remove('loading');
        }, 100);
    }
    
    measureLoadTime(startTime) {
        const endTime = performance.now();
        const loadTime = endTime - startTime;
        
        console.log(`Load time: ${loadTime.toFixed(2)}ms`);
        this.trackMetric('custom_load_time', loadTime);
        
        return loadTime;
    }
    
    // Cleanup method
    destroy() {
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        if (this.performanceObserver) {
            this.performanceObserver.disconnect();
        }
        this.lazyImages.clear();
    }
}

// Initialize performance manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.performanceManager = new PerformanceManager();
    });
} else {
    window.performanceManager = new PerformanceManager();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceManager;
}