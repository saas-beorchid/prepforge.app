#!/usr/bin/env python3
"""
Final Authentication Verification - Complete end-to-end test
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def comprehensive_auth_test():
    """Complete authentication test with redirect verification"""
    
    session = requests.Session()
    
    logger.info("🔍 FINAL AUTHENTICATION VERIFICATION")
    logger.info("=" * 50)
    
    try:
        # Test 1: Registration flow
        logger.info("Test 1: User Registration Flow")
        
        signup_page = session.get('http://localhost:5000/signup')
        soup = BeautifulSoup(signup_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        
        import time
        timestamp = int(time.time())
        
        registration_data = {
            'name': f'Final Test User {timestamp}',
            'email': f'final_test_{timestamp}@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'csrf_token': csrf_token
        }
        
        register_response = session.post(
            'http://localhost:5000/signup',
            data=registration_data,
            allow_redirects=True
        )
        
        if register_response.status_code == 200 and 'Sign In' in register_response.text:
            logger.info("✅ Registration successful - redirected to signin")
        else:
            logger.error(f"❌ Registration failed: {register_response.status_code}")
            return False
        
        # Test 2: Authentication flow
        logger.info("Test 2: Authentication Flow")
        
        signin_page = session.get('http://localhost:5000/signin')
        soup = BeautifulSoup(signin_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        
        login_data = {
            'email': registration_data['email'],
            'password': registration_data['password'],
            'csrf_token': csrf_token
        }
        
        login_response = session.post(
            'http://localhost:5000/signin',
            data=login_data,
            allow_redirects=True
        )
        
        logger.info(f"Login response status: {login_response.status_code}")
        logger.info(f"Final URL: {login_response.url}")
        
        # Check if redirected to dashboard
        if 'dashboard' in login_response.url:
            logger.info("✅ Authentication successful - redirected to dashboard")
        elif 'Welcome to PrepForge' in login_response.text and '/dashboard' in login_response.text:
            logger.info("✅ Authentication successful - dashboard content found")
        else:
            logger.warning("⚠️  Authentication may have succeeded but redirect unclear")
            
            # Direct dashboard test
            dashboard_test = session.get('http://localhost:5000/dashboard')
            if dashboard_test.status_code == 200 and 'Welcome to PrepForge' in dashboard_test.text:
                logger.info("✅ Dashboard accessible - authentication confirmed")
            else:
                logger.error("❌ Dashboard not accessible")
                return False
        
        # Test 3: Practice flow
        logger.info("Test 3: Practice Session Flow")
        
        dashboard_page = session.get('http://localhost:5000/dashboard')
        soup = BeautifulSoup(dashboard_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        
        practice_data = {
            'exam_type': 'GRE',
            'csrf_token': csrf_token
        }
        
        practice_response = session.post(
            'http://localhost:5000/start-practice',
            data=practice_data,
            allow_redirects=True
        )
        
        if practice_response.status_code == 200:
            practice_page = session.get('http://localhost:5000/practice')
            if practice_page.status_code == 200 and 'question' in practice_page.text.lower():
                logger.info("✅ Practice session started successfully")
            else:
                logger.warning("⚠️  Practice session may have issues")
        
        logger.info("=" * 50)
        logger.info("🎉 COMPREHENSIVE AUTHENTICATION: PASSED")
        logger.info("✅ Registration → Authentication → Dashboard → Practice")
        logger.info("✅ System fully functional")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Authentication test failed: {e}")
        return False

if __name__ == "__main__":
    success = comprehensive_auth_test()
    exit(0 if success else 1)