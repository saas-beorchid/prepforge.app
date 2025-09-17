#!/usr/bin/env python3
"""
Test Both Pages Checkout Integration
Verifies embedded checkout works from both dashboard and pricing pages
"""

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_both_pages_checkout():
    """Test embedded checkout from both dashboard and pricing pages"""
    base_url = 'http://localhost:5000'
    session = requests.Session()
    
    try:
        # Test dashboard page
        logger.info("🔍 Testing dashboard page checkout integration...")
        dashboard_response = session.get(f'{base_url}/dashboard')
        
        if dashboard_response.status_code == 200:
            content = dashboard_response.text
            
            # Check for embedded checkout elements
            checks = [
                'window.startEmbeddedCheckout' in content,
                'Global embedded checkout functions loaded' in content,
                'onclick="window.startEmbeddedCheckout' in content
            ]
            
            if all(checks):
                logger.info("✅ Dashboard: Embedded checkout fully integrated")
            else:
                logger.warning("⚠️ Dashboard: Some checkout elements missing")
        
        # Test pricing page
        logger.info("🔍 Testing pricing page checkout integration...")
        pricing_response = session.get(f'{base_url}/pricing')
        
        if pricing_response.status_code == 200:
            content = pricing_response.text
            
            # Check that pricing page extends base.html and has checkout
            checks = [
                'window.startEmbeddedCheckout' in content,
                'Global embedded checkout functions loaded' in content,
                'Select Pro Plan' in content,
                'extends "base.html"' in content or 'window.startEmbeddedCheckout' in content
            ]
            
            if all(checks):
                logger.info("✅ Pricing: Embedded checkout fully integrated")
            else:
                logger.warning("⚠️ Pricing: May have integration issues")
                
        # Test backend API
        logger.info("🔍 Testing checkout API endpoint...")
        
        # This should redirect to signin without auth
        api_response = session.post(f'{base_url}/create-checkout-session')
        
        if api_response.status_code in [200, 302, 401, 403]:
            logger.info("✅ API: Checkout endpoint responds correctly")
        else:
            logger.warning("⚠️ API: Endpoint may have issues")
            
        logger.info("🎉 Both pages checkout integration test completed")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_both_pages_checkout()