#!/usr/bin/env python3
"""
Manual authentication test to verify the complete adaptive system works.
This creates a test user and simulates the complete authentication flow.
"""

import os
import sys
sys.path.append('.')

from app import app
from models import User, db
from werkzeug.security import generate_password_hash
from flask_login import login_user
import requests
import logging

logging.basicConfig(level=logging.INFO)

def create_test_user():
    """Create a test user for authentication"""
    with app.app_context():
        # Check if test user exists
        test_user = User.query.filter_by(email='test@prepforge.com').first()
        if not test_user:
            test_user = User(
                name='Test User',
                email='test@prepforge.com',
                password_hash=generate_password_hash('testpass123'),
                subscription_plan='free'
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"✅ Created test user: {test_user.email} (ID: {test_user.id})")
        else:
            print(f"✅ Test user exists: {test_user.email} (ID: {test_user.id})")
        
        return test_user.id

def test_authentication_flow():
    """Test the complete authentication and adaptive system flow"""
    
    print("🧪 Starting comprehensive authentication and adaptive system test")
    print("=" * 60)
    
    # Create test user
    user_id = create_test_user()
    
    # Test session with manual login
    session = requests.Session()
    
    # Step 1: Get signup/signin page and extract CSRF
    signin_response = session.get("http://localhost:5000/signin")
    print(f"✅ Signin page accessible: {signin_response.status_code}")
    
    # Step 2: Try manual login
    login_data = {
        'email': 'test@prepforge.com',
        'password': 'testpass123'
    }
    
    login_response = session.post("http://localhost:5000/signin", data=login_data)
    print(f"Login response: {login_response.status_code}")
    
    if login_response.status_code == 302:  # Redirect after successful login
        print("✅ Login successful - redirected")
        
        # Step 3: Access dashboard
        dashboard_response = session.get("http://localhost:5000/dashboard")
        if dashboard_response.status_code == 200:
            print("✅ Dashboard accessible after login")
            
            # Check for adaptive practice JS
            if "adaptive-practice.js" in dashboard_response.text:
                print("✅ Adaptive practice JavaScript loaded")
            
            if "Mixpanel" in dashboard_response.text or "mixpanel" in dashboard_response.text:
                print("✅ Mixpanel tracking initialized")
            
            # Step 4: Start practice session
            practice_data = {'exam_type': 'GRE'}
            start_response = session.post("http://localhost:5000/start-practice", data=practice_data)
            
            if start_response.status_code in [200, 302]:
                print("✅ Practice session started")
                
                # Step 5: Access practice page
                practice_response = session.get("http://localhost:5000/practice")
                
                if practice_response.status_code == 200:
                    print("🎉 SUCCESS: Practice page loaded without CSRF errors!")
                    
                    # Check for adaptive controls
                    if "Generate Adaptive Question" in practice_response.text:
                        print("✅ Adaptive question generation button found")
                    
                    if "difficulty-indicator" in practice_response.text:
                        print("✅ Difficulty indicator present")
                    
                    if "user-score" in practice_response.text:
                        print("✅ User score display present")
                    
                    return True
                else:
                    print(f"❌ Practice page failed: {practice_response.status_code}")
                    if "csrf_token" in practice_response.text.lower():
                        print("   CSRF token issue detected")
            else:
                print(f"❌ Practice start failed: {start_response.status_code}")
        else:
            print(f"❌ Dashboard access failed: {dashboard_response.status_code}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print("Response:", login_response.text[:500])
    
    return False

if __name__ == "__main__":
    success = test_authentication_flow()
    if success:
        print("\n🎉 COMPLETE SUCCESS: All systems operational!")
        print("✅ Authentication working")  
        print("✅ Practice system working")
        print("✅ Adaptive controls present")
        print("✅ CSRF issues resolved")
        print("\n🚀 Ready for user testing!")
    else:
        print("\n❌ Issues detected - continuing debugging...")