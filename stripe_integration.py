#!/usr/bin/env python3
"""
Stripe Integration for PrepForge Pro Upgrades
Handles checkout session creation and webhook processing
"""

import os
import stripe
import logging
from flask import Blueprint, request, jsonify, current_app, session
from flask_login import login_required, current_user
from models import db, User
import hmac
import hashlib

# Initialize Stripe with secret key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Create Flask blueprint
stripe_bp = Blueprint('stripe', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@stripe_bp.route('/api/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session for Pro upgrade"""
    try:
        # Get domain for success/cancel URLs
        domain = request.host_url.rstrip('/')
        
        # Get price ID from environment (you'll need to set this)
        price_id = os.environ.get('STRIPE_PRICE_ID', 'price_1234567890')  # Default for testing
        
        logger.info(f"Creating checkout session for user {current_user.id}")
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',  # For recurring billing
            success_url=f'{domain}/dashboard?payment=success',
            cancel_url=f'{domain}/dashboard?payment=cancelled',
            client_reference_id=str(current_user.id),  # Link to our user
            customer_email=current_user.email,
            metadata={
                'user_id': current_user.id,
                'upgrade_type': 'pro'
            }
        )
        
        logger.info(f"Checkout session created: {checkout_session.id}")
        
        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Payment system error. Please try again.',
            'details': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error creating checkout session: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }), 500

@stripe_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.environ.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        # Verify webhook signature if secret is provided
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            # For development/testing without webhook secret
            event = stripe.Event.construct_from(
                request.get_json(), stripe.api_key
            )
            
        logger.info(f"Received Stripe webhook: {event['type']}")
        
        # Handle checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session_data = event['data']['object']
            
            # Get user ID from client_reference_id
            user_id = session_data.get('client_reference_id')
            if not user_id:
                user_id = session_data.get('metadata', {}).get('user_id')
            
            if user_id:
                # Update user subscription to pro
                user = User.query.get(int(user_id))
                if user:
                    user.subscription_plan = 'pro'
                    db.session.commit()
                    
                    logger.info(f"User {user_id} upgraded to Pro successfully")
                    
                    return jsonify({'success': True}), 200
                else:
                    logger.error(f"User {user_id} not found for Pro upgrade")
                    return jsonify({'error': 'User not found'}), 404
            else:
                logger.error("No user ID found in checkout session")
                return jsonify({'error': 'No user ID in session'}), 400
                
        # Handle other event types if needed
        elif event['type'] == 'customer.subscription.deleted':
            # Handle subscription cancellation
            session_data = event['data']['object']
            customer_id = session_data.get('customer')
            
            # You could implement downgrade logic here
            logger.info(f"Subscription cancelled for customer {customer_id}")
            
        return jsonify({'success': True}), 200
        
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid Stripe signature: {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 400
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@stripe_bp.route('/api/subscription-status', methods=['GET'])
@login_required
def get_subscription_status():
    """Get current user's subscription status"""
    try:
        return jsonify({
            'success': True,
            'subscription_plan': current_user.subscription_plan,
            'is_pro': current_user.subscription_plan == 'pro'
        })
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Could not retrieve subscription status'
        }), 500

def register_stripe_routes(app):
    """Register Stripe routes with the Flask app"""
    app.register_blueprint(stripe_bp)
    logger.info("Stripe integration routes registered")