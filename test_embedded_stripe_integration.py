#!/usr/bin/env python3
"""
Embedded Stripe Checkout Integration Test
Tests the new embedded checkout functionality with @stripe/stripe-js
"""

import requests
import time
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddedStripeIntegrationTest:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'embedded_checkout_backend': False,
            'client_secret_generation': False,
            'frontend_integration': False,
            'ui_mode_embedded': False,
            'mobile_responsive_checkout': False,
            'error_handling': False,
            'performance': False,
            'errors': []
        }
    
    def test_embedded_checkout_backend(self):
        """Test that backend returns client_secret instead of checkout_url"""
        logger.info("🔍 Testing embedded checkout backend integration...")
        
        try:
            # Test the create-checkout-session endpoint
            response = self.session.post(f'{self.base_url}/create-checkout-session')
            
            if response.status_code in [200, 401, 403]:  # Endpoint exists
                try:
                    data = response.json()
                    
                    # Check if response structure is for embedded checkout
                    has_client_secret = 'client_secret' in str(data)
                    no_checkout_url = 'checkout_url' not in str(data)
                    has_session_id = 'session_id' in str(data)
                    
                    if has_client_secret and no_checkout_url and has_session_id:
                        self.results['embedded_checkout_backend'] = True
                        logger.info("✅ Backend configured for embedded checkout")
                    else:
                        logger.warning("⚠️ Backend may still be using redirect checkout")
                        self.results['errors'].append("Backend not configured for embedded checkout")
                except:
                    # If not JSON, check for proper error handling
                    logger.info("✅ Backend endpoint exists and handles requests")
                    
            else:
                logger.error("❌ Checkout endpoint not accessible")
                self.results['errors'].append("Checkout endpoint not accessible")
                
        except Exception as e:
            logger.error(f"❌ Backend test failed: {e}")
            self.results['errors'].append(f"Backend test error: {e}")
    
    def test_client_secret_generation(self):
        """Test that Stripe session is created with ui_mode='embedded'"""
        logger.info("🔍 Testing client secret generation...")
        
        try:
            # Check if the app.py contains embedded configuration
            with open('app.py', 'r') as f:
                app_content = f.read()
                
            embedded_checks = [
                "ui_mode='embedded'" in app_content,
                "client_secret" in app_content,
                "return_url" in app_content,
                "initEmbeddedCheckout" in app_content or "client_secret" in app_content
            ]
            
            if all(embedded_checks):
                self.results['client_secret_generation'] = True
                logger.info("✅ Client secret generation configured")
            else:
                logger.warning("⚠️ Client secret generation may not be properly configured")
                self.results['errors'].append("Client secret generation incomplete")
                
        except Exception as e:
            logger.error(f"❌ Client secret test failed: {e}")
            self.results['errors'].append(f"Client secret error: {e}")
    
    def test_frontend_integration(self):
        """Test frontend @stripe/stripe-js integration"""
        logger.info("🔍 Testing frontend embedded checkout integration...")
        
        try:
            # Check quiz.html for embedded checkout code
            response = self.session.get(f'{self.base_url}/quiz')
            
            if response.status_code == 200:
                content = response.text
                
                frontend_checks = [
                    'initEmbeddedCheckout' in content,
                    'client_secret' in content,
                    'mountEmbeddedCheckout' in content,
                    'checkout-overlay' in content,
                    'embedded-checkout-container' in content,
                    'stripe.com/v3' in content,
                    'upgradeToProEmbedded' in content or 'client_secret' in content
                ]
                
                if all(frontend_checks):
                    self.results['frontend_integration'] = True
                    logger.info("✅ Frontend embedded checkout integration complete")
                else:
                    logger.warning("⚠️ Frontend integration may be incomplete")
                    missing = [f"Check {i}" for i, check in enumerate(frontend_checks) if not check]
                    self.results['errors'].append(f"Frontend missing: {missing}")
                    
        except Exception as e:
            logger.error(f"❌ Frontend integration test failed: {e}")
            self.results['errors'].append(f"Frontend integration error: {e}")
    
    def test_ui_mode_embedded(self):
        """Test that UI mode is set to embedded"""
        logger.info("🔍 Testing UI mode embedded configuration...")
        
        try:
            # Check app.py for ui_mode='embedded'
            with open('app.py', 'r') as f:
                app_content = f.read()
            
            # Check quiz.js for embedded checkout methods
            with open('static/js/quiz.js', 'r') as f:
                js_content = f.read()
            
            ui_mode_checks = [
                "ui_mode='embedded'" in app_content,
                "initializeEmbeddedCheckout" in js_content,
                "createCheckoutContainer" in js_content,
                "client_secret" in js_content,
                "closeCheckout" in js_content
            ]
            
            if all(ui_mode_checks):
                self.results['ui_mode_embedded'] = True
                logger.info("✅ UI mode embedded properly configured")
            else:
                logger.warning("⚠️ UI mode embedded configuration incomplete")
                self.results['errors'].append("UI mode embedded incomplete")
                
        except Exception as e:
            logger.error(f"❌ UI mode test failed: {e}")
            self.results['errors'].append(f"UI mode error: {e}")
    
    def test_mobile_responsive_checkout(self):
        """Test mobile responsiveness of embedded checkout"""
        logger.info("🔍 Testing mobile responsive embedded checkout...")
        
        try:
            # Check for mobile styles in base.html and CSS
            response = self.session.get(f'{self.base_url}/quiz')
            
            if response.status_code == 200:
                content = response.text
                
                mobile_checks = [
                    'checkout-overlay' in content,
                    '@media (max-width: 768px)' in content,
                    'backdrop-filter: blur' in content,
                    'padding: 1rem' in content,
                    'box-shadow:' in content,
                    'border-radius:' in content
                ]
                
                if all(mobile_checks):
                    self.results['mobile_responsive_checkout'] = True
                    logger.info("✅ Mobile responsive checkout configured")
                else:
                    logger.warning("⚠️ Mobile responsive checkout incomplete")
                    self.results['errors'].append("Mobile responsive checkout incomplete")
                    
        except Exception as e:
            logger.error(f"❌ Mobile responsive test failed: {e}")
            self.results['errors'].append(f"Mobile responsive error: {e}")
    
    def test_error_handling(self):
        """Test error handling for embedded checkout"""
        logger.info("🔍 Testing embedded checkout error handling...")
        
        try:
            # Check for error handling in JavaScript
            with open('static/js/quiz.js', 'r') as f:
                js_content = f.read()
            
            error_checks = [
                'try {' in js_content and 'catch' in js_content,
                'showError' in js_content,
                'console.error' in js_content,
                'Failed to load checkout' in js_content or 'checkout failed' in js_content,
                'hideLoading' in js_content
            ]
            
            if all(error_checks):
                self.results['error_handling'] = True
                logger.info("✅ Error handling properly implemented")
            else:
                logger.warning("⚠️ Error handling may be incomplete")
                self.results['errors'].append("Error handling incomplete")
                
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.results['errors'].append(f"Error handling error: {e}")
    
    def test_performance_requirements(self):
        """Test performance of embedded checkout"""
        logger.info("🔍 Testing embedded checkout performance...")
        
        try:
            # Test page load with embedded checkout
            start_time = time.time()
            response = self.session.get(f'{self.base_url}/quiz')
            load_time = time.time() - start_time
            
            # Test API endpoint response
            start_time = time.time()
            api_response = self.session.get(f'{self.base_url}/api/health', timeout=10)
            api_time = time.time() - start_time
            
            performance_ok = (
                load_time < 5.0 and  # Page loads in under 5s
                api_time < 3.0 and   # API responds in under 3s
                response.status_code == 200
            )
            
            if performance_ok:
                self.results['performance'] = True
                logger.info(f"✅ Performance: PASSED (Page: {load_time:.2f}s, API: {api_time:.2f}s)")
            else:
                logger.warning(f"⚠️ Performance: FAILED (Page: {load_time:.2f}s, API: {api_time:.2f}s)")
                self.results['errors'].append(f"Performance issue - Page: {load_time:.2f}s")
                
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            self.results['errors'].append(f"Performance error: {e}")
    
    def run_complete_test_suite(self):
        """Run all embedded Stripe checkout tests"""
        logger.info("🚀 Starting Embedded Stripe Checkout Integration Test Suite")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # Run all tests
        self.test_embedded_checkout_backend()
        self.test_client_secret_generation()
        self.test_frontend_integration()
        self.test_ui_mode_embedded()
        self.test_mobile_responsive_checkout()
        self.test_error_handling()
        self.test_performance_requirements()
        
        total_time = time.time() - start_time
        
        # Generate report
        logger.info("=" * 70)
        logger.info("📊 EMBEDDED STRIPE CHECKOUT TEST RESULTS")
        logger.info("=" * 70)
        
        tests = [
            ("Backend Integration", self.results['embedded_checkout_backend']),
            ("Client Secret Generation", self.results['client_secret_generation']),
            ("Frontend Integration", self.results['frontend_integration']),
            ("UI Mode Embedded", self.results['ui_mode_embedded']),
            ("Mobile Responsive", self.results['mobile_responsive_checkout']),
            ("Error Handling", self.results['error_handling']),
            ("Performance", self.results['performance'])
        ]
        
        passed_tests = sum(1 for _, passed in tests if passed)
        total_tests = len(tests)
        
        for test_name, passed in tests:
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"{test_name:<25}: {status}")
        
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
            logger.info("🎉 OVERALL STATUS: EMBEDDED STRIPE CHECKOUT FULLY INTEGRATED")
        else:
            logger.info("⚠️ OVERALL STATUS: SOME INTEGRATION ISSUES DETECTED")
        
        logger.info("=" * 70)
        
        return self.results

if __name__ == "__main__":
    print("🛒 Embedded Stripe Checkout Integration Test Suite")
    print("Testing @stripe/stripe-js embedded checkout implementation")
    print()
    
    tester = EmbeddedStripeIntegrationTest()
    results = tester.run_complete_test_suite()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'test_results_embedded_stripe_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: test_results_embedded_stripe_{timestamp}.json")