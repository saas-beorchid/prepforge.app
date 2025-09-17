#!/usr/bin/env python3
"""
Final Stripe Integration Test - Complete End-to-End Flow
"""

import requests
import time
import json

def test_complete_stripe_flow():
    """Test the complete Stripe upgrade flow"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("🚀 FINAL STRIPE INTEGRATION TEST")
    print("=" * 60)
    
    # Step 1: Authenticate user
    print("1. Authenticating user...")
    signin_data = {
        'email': 'anothermobile15@gmail.com',
        'password': 'Tobeornottobe@123'
    }
    
    response = session.post(f"{base_url}/signin", data=signin_data)
    if response.status_code == 200 and 'dashboard' in response.url:
        print("   ✅ Authentication successful")
    else:
        print(f"   ❌ Authentication failed: {response.status_code}")
        return False
    
    # Step 2: Test checkout session creation
    print("2. Creating Stripe checkout session...")
    response = session.post(f"{base_url}/create-checkout-session", allow_redirects=False)
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 303:
        checkout_url = response.headers.get('Location', '')
        print(f"   Redirect URL: {checkout_url}")
        
        if 'checkout.stripe.com' in checkout_url:
            print("   ✅ Stripe checkout session created successfully!")
            print(f"   🔗 Checkout URL: {checkout_url}")
            
            # Step 3: Simulate successful payment webhook
            print("3. Simulating successful payment webhook...")
            webhook_payload = {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_final_payment",
                        "client_reference_id": "15",
                        "customer_email": "anothermobile15@gmail.com",
                        "payment_status": "paid",
                        "subscription": "sub_test_final_payment",
                        "metadata": {
                            "user_id": "15",
                            "upgrade_type": "pro"
                        }
                    }
                }
            }
            
            webhook_response = session.post(
                f"{base_url}/webhook",
                json=webhook_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if webhook_response.status_code == 200:
                print("   ✅ Webhook processed successfully")
                
                print("\n🎉 STRIPE INTEGRATION COMPLETE!")
                print("=" * 60)
                print("✅ User authentication working")
                print("✅ Stripe checkout session creation working")
                print("✅ Webhook processing working")
                print()
                print("🎯 READY FOR PRODUCTION TESTING!")
                print()
                print("Manual Test Instructions:")
                print("1. Sign in: anothermobile15@gmail.com / Tobeornottobe@123")
                print("2. Go to /quiz page")
                print("3. Click 'Upgrade to Pro' button")
                print("4. Complete payment with test card: 4242 4242 4242 4242")
                print("5. Verify unlimited question generation")
                print()
                print(f"Test Checkout URL: {checkout_url}")
                return True
            else:
                print(f"   ❌ Webhook failed: {webhook_response.status_code}")
                return False
        else:
            print(f"   ❌ Invalid checkout URL: {checkout_url}")
            return False
    elif response.status_code == 302:
        location = response.headers.get('Location', '')
        if '/signin' in location:
            print("   ❌ Redirected to signin - authentication issue")
        else:
            print(f"   ❌ Unexpected redirect: {location}")
        return False
    else:
        print(f"   ❌ Unexpected response: {response.status_code}")
        try:
            print(f"   Response content: {response.text[:200]}...")
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_complete_stripe_flow()
    exit(0 if success else 1)