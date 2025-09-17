#!/usr/bin/env python3
"""
Test the fixed quiz API endpoints
"""

import requests
import json
import time

def test_fixed_api():
    """Test the fixed API endpoints"""
    
    print("🔧 TESTING FIXED QUIZ API")
    print("=" * 30)
    
    session = requests.Session()
    
    # Step 1: Login
    print("Step 1: Authentication...")
    login_data = {'email': 'test@prepforge.com', 'password': 'testpass123'}
    login_response = session.post("http://localhost:5000/signin", data=login_data, allow_redirects=False)
    
    if login_response.status_code == 302:
        print("✅ Login successful")
        
        # Follow redirect
        redirect_url = login_response.headers.get('Location', '/dashboard')
        if not redirect_url.startswith('http'):
            redirect_url = f"http://localhost:5000{redirect_url}"
        session.get(redirect_url)
        
        # Step 2: Test question generation
        print("\nStep 2: Testing question generation...")
        
        for exam in ['GRE', 'GMAT', 'MCAT']:
            response = session.post(
                "http://localhost:5000/api/generate-questions",
                json={"exam_type": exam, "topic": "algebra", "count": 1},
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"{exam}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('questions'):
                        q = data['questions'][0]
                        print(f"  ✅ Question: {q['question_text'][:50]}...")
                        print(f"  Choices: {len(q['choices'])}")
                        print(f"  Answer: {q['correct_answer']}")
                        
                        # Test answer submission
                        answer_response = session.post(
                            "http://localhost:5000/api/submit-answer",
                            json={
                                "question_id": q['id'],
                                "answer": "A",
                                "exam_type": exam,
                                "question_data": q
                            },
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        print(f"  Submit Answer: {answer_response.status_code}")
                        
                        if answer_response.status_code == 200:
                            answer_data = answer_response.json()
                            print(f"  ✅ Answer processed - Correct: {answer_data.get('is_correct')}")
                        
                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON error: {e}")
            else:
                print(f"  ❌ Failed: {response.status_code}")
        
        # Step 3: Test rate limiting
        print("\nStep 3: Testing multiple requests...")
        for i in range(5):
            resp = session.post(
                "http://localhost:5000/api/generate-questions",
                json={"exam_type": "GRE", "count": 1},
                headers={'Content-Type': 'application/json'}
            )
            print(f"Request {i+1}: {resp.status_code}")
            
            if resp.status_code == 429:
                print("✅ Rate limiting triggered")
                break
        
    else:
        print(f"❌ Login failed: {login_response.status_code}")

if __name__ == "__main__":
    test_fixed_api()