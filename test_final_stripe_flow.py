#!/usr/bin/env python3
"""
Final Stripe Integration Test
Complete end-to-end test of the upgrade flow
"""

import requests
import time
import json

class FinalStripeTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
        self.test_user = {
            'email': 'anothermobile15@gmail.com',
            'password': 'Tobeornottobe@123'
        }
        
    def authenticate_user(self):
        """Authenticate the test user"""
        print("🔐 Authenticating user...")
        
        signin_data = {
            'email': self.test_user['email'],
            'password': self.test_user['password']
        }
        
        response = self.session.post(f"{self.base_url}/signin", data=signin_data)
        
        if response.status_code == 200 and 'dashboard' in response.url:
            print("✅ User authenticated successfully")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    
    def test_checkout_session_creation(self):
        """Test creating a Stripe checkout session"""
        print("💳 Testing Stripe checkout session creation...")
        
        response = self.session.post(f"{self.base_url}/create-checkout-session", allow_redirects=False)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 303:
            location = response.headers.get('Location', '')
            print(f"Redirect location: {location}")
            
            if 'checkout.stripe.com' in location:
                print("✅ Stripe checkout session created successfully!")
                print(f"Checkout URL: {location}")
                return True, location
            else:
                print(f"❌ Invalid redirect location: {location}")
                return False, None
        else:
            print(f"❌ Checkout creation failed: {response.status_code}")
            try:
                print(f"Response content: {response.text[:200]}...")
            except:
                pass
            return False, None
    
    def simulate_successful_payment_webhook(self):
        """Simulate a successful payment webhook"""
        print("🎭 Simulating successful payment webhook...")
        
        webhook_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_final_123456789",
                    "client_reference_id": "15",  # User ID 15
                    "customer_email": self.test_user['email'],
                    "payment_status": "paid",
                    "subscription": "sub_test_final_123456789",
                    "metadata": {
                        "user_id": "15",
                        "upgrade_type": "pro"
                    }
                }
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/webhook",
            json=webhook_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Webhook response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook processed successfully")
            return True
        else:
            print(f"❌ Webhook failed: {response.text}")
            return False
    
    def verify_pro_subscription_access(self):
        """Verify user now has pro subscription access"""
        print("🎯 Verifying pro subscription access...")
        
        # Test generating multiple questions (should work for pro users)
        exam_types = ['GRE', 'GMAT', 'MCAT']
        success_count = 0
        
        for exam_type in exam_types:
            quiz_data = {
                'exam_type': exam_type,
                'count': 1
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate-questions",
                json=quiz_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success') and data.get('questions'):
                        success_count += 1
                        print(f"  ✅ {exam_type} question generated successfully")
                    else:
                        print(f"  ❌ {exam_type} generation failed: {data}")
                except:
                    print(f"  ❌ {exam_type} invalid JSON response")
            elif response.status_code == 429:
                print(f"  ❌ {exam_type} rate limited (pro upgrade didn't work)")
            else:
                print(f"  ❌ {exam_type} API error: {response.status_code}")
        
        pro_access_working = success_count >= 2
        print(f"Pro access verification: {success_count}/{len(exam_types)} successful")
        return pro_access_working
    
    def run_final_test(self):
        """Run the complete final Stripe integration test"""
        print("🚀 FINAL STRIPE INTEGRATION TEST")
        print("=" * 70)
        print("Testing complete upgrade flow: auth → checkout → webhook → pro access")
        print("=" * 70)
        
        # Step 1: Authenticate user
        if not self.authenticate_user():
            print("❌ Cannot proceed without authentication")
            return False
        
        print()
        
        # Step 2: Test checkout session creation
        checkout_success, checkout_url = self.test_checkout_session_creation()
        if not checkout_success:
            print("❌ Cannot proceed without working checkout")
            return False
        
        print()
        
        # Step 3: Simulate successful payment
        webhook_success = self.simulate_successful_payment_webhook()
        if not webhook_success:
            print("❌ Webhook processing failed")
            return False
        
        print()
        
        # Step 4: Verify pro access
        time.sleep(1)  # Brief wait for database update
        pro_access = self.verify_pro_subscription_access()
        
        print("\n" + "=" * 70)
        print("🏆 FINAL TEST RESULTS")
        print("=" * 70)
        
        all_tests_passed = checkout_success and webhook_success and pro_access
        
        if all_tests_passed:
            print("🎉 STRIPE INTEGRATION FULLY OPERATIONAL!")
            print()
            print("✅ User authentication working")
            print("✅ Stripe checkout session creation working")
            print("✅ Webhook payment processing working")
            print("✅ Pro subscription access working")
            print()
            print("🎯 READY FOR PRODUCTION!")
            print()
            print("Manual Test Instructions:")
            print("1. Sign in to the application")
            print("2. Go to /quiz page")
            print("3. Click 'Upgrade to Pro' button")
            print("4. Complete payment with test card: 4242 4242 4242 4242")
            print("5. Verify unlimited question generation")
            print()
            print(f"Test Checkout URL: {checkout_url}")
        else:
            print("❌ STRIPE INTEGRATION HAS ISSUES")
            print()
            if not checkout_success:
                print("• Checkout session creation failed")
            if not webhook_success:
                print("• Webhook processing failed")
            if not pro_access:
                print("• Pro access verification failed")
        
        return all_tests_passed

def main():
    test = FinalStripeTest()
    return test.run_final_test()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)