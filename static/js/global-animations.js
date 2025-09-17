// Global Animation System and Interactive Features

// Initialize global animation system
document.addEventListener('DOMContentLoaded', function() {
    initGlobalAnimations();
    initScrollAnimations();
    initInteractiveElements();
    initNotificationSystem();
    initAchievementSystem();
    initThemeManager();
});

// Global animation initialization
function initGlobalAnimations() {
    // Add animation observer for elements entering viewport
    setupIntersectionObserver();
    
    // Initialize page transition effects
    initPageTransitions();
    
    // Setup loading animations
    initLoadingAnimations();
    
    // Initialize scroll-based animations
    initScrollBasedAnimations();
}

// Intersection Observer for viewport animations
function setupIntersectionObserver() {
    const options = {
        threshold: 0.1,
        rootMargin: '50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                
                // Add visible class to trigger animations
                element.classList.add('visible');
                
                // Handle specific animation types
                if (element.classList.contains('fade-in-up')) {
                    element.style.opacity = '1';
                    element.style.transform = 'translateY(0)';
                }
                
                if (element.classList.contains('slide-in-left')) {
                    element.style.opacity = '1';
                    element.style.transform = 'translateX(0)';
                }
                
                if (element.classList.contains('scale-in')) {
                    element.style.opacity = '1';
                    element.style.transform = 'scale(1)';
                }
                
                // Stagger child animations
                staggerChildAnimations(element);
                
                // Stop observing once animated
                observer.unobserve(element);
            }
        });
    }, options);
    
    // Observe all animatable elements
    const animatableElements = document.querySelectorAll('.fade-in-up, .slide-in-left, .slide-in-right, .scale-in, .bounce-in');
    animatableElements.forEach(el => observer.observe(el));
}

function staggerChildAnimations(parent) {
    const children = parent.querySelectorAll('.stagger-child');
    children.forEach((child, index) => {
        setTimeout(() => {
            child.classList.add('visible');
        }, index * 100);
    });
}

// Page transitions
function initPageTransitions() {
    // Add page load animation
    document.body.classList.add('page-loaded');
    
    // Handle navigation transitions
    const navLinks = document.querySelectorAll('a[href]:not([target="_blank"])');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.hostname === window.location.hostname) {
                handlePageTransition(e, this.href);
            }
        });
    });
}

function handlePageTransition(event, url) {
    // Skip for external links or special cases
    if (event.ctrlKey || event.metaKey || event.target.closest('.no-transition')) {
        return;
    }
    
    event.preventDefault();
    
    // Add transition overlay
    const overlay = document.createElement('div');
    overlay.className = 'page-transition-overlay';
    document.body.appendChild(overlay);
    
    // Animate overlay
    setTimeout(() => {
        overlay.classList.add('active');
    }, 10);
    
    // Navigate after animation
    setTimeout(() => {
        window.location.href = url;
    }, 300);
}

// Loading animations
function initLoadingAnimations() {
    // Show loading for forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            showLoadingState(this);
        });
    });
    
    // Show loading for AJAX requests
    setupAjaxLoadingIndicators();
}

function showLoadingState(element) {
    const submitBtn = element.querySelector('button[type="submit"], input[type="submit"]');
    if (submitBtn) {
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        
        // Store original text for restoration
        submitBtn.dataset.originalText = originalText;
    }
}

// Scroll-based animations
function initScrollBasedAnimations() {
    let ticking = false;
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(updateScrollAnimations);
            ticking = true;
        }
    });
}

function updateScrollAnimations() {
    const scrollY = window.scrollY;
    const windowHeight = window.innerHeight;
    
    // Header scroll effects
    const header = document.querySelector('header');
    if (header) {
        if (scrollY > 100) {
            header.classList.add('header-scrolled');
        } else {
            header.classList.remove('header-scrolled');
        }
    }
    
    // Parallax effects
    const parallaxElements = document.querySelectorAll('.parallax');
    parallaxElements.forEach(el => {
        const speed = el.dataset.speed || 0.5;
        const yPos = -(scrollY * speed);
        el.style.transform = `translateY(${yPos}px)`;
    });
    
    // Progress bar for reading progress
    updateReadingProgress();
    
    ticking = false;
}

function updateReadingProgress() {
    const progressBar = document.querySelector('.reading-progress');
    if (progressBar) {
        const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = (window.scrollY / documentHeight) * 100;
        progressBar.style.width = `${Math.min(scrollPercent, 100)}%`;
    }
}

// Interactive elements
function initInteractiveElements() {
    // Enhanced button interactions
    initButtonInteractions();
    
    // Card hover effects
    initCardInteractions();
    
    // Form field enhancements
    initFormEnhancements();
    
    // Tooltip system
    initTooltipSystem();
}

function initButtonInteractions() {
    const buttons = document.querySelectorAll('.btn-animated, .btn');
    
    buttons.forEach(button => {
        // Add ripple effect
        button.addEventListener('click', function(e) {
            createRippleEffect(e, this);
        });
        
        // Add loading state for async actions
        if (button.dataset.async === 'true') {
            button.addEventListener('click', function() {
                if (!this.disabled) {
                    addLoadingSpinner(this);
                }
            });
        }
    });
}

function createRippleEffect(event, element) {
    const ripple = document.createElement('span');
    ripple.classList.add('ripple');
    
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
    `;
    
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

function initCardInteractions() {
    const cards = document.querySelectorAll('.card-animated, .card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('card-hovered');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('card-hovered');
        });
        
        // Add tilt effect for special cards
        if (card.classList.contains('tilt-effect')) {
            initTiltEffect(card);
        }
    });
}

function initTiltEffect(element) {
    element.addEventListener('mousemove', function(e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 10;
        const rotateY = (centerX - x) / 10;
        
        this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    });
    
    element.addEventListener('mouseleave', function() {
        this.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
    });
}

// Form enhancements
function initFormEnhancements() {
    // Floating labels
    const formGroups = document.querySelectorAll('.form-group');
    formGroups.forEach(group => {
        const input = group.querySelector('input, textarea, select');
        const label = group.querySelector('label');
        
        if (input && label) {
            input.addEventListener('focus', function() {
                group.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                if (!this.value) {
                    group.classList.remove('focused');
                }
            });
            
            // Check if already has value
            if (input.value) {
                group.classList.add('focused');
            }
        }
    });
    
    // Real-time validation
    const inputs = document.querySelectorAll('input[data-validate]');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            validateInput(this);
        });
    });
}

function validateInput(input) {
    const validationType = input.dataset.validate;
    let isValid = true;
    let message = '';
    
    switch (validationType) {
        case 'email':
            isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value);
            message = 'Please enter a valid email address';
            break;
        case 'password':
            isValid = input.value.length >= 8;
            message = 'Password must be at least 8 characters';
            break;
        case 'required':
            isValid = input.value.trim() !== '';
            message = 'This field is required';
            break;
    }
    
    showValidationResult(input, isValid, message);
}

function showValidationResult(input, isValid, message) {
    const formGroup = input.closest('.form-group');
    const feedback = formGroup.querySelector('.validation-feedback') || createValidationFeedback(formGroup);
    
    formGroup.classList.remove('valid', 'invalid');
    
    if (isValid) {
        formGroup.classList.add('valid');
        feedback.textContent = '';
    } else {
        formGroup.classList.add('invalid');
        feedback.textContent = message;
    }
}

function createValidationFeedback(formGroup) {
    const feedback = document.createElement('div');
    feedback.className = 'validation-feedback';
    formGroup.appendChild(feedback);
    return feedback;
}

// Tooltip system
function initTooltipSystem() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element) {
    const tooltipText = element.dataset.tooltip;
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = tooltipText;
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2}px`;
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
    
    // Animate in
    setTimeout(() => {
        tooltip.classList.add('show');
    }, 10);
}

function hideTooltip() {
    const tooltip = document.querySelector('.custom-tooltip');
    if (tooltip) {
        tooltip.classList.remove('show');
        setTimeout(() => {
            tooltip.remove();
        }, 300);
    }
}

// Notification system
function initNotificationSystem() {
    // Create notification container
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const container = document.querySelector('.notification-container');
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getIconForType(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="closeNotification(this)">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Auto-remove
    if (duration > 0) {
        setTimeout(() => {
            closeNotification(notification.querySelector('.notification-close'));
        }, duration);
    }
    
    return notification;
}

function closeNotification(closeBtn) {
    const notification = closeBtn.closest('.notification');
    notification.classList.remove('show');
    setTimeout(() => {
        notification.remove();
    }, 300);
}

function getIconForType(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Achievement system
function initAchievementSystem() {
    // Listen for achievement events
    window.addEventListener('achievementUnlocked', function(e) {
        showAchievementNotification(e.detail);
    });
}

function showAchievementNotification(achievement) {
    const achievementElement = document.createElement('div');
    achievementElement.className = 'achievement-popup';
    
    achievementElement.innerHTML = `
        <div class="achievement-content">
            <div class="achievement-icon">
                <i class="fas fa-trophy"></i>
            </div>
            <div class="achievement-text">
                <h4>Achievement Unlocked!</h4>
                <p>${achievement.name}</p>
                <span class="achievement-description">${achievement.description}</span>
            </div>
        </div>
    `;
    
    document.body.appendChild(achievementElement);
    
    // Animate in
    setTimeout(() => {
        achievementElement.classList.add('show');
    }, 100);
    
    // Add confetti effect
    createConfettiEffect();
    
    // Auto-remove
    setTimeout(() => {
        achievementElement.classList.remove('show');
        setTimeout(() => {
            achievementElement.remove();
        }, 500);
    }, 5000);
}

function createConfettiEffect() {
    const colors = ['#4169e1', '#d4a859', '#28a745', '#dc3545', '#17a2b8'];
    const confettiContainer = document.createElement('div');
    confettiContainer.className = 'confetti';
    
    for (let i = 0; i < 50; i++) {
        const confettiPiece = document.createElement('div');
        confettiPiece.className = 'confetti-piece';
        confettiPiece.style.left = Math.random() * 100 + 'vw';
        confettiPiece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confettiPiece.style.animationDelay = Math.random() * 3 + 's';
        confettiPiece.style.animationDuration = (Math.random() * 3 + 2) + 's';
        
        confettiContainer.appendChild(confettiPiece);
    }
    
    document.body.appendChild(confettiContainer);
    
    // Remove after animation
    setTimeout(() => {
        confettiContainer.remove();
    }, 6000);
}

function celebrateStreak(streakCount) {
    // Enhanced celebration for streak milestones
    if (streakCount % 7 === 0) {
        createConfettiEffect();
        showNotification(`🔥 ${streakCount} day streak! You're on fire!`, 'success', 3000);
    }
}

// Theme manager
function initThemeManager() {
    // Check for saved theme preference or default to 'light'
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Theme toggle functionality
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Animate theme transition
    document.body.classList.add('theme-transitioning');
    setTimeout(() => {
        document.body.classList.remove('theme-transitioning');
    }, 300);
}

// Utility functions
function addLoadingSpinner(button) {
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    button.disabled = true;
    
    // Store original content for restoration
    button.dataset.originalContent = originalContent;
}

function removeLoadingSpinner(button) {
    if (button.dataset.originalContent) {
        button.innerHTML = button.dataset.originalContent;
        button.disabled = false;
        delete button.dataset.originalContent;
    }
}

// AJAX loading indicators
function setupAjaxLoadingIndicators() {
    // Override fetch to show global loading
    const originalFetch = window.fetch;
    let activeRequests = 0;
    
    window.fetch = function(...args) {
        activeRequests++;
        updateGlobalLoadingState();
        
        return originalFetch.apply(this, args)
            .then(response => {
                activeRequests--;
                updateGlobalLoadingState();
                return response;
            })
            .catch(error => {
                activeRequests--;
                updateGlobalLoadingState();
                throw error;
            });
    };
}

function updateGlobalLoadingState() {
    const loadingIndicator = document.querySelector('.global-loading');
    if (loadingIndicator) {
        if (activeRequests > 0) {
            loadingIndicator.classList.add('active');
        } else {
            loadingIndicator.classList.remove('active');
        }
    }
}

// Export functions for global use
window.showNotification = showNotification;
window.showAchievementNotification = showAchievementNotification;
window.celebrateStreak = celebrateStreak;
window.createRippleEffect = createRippleEffect;

// Add CSS for animations and effects
const animationCSS = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.4);
        pointer-events: none;
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .page-transition-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(45deg, #4169e1, #d4a859);
        z-index: 9999;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
    }
    
    .page-transition-overlay.active {
        opacity: 1;
    }
    
    .notification-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1050;
        max-width: 400px;
    }
    
    .notification {
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        margin-bottom: 10px;
        transform: translateX(400px);
        transition: transform 0.3s ease, opacity 0.3s ease;
        opacity: 0;
    }
    
    .notification.show {
        transform: translateX(0);
        opacity: 1;
    }
    
    .theme-transitioning {
        transition: background-color 0.3s ease, color 0.3s ease;
    }
`;

// Add styles to document
const styleSheet = document.createElement('style');
styleSheet.textContent = animationCSS;
document.head.appendChild(styleSheet);