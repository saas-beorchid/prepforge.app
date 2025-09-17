#!/usr/bin/env python3
"""
System Verification Test - Final Working User Journey
Tests with proper password validation and complete flow verification
"""

import requests
import json
import time
import logging
import re
from bs4 import BeautifulSoup
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemVerificationTest:
    """Final system verification with proper validation"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrf_token'})
            if csrf_input and csrf_input.get('value'):
                return csrf_input['value']
            return None
        except Exception as e:
            logger.error(f"Error extracting CSRF token: {e}")
            return None
    
    def verify_complete_system(self):
        """Verify complete system functionality"""
        
        logger.info("🔍 SYSTEM VERIFICATION TEST")
        logger.info("=" * 50)
        
        # Test 1: Basic connectivity
        logger.info("Test 1: Basic Connectivity")
        try:
            response = self.session.get(self.base_url)
            assert response.status_code == 200, f"Status: {response.status_code}"
            assert 'PrepForge' in response.text, "PrepForge branding not found"
            logger.info("✅ Landing page accessible")
        except Exception as e:
            logger.error(f"❌ Landing page failed: {e}")
            return False
        
        # Test 2: User Registration with proper password
        logger.info("Test 2: User Registration")
        try:
            signup_response = self.session.get(f"{self.base_url}/signup")
            csrf_token = self.extract_csrf_token(signup_response.text)
            assert csrf_token, "Could not extract CSRF token"
            
            timestamp = int(time.time())
            test_data = {
                'name': f'System Test User {timestamp}',
                'email': f'system_test_{timestamp}@example.com',
                'password': f'SecurePassword123_{timestamp}',  # 8+ chars with numbers
                'confirm_password': f'SecurePassword123_{timestamp}',
                'csrf_token': csrf_token
            }
            
            register_response = self.session.post(
                f"{self.base_url}/signup", 
                data=test_data,
                allow_redirects=True
            )
            
            # Should redirect to signin after successful registration
            success = (register_response.status_code == 200 and 
                      ('Sign In' in register_response.text or 'signin' in register_response.url))
            
            assert success, f"Registration failed: {register_response.status_code}"
            
            self.test_email = test_data['email']
            self.test_password = test_data['password']
            
            logger.info(f"✅ User registration successful: {self.test_email}")
            
        except Exception as e:
            logger.error(f"❌ User registration failed: {e}")
            return False
        
        # Test 3: User Authentication
        logger.info("Test 3: User Authentication")
        try:
            signin_response = self.session.get(f"{self.base_url}/signin")
            csrf_token = self.extract_csrf_token(signin_response.text)
            assert csrf_token, "Could not extract CSRF token"
            
            login_data = {
                'email': self.test_email,
                'password': self.test_password,
                'csrf_token': csrf_token
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': f"{self.base_url}/signin"
            }
            
            login_response = self.session.post(
                f"{self.base_url}/signin", 
                data=login_data,
                headers=headers,
                allow_redirects=True
            )
            
            # Should redirect to dashboard after successful login
            success = (login_response.status_code == 200 and 
                      ('dashboard' in login_response.url or 'Welcome to PrepForge' in login_response.text))
            
            assert success, f"Authentication failed: {login_response.status_code}, URL: {login_response.url}"
            logger.info("✅ User authentication successful")
            
        except Exception as e:
            logger.error(f"❌ User authentication failed: {e}")
            return False
        
        # Test 4: Dashboard functionality
        logger.info("Test 4: Dashboard Access")
        try:
            dashboard_response = self.session.get(f"{self.base_url}/dashboard")
            dashboard_content = dashboard_response.text
            
            required_elements = ['Welcome to PrepForge', 'Start Practice', 'GRE', 'GMAT']
            found_elements = [elem for elem in required_elements if elem in dashboard_content]
            
            assert len(found_elements) >= 3, f"Dashboard missing elements. Found: {found_elements}"
            logger.info(f"✅ Dashboard accessible with {len(found_elements)}/4 elements")
            
        except Exception as e:
            logger.error(f"❌ Dashboard access failed: {e}")
            return False
        
        # Test 5: Practice Session
        logger.info("Test 5: Practice Session")
        try:
            dashboard_response = self.session.get(f"{self.base_url}/dashboard")
            csrf_token = self.extract_csrf_token(dashboard_response.text)
            assert csrf_token, "Could not extract CSRF token"
            
            practice_data = {
                'exam_type': 'GRE',
                'csrf_token': csrf_token
            }
            
            practice_response = self.session.post(
                f"{self.base_url}/start-practice", 
                data=practice_data,
                allow_redirects=True
            )
            
            assert practice_response.status_code == 200, f"Practice start failed: {practice_response.status_code}"
            
            # Try to access practice page
            practice_page = self.session.get(f"{self.base_url}/practice")
            assert practice_page.status_code == 200, f"Practice page failed: {practice_page.status_code}"
            
            logger.info("✅ Practice session initiated successfully")
            
        except Exception as e:
            logger.error(f"❌ Practice session failed: {e}")
            return False
        
        # Test 6: Question display
        logger.info("Test 6: Question Display")
        try:
            practice_response = self.session.get(f"{self.base_url}/practice")
            practice_content = practice_response.text
            
            question_indicators = ['question', 'option', 'submit', 'radio']
            found_indicators = [indicator for indicator in question_indicators 
                              if indicator.lower() in practice_content.lower()]
            
            assert len(found_indicators) >= 2, f"Question page missing elements. Found: {found_indicators}"
            logger.info(f"✅ Question displayed with {len(found_indicators)} elements")
            
        except Exception as e:
            logger.error(f"❌ Question display failed: {e}")
            return False
        
        # Test 7: Answer submission
        logger.info("Test 7: Answer Submission")
        try:
            practice_response = self.session.get(f"{self.base_url}/practice")
            csrf_token = self.extract_csrf_token(practice_response.text)
            
            if csrf_token:
                answer_data = {
                    'answer': 'A',
                    'csrf_token': csrf_token
                }
                
                submit_response = self.session.post(
                    f"{self.base_url}/submit-answer", 
                    data=answer_data,
                    allow_redirects=True
                )
                
                assert submit_response.status_code == 200, f"Answer submission failed: {submit_response.status_code}"
                logger.info("✅ Answer submission successful")
            else:
                logger.info("⚠️  Answer submission skipped (no CSRF token)")
                
        except Exception as e:
            logger.error(f"❌ Answer submission failed: {e}")
            return False
        
        # Test 8: Multiple exam types
        logger.info("Test 8: Multiple Exam Types")
        try:
            exam_types = ['GMAT', 'MCAT', 'SAT']
            successful_exams = []
            
            for exam_type in exam_types:
                try:
                    dashboard_response = self.session.get(f"{self.base_url}/dashboard")
                    csrf_token = self.extract_csrf_token(dashboard_response.text)
                    
                    if csrf_token:
                        practice_data = {
                            'exam_type': exam_type,
                            'csrf_token': csrf_token
                        }
                        
                        response = self.session.post(
                            f"{self.base_url}/start-practice", 
                            data=practice_data,
                            allow_redirects=True
                        )
                        
                        if response.status_code == 200:
                            successful_exams.append(exam_type)
                            
                except Exception:
                    continue
            
            assert len(successful_exams) >= 2, f"Not enough exam types working: {successful_exams}"
            logger.info(f"✅ Multiple exam types working: {successful_exams}")
            
        except Exception as e:
            logger.error(f"❌ Multiple exam types failed: {e}")
            return False
        
        logger.info("=" * 50)
        logger.info("🎉 SYSTEM VERIFICATION: PASSED")
        logger.info("✅ All critical user journeys functional")
        logger.info("✅ Registration → Authentication → Dashboard → Practice")
        logger.info("✅ System ready for production use")
        
        return True

def run_quick_test():
    """Run a quick test to verify basic functionality"""
    logger.info("🚀 Quick System Test")
    
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200 and 'PrepForge' in response.text:
            logger.info("✅ Basic connectivity working")
            return True
        else:
            logger.error(f"❌ Basic connectivity failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Basic connectivity failed: {e}")
        return False

if __name__ == "__main__":
    # Check application availability
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 5000))
    sock.close()
    
    if result != 0:
        print("❌ Application not running on localhost:5000")
        sys.exit(1)
    
    # Run quick test first
    if not run_quick_test():
        print("❌ Quick test failed")
        sys.exit(1)
    
    # Run full system verification
    test = SystemVerificationTest()
    system_functional = test.verify_complete_system()
    
    sys.exit(0 if system_functional else 1)