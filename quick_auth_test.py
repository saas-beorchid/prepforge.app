#!/usr/bin/env python3
"""
Quick Authentication Test - Test full auth flow after logging fix
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_auth_flow():
    """Test the complete authentication flow"""
    
    session = requests.Session()
    
    try:
        # Step 1: Get signin page and extract CSRF token
        logger.info("Step 1: Getting signin page")
        signin_page = session.get('http://localhost:5000/signin')
        assert signin_page.status_code == 200, f"Signin page failed: {signin_page.status_code}"
        
        soup = BeautifulSoup(signin_page.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        assert csrf_input, "No CSRF token found"
        
        csrf_token = csrf_input['value']
        logger.info(f"CSRF token extracted: {csrf_token[:20]}...")
        
        # Step 2: Submit login credentials
        logger.info("Step 2: Submitting login credentials")
        login_data = {
            'email': 'abibasakor@gmail.com',
            'password': 'admin123456',
            'csrf_token': csrf_token
        }
        
        login_response = session.post(
            'http://localhost:5000/signin',
            data=login_data,
            allow_redirects=True
        )
        
        logger.info(f"Login response status: {login_response.status_code}")
        logger.info(f"Login response URL: {login_response.url}")
        
        # Step 3: Check for successful authentication
        if login_response.status_code == 200:
            if 'dashboard' in login_response.url:
                logger.info("✅ Redirect to dashboard successful")
                return True
            elif 'Welcome to PrepForge' in login_response.text:
                logger.info("✅ Dashboard content found in response")
                return True
            elif 'Invalid email or password' in login_response.text:
                logger.error("❌ Invalid credentials")
                return False
            else:
                logger.warning("⚠️  Uncertain login state")
                # Check if we can access dashboard directly
                dashboard_test = session.get('http://localhost:5000/dashboard')
                if dashboard_test.status_code == 200:
                    logger.info("✅ Dashboard accessible after login")
                    return True
                else:
                    logger.error(f"❌ Dashboard not accessible: {dashboard_test.status_code}")
                    return False
        else:
            logger.error(f"❌ Login failed with status: {login_response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Authentication test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Quick Authentication Test")
    logger.info("=" * 40)
    
    if test_full_auth_flow():
        logger.info("🎉 AUTHENTICATION TEST: PASSED")
        logger.info("✅ Complete authentication flow working")
    else:
        logger.error("🚨 AUTHENTICATION TEST: FAILED")
        logger.error("❌ Authentication flow needs additional fixes")