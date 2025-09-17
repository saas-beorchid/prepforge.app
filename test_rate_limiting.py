#!/usr/bin/env python3
"""
Test rate limiting functionality specifically
"""

import requests
import json

def test_rate_limiting():
    """Test the rate limiting system"""
    
    print("🚫 RATE LIMITING TEST")
    print("=" * 25)
    
    session = requests.Session()
    
    # Login
    login_data = {'email': 'test@prepforge.com', 'password': 'testpass123'}
    login_response = session.post("http://localhost:5000/signin", data=login_data, allow_redirects=False)
    
    if login_response.status_code == 302:
        print("✅ Authenticated")
        
        # Follow redirect
        redirect_url = login_response.headers.get('Location', '/dashboard')
        if not redirect_url.startswith('http'):
            redirect_url = f"http://localhost:5000{redirect_url}"
        session.get(redirect_url)
        
        # Test rate limiting for specific exam type
        print("Testing GRE rate limiting...")
        
        for i in range(22):  # Try 22 requests (should hit limit at 21)
            response = session.post(
                "http://localhost:5000/api/generate-questions",
                json={"exam_type": "GRE", "count": 1},
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Request {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                print("✅ Rate limit triggered!")
                try:
                    data = response.json()
                    print(f"Error: {data.get('error')}")
                    print(f"Exam type: {data.get('exam_type')}")
                    print(f"Remaining: {data.get('remaining')}")
                except:
                    pass
                break
            elif response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  Remaining: {data.get('questions_remaining')}")
                except:
                    pass
        
        # Test different exam type (should have separate limit)
        print("\nTesting GMAT rate limiting (separate limit)...")
        gmat_response = session.post(
            "http://localhost:5000/api/generate-questions",
            json={"exam_type": "GMAT", "count": 1},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"GMAT request: {gmat_response.status_code}")
        if gmat_response.status_code == 200:
            try:
                data = gmat_response.json()
                print(f"GMAT remaining: {data.get('questions_remaining')}")
                print("✅ Per-exam-type limits working")
            except:
                pass
    else:
        print("❌ Authentication failed")

if __name__ == "__main__":
    test_rate_limiting()