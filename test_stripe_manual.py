#!/usr/bin/env python3
"""
Manual Stripe Integration Test
Simple test to verify Stripe checkout works when properly authenticated
"""

import requests
import urllib.parse

def test_manual_stripe():
    """Test Stripe integration with manual session handling"""
    print("🚀 MANUAL STRIPE INTEGRATION TEST")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Step 1: Get login page for CSRF token
    print("1. Getting login page...")
    session = requests.Session()
    login_page = session.get(f"{base_url}/signin")
    print(f"   Login page status: {login_page.status_code}")
    
    # Step 2: Attempt login
    print("2. Attempting login...")
    login_data = {
        'email': 'anothermobile15@gmail.com',
        'password': 'Tobeornottobe@123'
    }
    
    login_response = session.post(f"{base_url}/signin", data=login_data, allow_redirects=True)
    print(f"   Login response status: {login_response.status_code}")
    print(f"   Final URL: {login_response.url}")
    
    # Check if we're on dashboard
    if 'dashboard' in login_response.url.lower():
        print("   ✅ Successfully authenticated")
        
        # Step 3: Test checkout session creation
        print("3. Testing checkout session creation...")
        checkout_response = session.post(f"{base_url}/create-checkout-session", allow_redirects=False)
        print(f"   Checkout status: {checkout_response.status_code}")
        
        if checkout_response.status_code == 303:
            location = checkout_response.headers.get('Location', '')
            print(f"   Redirect location: {location}")
            
            if 'checkout.stripe.com' in location:
                print("   ✅ Stripe checkout session created!")
                print(f"   🔗 Checkout URL: {location}")
                
                # Test webhook simulation
                print("4. Testing webhook simulation...")
                webhook_data = {
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "id": "cs_test_manual_123",
                            "client_reference_id": "15",
                            "customer_email": "anothermobile15@gmail.com",
                            "payment_status": "paid",
                            "subscription": "sub_test_manual_123"
                        }
                    }
                }
                
                webhook_response = session.post(
                    f"{base_url}/webhook",
                    json=webhook_data,
                    headers={'Content-Type': 'application/json'}
                )
                print(f"   Webhook status: {webhook_response.status_code}")
                
                if webhook_response.status_code == 200:
                    print("   ✅ Webhook processed successfully")
                    
                    print("\n🎉 STRIPE INTEGRATION WORKING!")
                    print("=" * 50)
                    print("✅ Authentication successful")
                    print("✅ Checkout session creation working")
                    print("✅ Webhook processing working")
                    print()
                    print("🎯 PRODUCTION READY!")
                    print()
                    print("Test Instructions:")
                    print("1. Sign in to the application")
                    print("2. Navigate to /quiz page")
                    print("3. Click 'Upgrade to Pro' button")
                    print("4. Use test card: 4242 4242 4242 4242")
                    print("5. Complete payment flow")
                    print()
                    print(f"Live Checkout URL: {location}")
                    return True
                else:
                    print(f"   ❌ Webhook failed: {webhook_response.text}")
            else:
                print(f"   ❌ Invalid checkout URL: {location}")
        elif checkout_response.status_code == 302:
            location = checkout_response.headers.get('Location', '')
            print(f"   ❌ Redirected to: {location}")
        else:
            print(f"   ❌ Checkout failed: {checkout_response.status_code}")
            print(f"   Response: {checkout_response.text[:200]}...")
    else:
        print("   ❌ Authentication failed - not redirected to dashboard")
        print(f"   Response contains: {login_response.text[:200]}...")
    
    return False

if __name__ == "__main__":
    success = test_manual_stripe()
    exit(0 if success else 1)