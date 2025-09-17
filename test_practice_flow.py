#!/usr/bin/env python3
"""
Test Complete Practice Flow
Test the end-to-end practice and answer submission flow
"""

import requests
from bs4 import BeautifulSoup
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_practice_flow():
    """Test the complete practice flow from login to answer submission"""
    
    session = requests.Session()
    
    logger.info("🧪 TESTING COMPLETE PRACTICE FLOW")
    logger.info("=" * 50)
    
    try:
        # Step 1: Login
        logger.info("Step 1: User authentication...")
        
        signin_page = session.get('http://localhost:5000/signin')
        soup = BeautifulSoup(signin_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        
        login_data = {
            'email': 'abibasakor@gmail.com',
            'password': 'admin123456',
            'csrf_token': csrf_token
        }
        
        login_response = session.post(
            'http://localhost:5000/signin',
            data=login_data,
            allow_redirects=True
        )
        
        # Verify login by checking dashboard access
        dashboard_test = session.get('http://localhost:5000/dashboard')
        if dashboard_test.status_code != 200:
            logger.error("❌ Login failed - cannot access dashboard")
            return False
        
        logger.info("✅ User authenticated successfully")
        
        # Step 2: Start practice session
        logger.info("Step 2: Starting practice session...")
        
        dashboard_page = session.get('http://localhost:5000/dashboard')
        soup = BeautifulSoup(dashboard_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        
        practice_data = {
            'exam_type': 'GRE',
            'csrf_token': csrf_token
        }
        
        practice_response = session.post(
            'http://localhost:5000/start-practice',
            data=practice_data,
            allow_redirects=True
        )
        
        if practice_response.status_code != 200:
            logger.error(f"❌ Failed to start practice session: {practice_response.status_code}")
            return False
        
        logger.info("✅ Practice session started successfully")
        
        # Step 3: Access practice question
        logger.info("Step 3: Accessing practice question...")
        
        practice_page = session.get('http://localhost:5000/practice')
        if practice_page.status_code != 200:
            logger.error(f"❌ Failed to access practice page: {practice_page.status_code}")
            return False
        
        if 'question' not in practice_page.text.lower():
            logger.error("❌ No question content found on practice page")
            return False
        
        logger.info("✅ Practice question loaded successfully")
        
        # Step 4: Submit answer
        logger.info("Step 4: Submitting answer...")
        
        soup = BeautifulSoup(practice_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            csrf_token = csrf_token['value']
        else:
            logger.warning("No CSRF token found, proceeding without it")
            csrf_token = ""
        
        answer_data = {
            'answer': 'A',  # Submit option A
            'csrf_token': csrf_token
        }
        
        submit_response = session.post(
            'http://localhost:5000/submit-answer',
            data=answer_data,
            allow_redirects=True
        )
        
        if submit_response.status_code != 200:
            logger.error(f"❌ Failed to submit answer: {submit_response.status_code}")
            return False
        
        # Check if we get feedback or next question
        if 'correct' in submit_response.text.lower() or 'incorrect' in submit_response.text.lower():
            logger.info("✅ Answer submitted successfully - feedback received")
        elif 'question' in submit_response.text.lower():
            logger.info("✅ Answer submitted successfully - next question loaded")
        else:
            logger.warning("⚠️  Answer submitted but unclear feedback")
        
        # Step 5: Test next question navigation
        logger.info("Step 5: Testing question navigation...")
        
        next_response = session.get('http://localhost:5000/next-question')
        if next_response.status_code == 200:
            logger.info("✅ Question navigation working")
        else:
            logger.warning(f"⚠️  Question navigation issue: {next_response.status_code}")
        
        logger.info("=" * 50)
        logger.info("🎉 COMPLETE PRACTICE FLOW: SUCCESSFUL")
        logger.info("✅ Users can now practice questions and submit answers")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Practice flow test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_practice_flow()
    exit(0 if success else 1)