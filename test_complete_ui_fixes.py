#!/usr/bin/env python3
"""
Complete UI Fixes Test Suite
Tests loading feedback, hamburger menu, mobile responsiveness, and Stripe integration
"""

import requests
import time
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteUIFixesTest:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'loading_feedback': False,
            'hamburger_menu': False,
            'mobile_responsive': False,
            'stripe_integration': False,
            'explanation_system': False,
            'performance': False,
            'errors': []
        }
    
    def test_loading_feedback_implementation(self):
        """Test that loading spinners are properly implemented with debug logs"""
        logger.info("🔍 Testing loading feedback implementation...")
        
        try:
            # Check for loading spinner elements in quiz.html
            response = self.session.get(f'{self.base_url}/quiz')
            
            if response.status_code == 200:
                content = response.text
                
                # Check for loading spinner elements
                spinner_checks = [
                    'id="loading-spinner"' in content,
                    'id="answer-loading"' in content,
                    'id="payment-loading"' in content,
                    'class="spinner"' in content,
                    'class="loading-text"' in content,
                    'id="loading-timer"' in content
                ]
                
                # Check JavaScript functionality
                js_response = self.session.get(f'{self.base_url}/static/js/quiz.js')
                if js_response.status_code == 200:
                    js_content = js_response.text
                    
                    js_checks = [
                        'showLoading(' in js_content,
                        'hideLoading(' in js_content,
                        'startLoadingTimer(' in js_content,
                        'stopLoadingTimer(' in js_content,
                        'console.log(' in js_content and 'Showing loading' in js_content,
                        'Loading taking longer than expected' in js_content
                    ]
                    
                    if all(spinner_checks + js_checks):
                        self.results['loading_feedback'] = True
                        logger.info("✅ Loading feedback: PASSED")
                    else:
                        logger.warning("⚠️ Loading feedback: Some features missing")
                        missing = [f"Spinner check {i}" for i, check in enumerate(spinner_checks) if not check]
                        missing += [f"JS check {i}" for i, check in enumerate(js_checks) if not check]
                        self.results['errors'].append(f"Loading feedback missing: {missing}")
                else:
                    logger.error("❌ Could not load quiz.js")
                    
        except Exception as e:
            logger.error(f"❌ Loading feedback test failed: {e}")
            self.results['errors'].append(f"Loading feedback error: {e}")
    
    def test_hamburger_menu_functionality(self):
        """Test hamburger menu with proper mobile event binding"""
        logger.info("🔍 Testing hamburger menu functionality...")
        
        try:
            # Check base template for hamburger menu
            response = self.session.get(f'{self.base_url}/')
            
            if response.status_code == 200:
                content = response.text
                
                menu_checks = [
                    'mobile-menu-toggle' in content,
                    'main-nav' in content,
                    '<span></span>' in content,  # Hamburger lines
                    'aria-expanded' in content,
                    'console.log(' in content and 'Hamburger menu' in content,
                    'initializeHamburgerMenu' in content,
                    '@media (max-width: 768px)' in content,
                    'click' in content and 'touchstart' in content  # Enhanced event binding
                ]
                
                if all(menu_checks):
                    self.results['hamburger_menu'] = True
                    logger.info("✅ Hamburger menu: PASSED")
                else:
                    logger.warning("⚠️ Hamburger menu: Some features missing")
                    self.results['errors'].append("Hamburger menu incomplete")
                    
        except Exception as e:
            logger.error(f"❌ Hamburger menu test failed: {e}")
            self.results['errors'].append(f"Hamburger menu error: {e}")
    
    def test_mobile_responsiveness(self):
        """Test mobile-first design with 360px optimization"""
        logger.info("🔍 Testing mobile responsiveness...")
        
        try:
            # Check CSS for mobile optimizations
            response = self.session.get(f'{self.base_url}/static/css/style.css')
            
            if response.status_code == 200:
                css_content = response.text
                
                mobile_checks = [
                    '@media (max-width: 360px)' in css_content,
                    'grid-template-columns: 1fr !important' in css_content,
                    'flex-direction: column !important' in css_content,
                    'width: 100% !important' in css_content,
                    'padding: 0.5rem !important' in css_content,
                    'font-size: 0.8rem !important' in css_content,
                    'max-height: 400px' in css_content,  # Mobile nav height
                    'z-index: 1000' in css_content  # Proper layering
                ]
                
                if all(mobile_checks):
                    self.results['mobile_responsive'] = True
                    logger.info("✅ Mobile responsiveness: PASSED")
                else:
                    logger.warning("⚠️ Mobile responsiveness: Some features missing")
                    self.results['errors'].append("Mobile CSS incomplete")
                    
        except Exception as e:
            logger.error(f"❌ Mobile responsiveness test failed: {e}")
            self.results['errors'].append(f"Mobile responsiveness error: {e}")
    
    def test_stripe_integration(self):
        """Test complete Stripe integration with proper logging"""
        logger.info("🔍 Testing Stripe integration...")
        
        try:
            # Check for Stripe CDN integration
            response = self.session.get(f'{self.base_url}/quiz')
            
            if response.status_code == 200:
                content = response.text
                
                stripe_checks = [
                    'stripe.com/v3' in content,  # Latest Stripe.js
                    'upgradeToPro' in content,
                    'create-checkout-session' in content,
                    'window.location.href' in content,  # Full page redirect
                    'checkout_url' in content,
                    'console.log(' in content and 'upgradeToPro started' in content,
                    'Processing payment...' in content
                ]
                
                # Test checkout endpoint exists
                checkout_response = self.session.post(f'{self.base_url}/create-checkout-session')
                endpoint_working = checkout_response.status_code in [200, 401, 403]  # Endpoint exists
                
                if all(stripe_checks) and endpoint_working:
                    self.results['stripe_integration'] = True
                    logger.info("✅ Stripe integration: PASSED")
                else:
                    logger.warning("⚠️ Stripe integration: Some features missing")
                    self.results['errors'].append("Stripe integration incomplete")
                    
        except Exception as e:
            logger.error(f"❌ Stripe integration test failed: {e}")
            self.results['errors'].append(f"Stripe integration error: {e}")
    
    def test_explanation_system(self):
        """Test collapsible explanation system"""
        logger.info("🔍 Testing explanation system...")
        
        try:
            response = self.session.get(f'{self.base_url}/quiz')
            
            if response.status_code == 200:
                content = response.text
                
                explanation_checks = [
                    'explanation-technical' in content,
                    'explanation-simple' in content,
                    'explanation-concepts' in content,
                    'toggleExplanation(' in content,
                    'explanation-header' in content,
                    'explanation-content' in content,
                    'collapsed' in content,
                    'expanded' in content,
                    'toggle-icon' in content
                ]
                
                if all(explanation_checks):
                    self.results['explanation_system'] = True
                    logger.info("✅ Explanation system: PASSED")
                else:
                    logger.warning("⚠️ Explanation system: Some features missing")
                    self.results['errors'].append("Explanation system incomplete")
                    
        except Exception as e:
            logger.error(f"❌ Explanation system test failed: {e}")
            self.results['errors'].append(f"Explanation system error: {e}")
    
    def test_performance_requirements(self):
        """Test <10s load time and <5s question generation"""
        logger.info("🔍 Testing performance requirements...")
        
        try:
            # Test page load times
            start_time = time.time()
            response = self.session.get(f'{self.base_url}/quiz')
            page_load_time = time.time() - start_time
            
            # Test API endpoint response time
            start_time = time.time()
            api_response = self.session.get(f'{self.base_url}/api/health', timeout=10)
            api_response_time = time.time() - start_time
            
            performance_ok = (
                page_load_time < 10.0 and
                api_response_time < 5.0 and
                response.status_code == 200
            )
            
            if performance_ok:
                self.results['performance'] = True
                logger.info(f"✅ Performance: PASSED (Page: {page_load_time:.2f}s, API: {api_response_time:.2f}s)")
            else:
                logger.warning(f"⚠️ Performance: FAILED (Page: {page_load_time:.2f}s, API: {api_response_time:.2f}s)")
                self.results['errors'].append(f"Performance issue - Page: {page_load_time:.2f}s")
                
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            self.results['errors'].append(f"Performance error: {e}")
    
    def run_complete_test_suite(self):
        """Run all UI fix tests"""
        logger.info("🚀 Starting Complete UI Fixes Test Suite")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # Run all tests
        self.test_loading_feedback_implementation()
        self.test_hamburger_menu_functionality()
        self.test_mobile_responsiveness()
        self.test_stripe_integration()
        self.test_explanation_system()
        self.test_performance_requirements()
        
        total_time = time.time() - start_time
        
        # Generate report
        logger.info("=" * 70)
        logger.info("📊 COMPLETE UI FIXES TEST RESULTS")
        logger.info("=" * 70)
        
        tests = [
            ("Loading Feedback", self.results['loading_feedback']),
            ("Hamburger Menu", self.results['hamburger_menu']),
            ("Mobile Responsive", self.results['mobile_responsive']),
            ("Stripe Integration", self.results['stripe_integration']),
            ("Explanation System", self.results['explanation_system']),
            ("Performance", self.results['performance'])
        ]
        
        passed_tests = sum(1 for _, passed in tests if passed)
        total_tests = len(tests)
        
        for test_name, passed in tests:
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"{test_name:<20}: {status}")
        
        logger.info("=" * 70)
        logger.info(f"📈 SUMMARY:")
        logger.info(f"   Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"   Total Time: {total_time:.2f}s")
        logger.info(f"   Errors: {len(self.results['errors'])}")
        
        if self.results['errors']:
            logger.info(f"🔍 ERROR DETAILS:")
            for i, error in enumerate(self.results['errors'], 1):
                logger.info(f"   {i}. {error}")
        
        # Overall status
        overall_success = passed_tests == total_tests and len(self.results['errors']) == 0
        
        if overall_success:
            logger.info("🎉 OVERALL STATUS: ALL UI FIXES COMPLETE - READY FOR TESTING")
        else:
            logger.info("⚠️ OVERALL STATUS: SOME FIXES NEED ATTENTION")
        
        logger.info("=" * 70)
        
        return self.results

if __name__ == "__main__":
    print("🔧 Complete UI Fixes Test Suite")
    print("Testing loading feedback, hamburger menu, mobile design, and Stripe integration")
    print()
    
    tester = CompleteUIFixesTest()
    results = tester.run_complete_test_suite()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'test_results_ui_fixes_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: test_results_ui_fixes_{timestamp}.json")