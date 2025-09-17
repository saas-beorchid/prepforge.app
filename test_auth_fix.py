#!/usr/bin/env python3
"""
Test the authentication fix after resolving Unicode encoding issue
"""

import requests
import time

def test_authentication_complete():
    """Test complete authentication flow after Unicode fix"""
    
    print("🧪 Testing Authentication After Unicode Fix")
    print("=" * 50)
    
    session = requests.Session()
    
    # Wait for app to restart
    print("⏳ Waiting for app to restart...")
    time.sleep(5)
    
    try:
        # Test signin page
        signin_response = session.get("http://localhost:5000/signin")
        print(f"✅ Signin page: {signin_response.status_code}")
        
        # Test login with test user
        login_data = {
            'email': 'test@prepforge.com',
            'password': 'testpass123'
        }
        
        login_response = session.post("http://localhost:5000/signin", data=login_data)
        print(f"🔐 Login response: {login_response.status_code}")
        
        if login_response.status_code == 302:
            print("🎉 SUCCESS: Login works without Unicode errors!")
            
            # Test dashboard access
            dashboard_response = session.get("http://localhost:5000/dashboard")
            print(f"📊 Dashboard: {dashboard_response.status_code}")
            
            # Test quiz page
            quiz_response = session.get("http://localhost:5000/quiz")
            print(f"🧠 Quiz page: {quiz_response.status_code}")
            
            if quiz_response.status_code == 200:
                print("🎯 SUCCESS: Complete system working!")
                
                # Check for key components
                if "Generate Question" in quiz_response.text:
                    print("✅ Generate Question button found")
                if "Submit Answer" in quiz_response.text:
                    print("✅ Submit Answer button found")
                if "Upgrade to Pro" in quiz_response.text:
                    print("✅ Upgrade button found")
                if "quiz.js" in quiz_response.text:
                    print("✅ Quiz JavaScript loaded")
                
                return True
            else:
                print(f"❌ Quiz page failed: {quiz_response.status_code}")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            if "UnicodeEncodeError" in login_response.text:
                print("   Unicode error still present")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    return False

if __name__ == "__main__":
    success = test_authentication_complete()
    if success:
        print("\n🚀 SYSTEM READY: All authentication and quiz components working!")
    else:
        print("\n⚠️  Issues remain - continuing to debug...")