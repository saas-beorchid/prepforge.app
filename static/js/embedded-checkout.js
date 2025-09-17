/**
 * Embedded Stripe Checkout Integration
 * Uses @stripe/stripe-js for seamless in-page checkout experience
 */

import { loadStripe } from '@stripe/stripe-js';

class EmbeddedCheckout {
    constructor() {
        this.stripe = null;
        this.stripePromise = null;
        this.checkout = null;
        this.init();
    }

    async init() {
        try {
            console.log('🚀 Initializing embedded Stripe checkout...');
            
            // Initialize Stripe with publishable key
            this.stripePromise = loadStripe('pk_test_51QbVAeKrCF3SkKYB2PJZPJv5hKAd8gC8H9eJiJKJPJv5hKAd8gC8H9eJiJKJPJv5hKAd8gC8H9eJiJKJPJv5hKAd8gC8H9eJiJKJPJv5hKAd8gC8H9eJiJKJPJv5h');
            this.stripe = await this.stripePromise;
            
            if (!this.stripe) {
                throw new Error('Failed to load Stripe.js');
            }
            
            console.log('✅ Stripe.js loaded successfully');
            
            // Set up upgrade button handler
            this.setupUpgradeHandler();
            
        } catch (error) {
            console.error('❌ Failed to initialize Stripe:', error);
            this.showError('Failed to initialize payment system. Please refresh and try again.');
        }
    }

    setupUpgradeHandler() {
        // Handle upgrade button clicks
        document.addEventListener('click', async (e) => {
            if (e.target.matches('#upgrade-btn, .upgrade-to-pro, [onclick*="upgradeToPro"]')) {
                e.preventDefault();
                await this.startCheckout();
            }
        });
        
        console.log('✅ Upgrade handlers set up');
    }

    async startCheckout() {
        try {
            console.log('🛒 Starting embedded checkout process...');
            this.showLoading('payment', 'Preparing checkout...');

            // Create checkout session on backend
            const response = await fetch('/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to create checkout session');
            }

            console.log('✅ Checkout session created:', data.session_id);

            // Create embedded checkout
            await this.mountEmbeddedCheckout(data.client_secret);

        } catch (error) {
            console.error('❌ Checkout error:', error);
            this.hideLoading('payment');
            this.showError(`Checkout failed: ${error.message}`);
        }
    }

    async mountEmbeddedCheckout(clientSecret) {
        try {
            console.log('🏗️ Mounting embedded checkout...');

            // Create checkout container if it doesn't exist
            let checkoutContainer = document.getElementById('embedded-checkout-container');
            if (!checkoutContainer) {
                checkoutContainer = this.createCheckoutContainer();
            }

            // Clear any existing checkout
            checkoutContainer.innerHTML = '';

            // Mount the embedded checkout
            this.checkout = await this.stripe.initEmbeddedCheckout({
                clientSecret: clientSecret
            });

            this.checkout.mount('#embedded-checkout-container');

            // Show checkout container
            checkoutContainer.style.display = 'block';
            this.hideLoading('payment');

            console.log('✅ Embedded checkout mounted successfully');

            // Track checkout start
            if (window.mixpanel && window.mixpanelToken) {
                window.mixpanel.track('Checkout Started', {
                    method: 'embedded',
                    plan: 'pro'
                });
            }

        } catch (error) {
            console.error('❌ Failed to mount checkout:', error);
            this.hideLoading('payment');
            this.showError('Failed to load checkout. Please try again.');
        }
    }

    createCheckoutContainer() {
        console.log('📦 Creating checkout container...');

        // Create overlay
        const overlay = document.createElement('div');
        overlay.id = 'checkout-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: none;
            overflow-y: auto;
            padding: 2rem;
            box-sizing: border-box;
        `;

        // Create container
        const container = document.createElement('div');
        container.id = 'embedded-checkout-container';
        container.style.cssText = `
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 2rem;
            position: relative;
            min-height: 400px;
        `;

        // Create close button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '&times;';
        closeButton.style.cssText = `
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            font-size: 2rem;
            cursor: pointer;
            color: #666;
            z-index: 1;
        `;
        closeButton.onclick = () => this.closeCheckout();

        container.appendChild(closeButton);
        overlay.appendChild(container);
        document.body.appendChild(overlay);

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.closeCheckout();
            }
        });

        return container;
    }

    closeCheckout() {
        console.log('❌ Closing embedded checkout...');
        
        const overlay = document.getElementById('checkout-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }

        if (this.checkout) {
            this.checkout.destroy();
            this.checkout = null;
        }

        // Track checkout cancellation
        if (window.mixpanel && window.mixpanelToken) {
            window.mixpanel.track('Checkout Cancelled', {
                method: 'embedded'
            });
        }
    }

    showLoading(type, message) {
        const loadingElement = document.getElementById(`${type}-loading`);
        const loadingText = loadingElement?.querySelector('.loading-text');
        
        if (loadingElement) {
            if (loadingText) {
                loadingText.textContent = message;
            }
            loadingElement.style.display = 'block';
            console.log(`⏳ Showing ${type} loading: ${message}`);
        }
    }

    hideLoading(type) {
        const loadingElement = document.getElementById(`${type}-loading`);
        if (loadingElement) {
            loadingElement.style.display = 'none';
            console.log(`✅ Hiding ${type} loading`);
        }
    }

    showError(message) {
        console.error('🚨 Displaying error:', message);
        
        const errorElement = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        
        if (errorElement && errorText) {
            errorText.textContent = message;
            errorElement.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                errorElement.style.display = 'none';
            }, 5000);
        } else {
            alert(message);
        }
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔧 Initializing embedded checkout system...');
    window.embeddedCheckout = new EmbeddedCheckout();
});

// Export for potential external use
export default EmbeddedCheckout;