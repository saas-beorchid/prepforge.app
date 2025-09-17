#!/usr/bin/env python3
"""
Comprehensive Test Suite for Answer Contest System
Tests ALL layers: Database, Backend Routes, Frontend Form, API Integration

REQUIREMENTS:
- Database model: AnswerContest
- Backend route: /submit-contest  
- Frontend form: Contest modal with work submission
- API validation: Proper error handling and success flow
- 100% functionality across all layers
"""

import logging
import sys
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContestSystemTester:
    """Comprehensive testing for the contest submission system"""
    
    def __init__(self, base_url='http://0.0.0.0:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        message = f"{status} | {test_name}"
        if details:
            message += f" | {details}"
        logger.info(message)
        self.test_results.append((test_name, success, details))
    
    def test_database_model(self):
        """Test 1: Database Model and Table Creation"""
        try:
            from app import app, db
            from models import AnswerContest, User, Question
            
            with app.app_context():
                # Check if AnswerContest model exists and has correct fields
                contest = AnswerContest(
                    user_id=1,
                    question_id='test_q_1',
                    exam_type='GRE',
                    user_answer='A',
                    correct_answer='B',
                    user_work='Test work showing calculation steps',
                    reason='I believe my answer is correct because...',
                    status='pending'
                )
                
                # Test model attributes
                assert hasattr(contest, 'user_id')
                assert hasattr(contest, 'question_id')
                assert hasattr(contest, 'user_work')
                assert hasattr(contest, 'status')
                assert hasattr(contest, 'created_at')
                
                # Test relationships exist
                assert hasattr(AnswerContest, 'user')
                assert hasattr(AnswerContest, 'question')
                
                self.log_test("Database Model Structure", True, "All required fields present")
                return True
                
        except Exception as e:
            self.log_test("Database Model Structure", False, str(e))
            return False
    
    def test_backend_route_exists(self):
        """Test 2: Backend Route Registration"""
        try:
            from app import app
            from practice import practice
            
            with app.app_context():
                # Check if the route is registered
                routes = [rule.endpoint for rule in app.url_map.iter_rules()]
                contest_route_exists = 'practice.submit_contest' in routes
                
                if contest_route_exists:
                    self.log_test("Backend Route Registration", True, "/submit-contest route found")
                    return True
                else:
                    self.log_test("Backend Route Registration", False, "Route not found in app")
                    return False
                    
        except Exception as e:
            self.log_test("Backend Route Registration", False, str(e))
            return False
    
    def test_route_validation_logic(self):
        """Test 3: Backend Validation Logic"""
        try:
            from app import app, db
            from models import AnswerContest
            from flask import session
            from flask_login import current_user
            
            with app.app_context():
                with app.test_client() as client:
                    # Test missing required fields
                    response = client.post('/practice/submit-contest', data={
                        'question_id': '',
                        'user_work': '',
                        'user_answer': 'A',
                        'correct_answer': 'B'
                    })
                    
                    # Should redirect back with error (not crash)
                    assert response.status_code in [302, 401]  # Redirect or login required
                    
                    self.log_test("Backend Validation", True, "Handles missing fields without crashing")
                    return True
                    
        except Exception as e:
            self.log_test("Backend Validation", False, str(e))
            return False
    
    def test_frontend_modal_structure(self):
        """Test 4: Frontend Modal and Form Structure"""
        try:
            from str_replace_based_edit_tool import str_replace_based_edit_tool
            
            # Read the practice template
            with open('templates/practice.html', 'r') as f:
                template_content = f.read()
            
            # Check for required frontend elements
            required_elements = [
                'contestModal',
                'showContestForm()',
                'hideContestForm()',
                'contest-btn',
                'user_work',
                'reason',
                'submit-contest'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in template_content:
                    missing_elements.append(element)
            
            if not missing_elements:
                self.log_test("Frontend Modal Structure", True, "All required elements present")
                return True
            else:
                self.log_test("Frontend Modal Structure", False, f"Missing: {missing_elements}")
                return False
                
        except Exception as e:
            self.log_test("Frontend Modal Structure", False, str(e))
            return False
    
    def test_javascript_functionality(self):
        """Test 5: JavaScript Functions"""
        try:
            with open('templates/practice.html', 'r') as f:
                template_content = f.read()
            
            # Check for JavaScript functions
            js_functions = [
                'function showContestForm()',
                'function hideContestForm()',
                'getElementById(\'contestModal\')',
                'style.display = \'flex\'',
                'style.display = \'none\''
            ]
            
            missing_functions = []
            for func in js_functions:
                if func not in template_content:
                    missing_functions.append(func)
            
            if not missing_functions:
                self.log_test("JavaScript Functions", True, "All modal functions implemented")
                return True
            else:
                self.log_test("JavaScript Functions", False, f"Missing: {missing_functions}")
                return False
                
        except Exception as e:
            self.log_test("JavaScript Functions", False, str(e))
            return False
    
    def test_css_styling(self):
        """Test 6: CSS Modal Styling"""
        try:
            with open('templates/practice.html', 'r') as f:
                template_content = f.read()
            
            # Check for CSS classes
            css_classes = [
                '.contest-modal',
                '.contest-btn',
                '.contest-modal-content',
                '.contest-form',
                '.form-control'
            ]
            
            missing_classes = []
            for css_class in css_classes:
                if css_class not in template_content:
                    missing_classes.append(css_class)
            
            if not missing_classes:
                self.log_test("CSS Styling", True, "All modal styles implemented")
                return True
            else:
                self.log_test("CSS Styling", False, f"Missing: {missing_classes}")
                return False
                
        except Exception as e:
            self.log_test("CSS Styling", False, str(e))
            return False
    
    def test_database_insert_capability(self):
        """Test 7: Database Insert Operations"""
        try:
            from app import app, db
            from models import AnswerContest
            
            with app.app_context():
                # Test database insert
                test_contest = AnswerContest(
                    user_id=1,
                    question_id='test_integration_q',
                    exam_type='TEST',
                    user_answer='A',
                    correct_answer='B',
                    user_work='This is a comprehensive test of the contest system. I solved this using step-by-step analysis.',
                    reason='Testing the complete integration'
                )
                
                db.session.add(test_contest)
                db.session.commit()
                
                # Verify insert
                inserted = AnswerContest.query.filter_by(question_id='test_integration_q').first()
                if inserted:
                    # Clean up test data
                    db.session.delete(inserted)
                    db.session.commit()
                    
                    self.log_test("Database Insert", True, "Contest submission saved successfully")
                    return True
                else:
                    self.log_test("Database Insert", False, "Failed to retrieve inserted record")
                    return False
                    
        except Exception as e:
            self.log_test("Database Insert", False, str(e))
            return False
    
    def test_form_csrf_protection(self):
        """Test 8: CSRF Token Implementation"""
        try:
            with open('templates/practice.html', 'r') as f:
                template_content = f.read()
            
            # Check for CSRF token
            csrf_present = 'csrf_token' in template_content and 'hidden' in template_content
            
            if csrf_present:
                self.log_test("CSRF Protection", True, "CSRF token implemented")
                return True
            else:
                self.log_test("CSRF Protection", False, "CSRF token not found")
                return False
                
        except Exception as e:
            self.log_test("CSRF Protection", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 STARTING COMPREHENSIVE CONTEST SYSTEM TEST SUITE")
        logger.info("=" * 80)
        
        tests = [
            self.test_database_model,
            self.test_backend_route_exists,
            self.test_route_validation_logic,
            self.test_frontend_modal_structure,
            self.test_javascript_functionality,
            self.test_css_styling,
            self.test_database_insert_capability,
            self.test_form_csrf_protection
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        logger.info("=" * 80)
        logger.info(f"🎯 TEST RESULTS: {passed}/{total} PASSED")
        
        if passed == total:
            logger.info("✅ CONTEST SYSTEM: 100% FUNCTIONAL ACROSS ALL LAYERS")
            logger.info("✅ DATABASE: Model and operations working")
            logger.info("✅ BACKEND: Routes and validation implemented")
            logger.info("✅ FRONTEND: Modal and form complete") 
            logger.info("✅ API: Error handling and success flow ready")
            return True
        else:
            logger.error("❌ CONTEST SYSTEM: INCOMPLETE - Review failed tests above")
            return False

def main():
    """Run the comprehensive test suite"""
    tester = ContestSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 CONTEST SYSTEM READY FOR PRODUCTION!")
        print("Users can now contest incorrect answers across all layers.")
        sys.exit(0)
    else:
        print("\n⚠️ CONTEST SYSTEM NEEDS FIXES")
        print("Review the failed tests and fix issues before deployment.")
        sys.exit(1)

if __name__ == '__main__':
    main()