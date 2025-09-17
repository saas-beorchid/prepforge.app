#!/usr/bin/env python3
"""
Direct test of API endpoint to verify it's working
"""

import requests
import json

def test_api_endpoints():
    """Test API endpoints directly"""
    
    print("🔧 DIRECT API ENDPOINT TEST")
    print("=" * 30)
    
    session = requests.Session()
    
    # Login first
    print("Step 1: Authentication...")
    login_data = {'email': 'test@prepforge.com', 'password': 'testpass123'}
    login_response = session.post("http://localhost:5000/signin", data=login_data, allow_redirects=False)
    print(f"Login: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("✅ Authenticated successfully")
        
        # Follow redirect to establish session
        redirect_url = login_response.headers.get('Location', '/dashboard')
        if not redirect_url.startswith('http'):
            redirect_url = f"http://localhost:5000{redirect_url}"
        session.get(redirect_url)
        
        # Test question generation
        print("\nStep 2: Testing question generation API...")
        test_data = {"exam_type": "GRE", "count": 1}
        
        response = session.post(
            "http://localhost:5000/api/generate-questions",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"API Response: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ API working successfully")
                print(f"Response data: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
                print(f"Raw response: {response.text[:200]}")
        else:
            print(f"❌ API failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
        # Test answer submission
        print("\nStep 3: Testing answer submission API...")
        answer_data = {
            "question_id": "test-question",
            "answer": "A",
            "exam_type": "GRE"
        }
        
        answer_response = session.post(
            "http://localhost:5000/api/submit-answer",
            json=answer_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Answer API Response: {answer_response.status_code}")
        
        if answer_response.status_code == 200:
            try:
                answer_data = answer_response.json()
                print("✅ Answer API working")
                print(f"Answer result: {json.dumps(answer_data, indent=2)}")
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
        else:
            print(f"❌ Answer API failed: {answer_response.status_code}")
            print(f"Response: {answer_response.text[:200]}")
            
    else:
        print("❌ Authentication failed")

if __name__ == "__main__":
    test_api_endpoints()