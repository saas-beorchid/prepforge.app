#!/usr/bin/env python3
"""
Enhanced Test Suite with Proper Authentication Flow
Tests all critical user journeys with session persistence
"""

import requests
import json
import time
import logging
from datetime import datetime
import sys
import os
from urllib.parse import urljoin
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedPrepForgeTestSuite:
    """Enhanced test suite with proper authentication and session management"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        self.test_credentials = None
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        if success:
            self.test_results['passed'] += 1
            logger.info(f"✅ {test_name}: PASSED {details}")
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {details}")
            logger.error(f"❌ {test_name}: FAILED {details}")
    
    def extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML content"""
        patterns = [
            r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"',
            r'<meta[^>]*name="csrf-token"[^>]*content="([^"]+)"',
            r'csrf_token["\']?\s*:\s*["\']([^"\']+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                return match.group(1)
        return None
    
    def test_basic_connectivity(self):
        """Test 1: Basic application connectivity"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            success = response.status_code == 200
            self.log_test("Basic Connectivity", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Basic Connectivity", False, str(e))
            return False
    
    def test_landing_page_content(self):
        """Test 2: Landing page essential content"""
        try:
            response = self.session.get(self.base_url)
            html = response.text
            
            essential_elements = [
                'PrepForge',
                'Start Free Trial',
                'GRE',
                'GMAT'
            ]
            
            missing = [elem for elem in essential_elements if elem not in html]
            success = len(missing) == 0
            details = f"Missing: {missing}" if missing else "All essential elements present"
            self.log_test("Landing Page Content", success, details)
            return success
        except Exception as e:
            self.log_test("Landing Page Content", False, str(e))
            return False
    
    def test_user_registration_complete_flow(self):
        """Test 3: Complete user registration flow"""
        try:
            # Step 1: Get signup page
            signup_response = self.session.get(f"{self.base_url}/signup")
            if signup_response.status_code != 200:
                self.log_test("User Registration", False, f"Signup page not accessible: {signup_response.status_code}")
                return False
            
            # Step 2: Extract CSRF token
            csrf_token = self.extract_csrf_token(signup_response.text)
            if not csrf_token:
                self.log_test("User Registration", False, "Could not extract CSRF token from signup page")
                return False
            
            # Step 3: Prepare test data
            timestamp = int(time.time())
            test_email = f"test_user_{timestamp}@example.com"
            test_password = f"SecurePass123_{timestamp}"
            
            registration_data = {
                'name': f'Test User {timestamp}',
                'email': test_email,
                'password': test_password,
                'confirm_password': test_password,
                'csrf_token': csrf_token
            }
            
            # Step 4: Submit registration
            register_response = self.session.post(
                f"{self.base_url}/signup", 
                data=registration_data,
                allow_redirects=True
            )
            
            # Step 5: Check if registration was successful
            success = (register_response.status_code == 200 and 
                      ('Sign In' in register_response.text or 'signin' in register_response.url))
            
            if success:
                self.test_credentials = {
                    'email': test_email,
                    'password': test_password,
                    'name': f'Test User {timestamp}'
                }
            
            self.log_test("User Registration", success, f"Email: {test_email}")
            return success
            
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False
    
    def test_user_authentication_flow(self):
        """Test 4: Complete user authentication flow"""
        if not self.test_credentials:
            self.log_test("User Authentication", False, "No test credentials available")
            return False
            
        try:
            # Step 1: Get signin page
            signin_response = self.session.get(f"{self.base_url}/signin")
            if signin_response.status_code != 200:
                self.log_test("User Authentication", False, f"Signin page not accessible: {signin_response.status_code}")
                return False
            
            # Step 2: Extract CSRF token
            csrf_token = self.extract_csrf_token(signin_response.text)
            if not csrf_token:
                self.log_test("User Authentication", False, "Could not extract CSRF token from signin page")
                return False
            
            # Step 3: Submit login credentials
            login_data = {
                'email': self.test_credentials['email'],
                'password': self.test_credentials['password'],
                'csrf_token': csrf_token
            }
            
            login_response = self.session.post(
                f"{self.base_url}/signin", 
                data=login_data,
                allow_redirects=True
            )
            
            # Step 4: Verify successful authentication
            success = (login_response.status_code == 200 and 
                      ('dashboard' in login_response.url or 'Dashboard' in login_response.text))
            
            self.log_test("User Authentication", success, f"Email: {self.test_credentials['email']}")
            return success
            
        except Exception as e:
            self.log_test("User Authentication", False, str(e))
            return False
    
    def test_authenticated_dashboard_access(self):
        """Test 5: Dashboard access with authentication"""
        try:
            response = self.session.get(f"{self.base_url}/dashboard")
            html = response.text
            
            if response.status_code != 200:
                self.log_test("Dashboard Access", False, f"Dashboard not accessible: {response.status_code}")
                return False
            
            # Check for dashboard-specific content
            dashboard_elements = [
                'Welcome to PrepForge',
                'Start Practice',
                'GRE',
                'GMAT',
                'MCAT'
            ]
            
            found_elements = [elem for elem in dashboard_elements if elem in html]
            success = len(found_elements) >= 4  # At least 4 out of 5 elements should be present
            
            details = f"Found {len(found_elements)}/{len(dashboard_elements)} elements: {found_elements}"
            self.log_test("Dashboard Access", success, details)
            return success
            
        except Exception as e:
            self.log_test("Dashboard Access", False, str(e))
            return False
    
    def test_practice_session_initialization(self):
        """Test 6: Practice session initialization"""
        try:
            # Step 1: Get dashboard to extract form data
            dashboard_response = self.session.get(f"{self.base_url}/dashboard")
            if dashboard_response.status_code != 200:
                self.log_test("Practice Session Init", False, "Dashboard not accessible")
                return False
            
            # Step 2: Extract CSRF token
            csrf_token = self.extract_csrf_token(dashboard_response.text)
            if not csrf_token:
                self.log_test("Practice Session Init", False, "Could not extract CSRF token")
                return False
            
            # Step 3: Start practice session
            practice_data = {
                'exam_type': 'GRE',
                'csrf_token': csrf_token
            }
            
            practice_response = self.session.post(
                f"{self.base_url}/start-practice", 
                data=practice_data,
                allow_redirects=True
            )
            
            # Step 4: Verify practice session started
            success = practice_response.status_code == 200
            if success:
                # Try accessing practice page
                practice_page = self.session.get(f"{self.base_url}/practice")
                success = practice_page.status_code == 200
            
            self.log_test("Practice Session Init", success, "Exam: GRE")
            return success
            
        except Exception as e:
            self.log_test("Practice Session Init", False, str(e))
            return False
    
    def test_question_display_and_interaction(self):
        """Test 7: Question display and interaction"""
        try:
            # Get practice page
            practice_response = self.session.get(f"{self.base_url}/practice")
            if practice_response.status_code != 200:
                self.log_test("Question Display", False, f"Practice page not accessible: {practice_response.status_code}")
                return False
            
            html = practice_response.text
            
            # Check for question elements
            question_indicators = [
                'question',
                'option',
                'answer',
                'submit',
                'radio',
                'choice'
            ]
            
            found_indicators = [indicator for indicator in question_indicators 
                              if indicator.lower() in html.lower()]
            
            success = len(found_indicators) >= 3
            details = f"Found indicators: {found_indicators}"
            self.log_test("Question Display", success, details)
            return success
            
        except Exception as e:
            self.log_test("Question Display", False, str(e))
            return False
    
    def test_answer_submission_flow(self):
        """Test 8: Complete answer submission flow"""
        try:
            # Step 1: Get practice page
            practice_response = self.session.get(f"{self.base_url}/practice")
            if practice_response.status_code != 200:
                self.log_test("Answer Submission", False, "Practice page not accessible")
                return False
            
            # Step 2: Extract form data
            html = practice_response.text
            csrf_token = self.extract_csrf_token(html)
            
            if not csrf_token:
                self.log_test("Answer Submission", False, "Could not extract CSRF token")
                return False
            
            # Step 3: Submit an answer
            answer_data = {
                'answer': 'A',  # Choose option A
                'csrf_token': csrf_token
            }
            
            submit_response = self.session.post(
                f"{self.base_url}/submit-answer", 
                data=answer_data,
                allow_redirects=True
            )
            
            # Step 4: Verify submission was processed
            success = submit_response.status_code == 200
            self.log_test("Answer Submission", success, "Selected option A")
            return success
            
        except Exception as e:
            self.log_test("Answer Submission", False, str(e))
            return False
    
    def test_multiple_exam_types_support(self):
        """Test 9: Multiple exam types support"""
        exam_types = ['GMAT', 'MCAT', 'SAT', 'USMLE_STEP_1']
        successful_exams = []
        
        for exam_type in exam_types:
            try:
                # Get fresh CSRF token
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
                        
            except Exception as e:
                logger.warning(f"Error testing {exam_type}: {e}")
        
        success = len(successful_exams) >= len(exam_types) // 2
        details = f"Working exams: {successful_exams}"
        self.log_test("Multiple Exam Types", success, details)
        return success
    
    def test_session_persistence(self):
        """Test 10: Session persistence across requests"""
        try:
            # Make multiple requests and ensure session persists
            responses = []
            
            for i in range(3):
                response = self.session.get(f"{self.base_url}/dashboard")
                responses.append(response.status_code)
                time.sleep(0.5)
            
            # All requests should be successful (200)
            success = all(status == 200 for status in responses)
            details = f"Response codes: {responses}"
            self.log_test("Session Persistence", success, details)
            return success
            
        except Exception as e:
            self.log_test("Session Persistence", False, str(e))
            return False
    
    def run_comprehensive_tests(self):
        """Run all tests in logical sequence"""
        logger.info("🚀 Starting Enhanced Comprehensive Test Suite")
        logger.info("=" * 60)
        
        # Test sequence designed to build upon previous tests
        test_sequence = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Landing Page Content", self.test_landing_page_content),
            ("User Registration", self.test_user_registration_complete_flow),
            ("User Authentication", self.test_user_authentication_flow),
            ("Dashboard Access", self.test_authenticated_dashboard_access),
            ("Practice Session Init", self.test_practice_session_initialization),
            ("Question Display", self.test_question_display_and_interaction),
            ("Answer Submission", self.test_answer_submission_flow),
            ("Multiple Exam Types", self.test_multiple_exam_types_support),
            ("Session Persistence", self.test_session_persistence)
        ]
        
        start_time = time.time()
        
        for test_name, test_function in test_sequence:
            try:
                logger.info(f"Running: {test_name}")
                test_function()
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                logger.error(f"Critical error in {test_name}: {e}")
                self.log_test(test_name, False, f"Critical error: {str(e)}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate comprehensive report
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📊 ENHANCED TEST SUITE RESULTS")
        logger.info(f"✅ Tests Passed: {self.test_results['passed']}")
        logger.info(f"❌ Tests Failed: {self.test_results['failed']}")
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
        
        if self.test_results['failed'] > 0:
            logger.error("🔍 FAILED TESTS:")
            for error in self.test_results['errors']:
                logger.error(f"   • {error}")
        
        # Determine overall success
        critical_tests_passed = (
            self.test_results['passed'] >= 7 and  # At least 7 out of 10 tests pass
            success_rate >= 70  # At least 70% success rate
        )
        
        if critical_tests_passed:
            logger.info("🎉 OVERALL ASSESSMENT: SYSTEM FUNCTIONAL")
        else:
            logger.warning("🚨 OVERALL ASSESSMENT: SYSTEM NEEDS FIXES")
        
        return critical_tests_passed

if __name__ == "__main__":
    # Check application availability
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 5000))
    sock.close()
    
    if result != 0:
        print("❌ Application not running on localhost:5000")
        print("Please start the application first")
        sys.exit(1)
    
    # Run enhanced test suite
    test_suite = EnhancedPrepForgeTestSuite()
    system_functional = test_suite.run_comprehensive_tests()
    
    sys.exit(0 if system_functional else 1)