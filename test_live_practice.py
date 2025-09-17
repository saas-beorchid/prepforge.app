#!/usr/bin/env python3
"""
Live test of the practice system using actual HTTP requests.
This will test the complete user flow including authentication.
"""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"
session = requests.Session()

def test_signin_and_practice():
    """Test the complete signin -> practice flow"""
    
    print("🔐 Testing signin and practice flow...")
    
    # Step 1: Get signin page
    signin_response = session.get(f"{BASE_URL}/signin")
    if signin_response.status_code != 200:
        print(f"❌ Signin page failed: {signin_response.status_code}")
        return False
    
    print("✅ Signin page accessible")
    
    # Step 2: Check if we can access dashboard (might be auto-logged in)
    dashboard_response = session.get(f"{BASE_URL}/dashboard")
    if dashboard_response.status_code == 200:
        print("✅ Already authenticated - can access dashboard")
        
        # Step 3: Try to start practice session
        practice_data = {
            'exam_type': 'GRE'
        }
        
        practice_start = session.post(f"{BASE_URL}/start-practice", data=practice_data)
        
        if practice_start.status_code == 302:  # Redirect to practice
            print("✅ Practice session started successfully")
            
            # Step 4: Try to access practice page
            practice_response = session.get(f"{BASE_URL}/practice")
            
            if practice_response.status_code == 200:
                print("✅ Practice page loaded successfully!")
                print("🎉 CSRF issue appears to be resolved!")
                return True
            else:
                print(f"❌ Practice page failed: {practice_response.status_code}")
                print("Response:", practice_response.text[:500])
                return False
        else:
            print(f"❌ Practice start failed: {practice_start.status_code}")
            return False
    else:
        print(f"⚠️ Not authenticated - need to test manual login")
        return False

if __name__ == "__main__":
    success = test_signin_and_practice()
    if success:
        print("\n🎉 SUCCESS: Authentication and practice system working!")
    else:
        print("\n❌ FAILURE: Issues remain with authentication or practice")