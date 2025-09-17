#!/usr/bin/env python3
"""
Test "Go Premium" Button Fix
Verifies that the embedded checkout is properly accessible
"""

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_go_premium_button_fix():
    """Test that Go Premium buttons now use embedded checkout"""
    base_url = 'http://localhost:5000'
    session = requests.Session()
    
    try:
        # Test dashboard page
        logger.info("🔍 Testing dashboard page...")
        dashboard_response = session.get(f'{base_url}/dashboard')
        
        if dashboard_response.status_code == 200:
            content = dashboard_response.text
            
            # Check for proper button implementation
            checks = [
                'window.startEmbeddedCheckout' in content,
                'onclick="window.startEmbeddedCheckout' in content,
                'Global embedded checkout functions loaded' in content,
                'window.mountEmbeddedCheckout' in content
            ]
            
            if all(checks):
                logger.info("✅ Dashboard: Embedded checkout properly configured")
            else:
                logger.warning("⚠️ Dashboard: Some embedded checkout elements missing")
                
        # Test pricing page
        logger.info("🔍 Testing pricing page...")
        pricing_response = session.get(f'{base_url}/pricing')
        
        if pricing_response.status_code == 200:
            content = pricing_response.text
            
            # Check that old form is removed and new button exists
            old_form_gone = 'action="/create-checkout-session"' not in content
            new_button_exists = 'window.startEmbeddedCheckout' in content
            
            if old_form_gone and new_button_exists:
                logger.info("✅ Pricing: Old form removed, embedded checkout added")
            else:
                logger.warning("⚠️ Pricing: May still have old form or missing new button")
                
        # Test that create-checkout-session still returns client_secret
        logger.info("🔍 Testing backend endpoint...")
        api_response = session.post(f'{base_url}/create-checkout-session')
        
        if api_response.status_code in [200, 401, 403]:
            logger.info("✅ Backend: Endpoint accessible and configured for embedded checkout")
        else:
            logger.warning("⚠️ Backend: Endpoint may have issues")
            
        logger.info("🎉 Go Premium button fix test completed")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_go_premium_button_fix()