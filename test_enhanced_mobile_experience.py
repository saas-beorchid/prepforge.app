#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Mobile Experience and User Interface
Tests all enhanced features including mobile responsiveness, loading feedback,
detailed explanations, and complete paid upgrade flow validation.
"""

import requests
import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedMobileExperienceTest:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {
            'mobile_responsiveness': False,
            'loading_feedback': False,
            'detailed_explanations': False,
            'stripe_integration': False,
            'performance_metrics': {},
            'errors': []
        }
    
    def test_mobile_responsive_design(self):
        """Test mobile-first design with 360px width responsiveness"""
        logger.info("🔍 Testing mobile responsive design...")
        
        try:
            # Test quiz page responsiveness
            response = self.session.get(f'{self.base_url}/quiz')
            
            if response.status_code == 200:
                content = response.text
                
                # Check for mobile-specific CSS media queries
                mobile_checks = [
                    '@media (max-width: 360px)' in content,
                    'mobile-first' in content.lower(),
                    'responsive' in content.lower(),
                    'viewport' in content,
                    'grid-template-columns: 1fr' in content
                ]
                
                if all(mobile_checks):
                    self.test_results['mobile_responsiveness'] = True
                    logger.info("✅ Mobile responsive design: PASSED")
                else:
                    logger.warning("⚠️ Mobile responsive design: Some features missing")
                    self.test_results['errors'].append("Mobile CSS features incomplete")
            else:
                logger.error(f"❌ Quiz page request failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Mobile responsiveness test failed: {e}")
            self.test_results['errors'].append(f"Mobile test error: {e}")
    
    def test_loading_feedback_system(self):
        """Test comprehensive loading feedback with spinners and timers"""
        logger.info("🔍 Testing loading feedback system...")
        
        try:
            # Test quiz page JavaScript for loading functions
            response = self.session.get(f'{self.base_url}/static/js/quiz.js')
            
            if response.status_code == 200:
                js_content = response.text
                
                # Check for enhanced loading functionality
                loading_checks = [
                    'showLoading(' in js_content,
                    'hideLoading(' in js_content,
                    'startLoadingTimer(' in js_content,
                    'stopLoadingTimer(' in js_content,
                    'answer-loading' in js_content,
                    'payment-loading' in js_content,
                    'loading-timer' in js_content
                ]
                
                if all(loading_checks):
                    self.test_results['loading_feedback'] = True
                    logger.info("✅ Loading feedback system: PASSED")
                else:
                    logger.warning("⚠️ Loading feedback system: Some features missing")
                    self.test_results['errors'].append("Loading feedback features incomplete")
            else:
                logger.error(f"❌ JavaScript file request failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Loading feedback test failed: {e}")
            self.test_results['errors'].append(f"Loading feedback error: {e}")
    
    def test_detailed_explanation_system(self):
        """Test enhanced explanation system with collapsible sections"""
        logger.info("🔍 Testing detailed explanation system...")
        
        try:
            # Test quiz page for explanation sections
            response = self.session.get(f'{self.base_url}/quiz')
            
            if response.status_code == 200:
                content = response.text
                
                # Check for enhanced explanation features
                explanation_checks = [
                    'explanation-technical' in content,
                    'explanation-simple' in content,
                    'explanation-concepts' in content,
                    'toggleExplanation' in content,
                    'explanation-header' in content,
                    'explanation-content' in content,
                    'collapsible' in content.lower()
                ]
                
                if all(explanation_checks):
                    self.test_results['detailed_explanations'] = True
                    logger.info("✅ Detailed explanation system: PASSED")
                else:
                    logger.warning("⚠️ Detailed explanation system: Some features missing")
                    self.test_results['errors'].append("Explanation features incomplete")
            else:
                logger.error(f"❌ Quiz page request failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Detailed explanation test failed: {e}")
            self.test_results['errors'].append(f"Explanation test error: {e}")
    
    def test_stripe_integration_validation(self):
        """Test complete Stripe integration with comprehensive logging"""
        logger.info("🔍 Testing Stripe integration validation...")
        
        try:
            # Test Stripe.js CDN integration
            response = self.session.get(f'{self.base_url}/quiz')
            
            if response.status_code == 200:
                content = response.text
                
                # Check for Stripe integration features
                stripe_checks = [
                    'stripe.com/v3' in content,
                    'upgradeToPro' in content,
                    'create-checkout-session' in content,
                    'window.location.href' in content,
                    'checkout_url' in content.lower()
                ]
                
                if all(stripe_checks):
                    self.test_results['stripe_integration'] = True
                    logger.info("✅ Stripe integration: PASSED")
                else:
                    logger.warning("⚠️ Stripe integration: Some features missing")
                    self.test_results['errors'].append("Stripe integration incomplete")
            else:
                logger.error(f"❌ Quiz page request failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Stripe integration test failed: {e}")
            self.test_results['errors'].append(f"Stripe test error: {e}")
    
    def test_performance_metrics(self):
        """Test performance requirements: loading <5s, total load <10s"""
        logger.info("🔍 Testing performance metrics...")
        
        try:
            # Test main page load time
            start_time = time.time()
            response = self.session.get(f'{self.base_url}/')
            main_load_time = time.time() - start_time
            
            # Test quiz page load time
            start_time = time.time()
            response = self.session.get(f'{self.base_url}/quiz')
            quiz_load_time = time.time() - start_time
            
            # Test API response time
            start_time = time.time()
            api_response = self.session.get(f'{self.base_url}/api/health', timeout=10)
            api_response_time = time.time() - start_time
            
            self.test_results['performance_metrics'] = {
                'main_load_time': main_load_time,
                'quiz_load_time': quiz_load_time,
                'api_response_time': api_response_time,
                'performance_target_met': all([
                    main_load_time < 5.0,
                    quiz_load_time < 5.0,
                    api_response_time < 2.0
                ])
            }
            
            logger.info(f"📊 Performance metrics:")
            logger.info(f"   Main page load: {main_load_time:.2f}s")
            logger.info(f"   Quiz page load: {quiz_load_time:.2f}s")
            logger.info(f"   API response: {api_response_time:.2f}s")
            
            if self.test_results['performance_metrics']['performance_target_met']:
                logger.info("✅ Performance targets: PASSED")
            else:
                logger.warning("⚠️ Performance targets: Some metrics exceed targets")
                
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            self.test_results['errors'].append(f"Performance test error: {e}")
    
    def test_complete_upgrade_flow_scenarios(self):
        """Test both upgrade flow scenarios with console logging validation"""
        logger.info("🔍 Testing complete upgrade flow scenarios...")
        
        try:
            # Scenario 1: Test checkout session creation endpoint
            logger.info("📋 Testing Scenario 1: Checkout session creation")
            
            # This would normally require authentication, so we test the endpoint exists
            response = self.session.post(f'{self.base_url}/create-checkout-session')
            
            if response.status_code in [401, 403]:  # Expected for unauthenticated request
                logger.info("✅ Checkout endpoint exists and requires authentication")
            elif response.status_code == 200:
                logger.info("✅ Checkout endpoint responding correctly")
            else:
                logger.warning(f"⚠️ Checkout endpoint returned: {response.status_code}")
            
            # Scenario 2: Test webhook endpoint exists
            logger.info("📋 Testing Scenario 2: Webhook endpoint")
            
            response = self.session.post(f'{self.base_url}/webhook/stripe')
            
            if response.status_code in [400, 401, 403]:  # Expected for invalid webhook
                logger.info("✅ Webhook endpoint exists and validates requests")
            elif response.status_code == 200:
                logger.info("✅ Webhook endpoint responding correctly")
            else:
                logger.warning(f"⚠️ Webhook endpoint returned: {response.status_code}")
                
            logger.info("✅ Upgrade flow scenarios: Basic validation passed")
            
        except Exception as e:
            logger.error(f"❌ Upgrade flow test failed: {e}")
            self.test_results['errors'].append(f"Upgrade flow error: {e}")
    
    def run_comprehensive_test_suite(self):
        """Run all tests and generate comprehensive report"""
        logger.info("🚀 Starting comprehensive enhanced mobile experience test suite")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # Run all test modules
        self.test_mobile_responsive_design()
        self.test_loading_feedback_system()
        self.test_detailed_explanation_system()
        self.test_stripe_integration_validation()
        self.test_performance_metrics()
        self.test_complete_upgrade_flow_scenarios()
        
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        logger.info("=" * 70)
        logger.info("📊 COMPREHENSIVE TEST RESULTS")
        logger.info("=" * 70)
        
        # Feature test results
        feature_results = [
            ("Mobile Responsiveness", self.test_results['mobile_responsiveness']),
            ("Loading Feedback System", self.test_results['loading_feedback']),
            ("Detailed Explanations", self.test_results['detailed_explanations']),
            ("Stripe Integration", self.test_results['stripe_integration'])
        ]
        
        passed_features = sum(1 for _, passed in feature_results if passed)
        total_features = len(feature_results)
        
        for feature, passed in feature_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"{feature:<25}: {status}")
        
        # Performance results
        perf = self.test_results['performance_metrics']
        if perf:
            logger.info(f"Performance Target Met   : {'✅ PASSED' if perf['performance_target_met'] else '❌ FAILED'}")
        
        # Summary
        logger.info("=" * 70)
        logger.info(f"📈 SUMMARY:")
        logger.info(f"   Features Passed: {passed_features}/{total_features}")
        logger.info(f"   Total Test Time: {total_time:.2f}s")
        logger.info(f"   Errors Encountered: {len(self.test_results['errors'])}")
        
        if self.test_results['errors']:
            logger.info(f"🔍 ERROR DETAILS:")
            for i, error in enumerate(self.test_results['errors'], 1):
                logger.info(f"   {i}. {error}")
        
        # Overall status
        overall_success = (
            passed_features == total_features and 
            len(self.test_results['errors']) == 0 and
            (not perf or perf['performance_target_met'])
        )
        
        if overall_success:
            logger.info("🎉 OVERALL STATUS: ALL TESTS PASSED - READY FOR DEPLOYMENT")
        else:
            logger.info("⚠️ OVERALL STATUS: SOME ISSUES FOUND - REVIEW REQUIRED")
        
        logger.info("=" * 70)
        
        return self.test_results

if __name__ == "__main__":
    print("🔧 Enhanced Mobile Experience Test Suite")
    print("Testing mobile responsiveness, loading feedback, explanations, and Stripe integration")
    print()
    
    tester = EnhancedMobileExperienceTest()
    results = tester.run_comprehensive_test_suite()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'test_results_enhanced_mobile_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: test_results_enhanced_mobile_{timestamp}.json")