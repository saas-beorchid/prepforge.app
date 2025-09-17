#!/usr/bin/env python3
"""
Test Stripe Integration for PrepForge Pro Upgrades
Tests the complete upgrade flow: login → checkout → webhook → verification
"""

import requests
import json
import time
import subprocess

class StripeIntegrationTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
        self.test_user = {
            'email': 'anothermobile14@gmail.com',
            'password': 'Tobeornottobe@123',
            'user_id': 7
        }
        
    def test_authentication(self):
        """Test user authentication (user_id 7)"""
        print("🔐 Testing authentication for user_id 7...")
        
        login_data = {
            'email': self.test_user['email'],
            'password': self.test_user['password']
        }
        
        response = self.session.post(f"{self.base_url}/signin", data=login_data, allow_redirects=True)
        
        if response.status_code == 200:
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    
    def test_checkout_session_creation(self):
        """Test Stripe checkout session creation"""
        print("💳 Testing Stripe checkout session creation...")
        
        response = self.session.post(
            f"{self.base_url}/api/create-checkout-session",
            headers={'Content-Type': 'application/json'},
            json={}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {data}")
            
            if data.get('success') and data.get('checkout_url'):
                print("✅ Checkout session created successfully")
                print(f"Checkout URL: {data['checkout_url']}")
                return True, data['checkout_url']
            else:
                print(f"❌ Checkout session creation failed: {data}")
                return False, None
        else:
            print(f"❌ API request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text}")
            return False, None
    
    def test_subscription_status(self):
        """Test subscription status API"""
        print("📊 Testing subscription status API...")
        
        response = self.session.get(f"{self.base_url}/api/subscription-status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Subscription status: {data}")
            return data
        else:
            print(f"❌ Subscription status check failed: {response.status_code}")
            return None
    
    def simulate_successful_payment(self):
        """Simulate a successful Stripe webhook"""
        print("🎭 Simulating successful Stripe webhook...")
        
        # Simulate webhook payload for successful payment
        webhook_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123456789",
                    "client_reference_id": str(self.test_user['user_id']),
                    "customer_email": self.test_user['email'],
                    "payment_status": "paid",
                    "metadata": {
                        "user_id": self.test_user['user_id'],
                        "upgrade_type": "pro"
                    }
                }
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/webhook/stripe",
            json=webhook_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Webhook response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook processed successfully")
            return True
        else:
            print(f"❌ Webhook processing failed")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text}")
            return False
    
    def verify_subscription_upgrade(self):
        """Verify that user subscription was upgraded to pro"""
        print("🔍 Verifying subscription upgrade...")
        
        # Check subscription status
        status_data = self.test_subscription_status()
        
        if status_data and status_data.get('subscription_plan') == 'pro':
            print("✅ Subscription successfully upgraded to Pro!")
            return True
        else:
            print(f"❌ Subscription not upgraded. Current status: {status_data}")
            return False
    
    def test_quiz_page_upgrade_button(self):
        """Test that upgrade button is properly configured on quiz page"""
        print("🎮 Testing quiz page upgrade button...")
        
        response = self.session.get(f"{self.base_url}/quiz")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for upgrade button and JavaScript function
            has_upgrade_button = 'id="upgrade-btn"' in content
            has_stripe_function = 'upgradeToProStripe' in content
            has_stripe_api_call = '/api/create-checkout-session' in content
            
            print(f"  Upgrade button present: {'✅' if has_upgrade_button else '❌'}")
            print(f"  Stripe function present: {'✅' if has_stripe_function else '❌'}")
            print(f"  API call configured: {'✅' if has_stripe_api_call else '❌'}")
            
            return has_upgrade_button and has_stripe_function and has_stripe_api_call
        else:
            print(f"❌ Could not access quiz page: {response.status_code}")
            return False
    
    def run_complete_test(self):
        """Run the complete Stripe integration test"""
        print("🚀 STRIPE INTEGRATION TEST SUITE")
        print("=" * 60)
        
        results = {}
        
        # Step 1: Authentication
        results['auth'] = self.test_authentication()
        if not results['auth']:
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Quiz page upgrade button
        results['quiz_button'] = self.test_quiz_page_upgrade_button()
        
        # Step 3: Initial subscription status
        print("\n📊 Checking initial subscription status...")
        initial_status = self.test_subscription_status()
        results['initial_status'] = initial_status is not None
        
        # Step 4: Checkout session creation
        results['checkout'], checkout_url = self.test_checkout_session_creation()
        
        # Step 5: Simulate webhook (payment completion)
        results['webhook'] = self.simulate_successful_payment()
        
        # Step 6: Verify upgrade
        time.sleep(1)  # Brief wait for database update
        results['upgrade_verified'] = self.verify_subscription_upgrade()
        
        # Summary
        print("\n" + "=" * 60)
        print("🏆 STRIPE INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        test_results = [
            ("User Authentication", results['auth']),
            ("Quiz Page Button", results['quiz_button']),
            ("Initial Status Check", results['initial_status']),
            ("Checkout Session Creation", results['checkout']),
            ("Webhook Processing", results['webhook']),
            ("Subscription Upgrade", results['upgrade_verified'])
        ]
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print()
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        # Integration assessment
        integration_working = (
            results['auth'] and 
            results['checkout'] and 
            results['webhook'] and 
            results['upgrade_verified']
        )
        
        print(f"\n🎯 Stripe Integration: {'✅ WORKING' if integration_working else '❌ NEEDS FIXES'}")
        
        if integration_working:
            print("\n🎉 STRIPE INTEGRATION SUCCESS!")
            print("  • User authentication ✅")
            print("  • Checkout session creation ✅") 
            print("  • Webhook processing ✅")
            print("  • Subscription upgrade ✅")
            print("  • Ready for test card: 4242 4242 4242 4242")
        else:
            print("\n⚠️ Integration issues detected:")
            if not results['auth']:
                print("  • Authentication failure")
            if not results['checkout']:
                print("  • Checkout session creation issues")
            if not results['webhook']:
                print("  • Webhook processing problems")
            if not results['upgrade_verified']:
                print("  • Subscription upgrade not working")
        
        return integration_working

def main():
    """Run the Stripe integration test"""
    test_suite = StripeIntegrationTest()
    success = test_suite.run_complete_test()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)