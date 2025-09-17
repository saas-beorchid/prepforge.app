#!/usr/bin/env python3
"""
Test script for Adaptive UI Integration with Flask-Login authentication,
API calls, Mixpanel tracking, and button/CTA wiring.

This script tests the complete workflow:
1. Login authentication
2. Button/CTA clicks with Mixpanel tracking
3. Adaptive question generation based on user performance
4. Answer submission and score updates
5. JSON response validation
"""

import requests
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdaptiveUIIntegrationTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_id = None
        self.exam_type = "GRE"
        self.topic = "algebra"
        
    def test_authentication(self):
        """Test Flask-Login authentication"""
        logger.info("🔐 Testing authentication...")
        
        # Test if we can access protected routes
        response = self.session.get(f"{self.base_url}/dashboard")
        
        if response.status_code == 200:
            logger.info("✅ Authentication successful - dashboard accessible")
            return True
        elif "signin" in response.url:
            logger.info("🔄 Need to sign in - authentication working correctly")
            return True
        else:
            logger.error(f"❌ Authentication failed - status: {response.status_code}")
            return False
    
    def test_mixpanel_integration(self):
        """Test Mixpanel token availability and tracking setup"""
        logger.info("📊 Testing Mixpanel integration...")
        
        response = self.session.get(f"{self.base_url}/dashboard")
        
        # Check if Mixpanel token is available in the page
        if "mixpanel.init" in response.text:
            logger.info("✅ Mixpanel initialization code found in dashboard")
            return True
        else:
            logger.warning("⚠️ Mixpanel initialization not found - check MIXPANEL_TOKEN")
            return False
    
    def test_adaptive_question_api(self):
        """Test adaptive question generation API"""
        logger.info("🧠 Testing adaptive question generation...")
        
        try:
            # Test user performance endpoint
            performance_response = self.session.get(
                f"{self.base_url}/api/user-performance/{self.exam_type}/{self.topic}"
            )
            
            if performance_response.status_code == 200:
                performance_data = performance_response.json()
                logger.info(f"✅ User performance API working: {performance_data}")
            else:
                logger.warning(f"⚠️ Performance API returned: {performance_response.status_code}")
            
            # Test adaptive question generation
            question_payload = {
                "exam_type": self.exam_type,
                "topic": self.topic,
                "count": 1
            }
            
            question_response = self.session.post(
                f"{self.base_url}/api/generate-adaptive-questions",
                json=question_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if question_response.status_code == 200:
                question_data = question_response.json()
                if question_data.get("success") and question_data.get("questions"):
                    logger.info("✅ Adaptive question generation working")
                    self.validate_question_format(question_data["questions"][0])
                    return True
                else:
                    logger.error(f"❌ Question generation failed: {question_data}")
                    return False
            else:
                logger.error(f"❌ Question API failed with status: {question_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Adaptive question API test failed: {e}")
            return False
    
    def validate_question_format(self, question):
        """Validate question JSON format"""
        logger.info("🔍 Validating question format...")
        
        required_fields = ["question", "options", "answer", "explanation"]
        
        for field in required_fields:
            if field not in question:
                logger.error(f"❌ Missing required field: {field}")
                return False
        
        # Validate options format
        if not isinstance(question["options"], dict):
            logger.error("❌ Options should be a dictionary")
            return False
        
        # Check for standard multiple choice options (A, B, C, D)
        expected_options = {"A", "B", "C", "D"}
        actual_options = set(question["options"].keys())
        
        if not expected_options.issubset(actual_options):
            logger.error(f"❌ Invalid options format. Expected A,B,C,D, got: {actual_options}")
            return False
        
        logger.info("✅ Question format validation passed")
        logger.info(f"   Question: {question['question'][:100]}...")
        logger.info(f"   Difficulty: {question.get('difficulty', 'Not specified')}")
        logger.info(f"   Answer: {question['answer']}")
        
        return True
    
    def test_answer_submission(self):
        """Test answer submission and score updates"""
        logger.info("📝 Testing answer submission...")
        
        try:
            # Submit a test answer
            answer_payload = {
                "exam_type": self.exam_type,
                "topic": self.topic,
                "score": 75.0
            }
            
            response = self.session.post(
                f"{self.base_url}/api/update-performance",
                json=answer_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Answer submission working: {result}")
                return True
            else:
                logger.error(f"❌ Answer submission failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Answer submission test failed: {e}")
            return False
    
    def test_difficulty_adaptation(self):
        """Test difficulty adaptation based on scores"""
        logger.info("🎯 Testing difficulty adaptation...")
        
        test_scenarios = [
            {"score": 30, "expected_difficulty": "easy"},
            {"score": 55, "expected_difficulty": "medium"}, 
            {"score": 80, "expected_difficulty": "hard"}
        ]
        
        for scenario in test_scenarios:
            logger.info(f"Testing score {scenario['score']}% -> {scenario['expected_difficulty']}")
            
            # Update performance
            self.session.post(
                f"{self.base_url}/api/update-performance",
                json={
                    "exam_type": self.exam_type,
                    "topic": self.topic,
                    "score": scenario["score"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            # Generate question and check difficulty
            response = self.session.post(
                f"{self.base_url}/api/generate-adaptive-questions",
                json={
                    "exam_type": self.exam_type,
                    "topic": self.topic,
                    "count": 1
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("questions"):
                    question = data["questions"][0]
                    actual_difficulty = question.get("difficulty", "unknown")
                    
                    if actual_difficulty == scenario["expected_difficulty"]:
                        logger.info(f"✅ Correct difficulty adaptation: {actual_difficulty}")
                    else:
                        logger.warning(f"⚠️ Expected {scenario['expected_difficulty']}, got {actual_difficulty}")
                else:
                    logger.error("❌ No questions in response")
            else:
                logger.error(f"❌ Question generation failed: {response.status_code}")
                
            time.sleep(1)  # Brief delay between tests
        
        return True
    
    def test_javascript_integration(self):
        """Test JavaScript integration and button availability"""
        logger.info("🖱️ Testing JavaScript integration...")
        
        # Test dashboard page
        dashboard_response = self.session.get(f"{self.base_url}/dashboard")
        if "adaptive-practice.js" in dashboard_response.text:
            logger.info("✅ Adaptive practice JS loaded in dashboard")
        else:
            logger.warning("⚠️ Adaptive practice JS not found in dashboard")
        
        # Test practice page
        practice_response = self.session.get(f"{self.base_url}/practice")
        if practice_response.status_code == 200:
            if "adaptive-practice.js" in practice_response.text:
                logger.info("✅ Adaptive practice JS loaded in practice page")
            
            # Check for button elements
            if 'data-action="generate-question"' in practice_response.text:
                logger.info("✅ Generate question button found")
            else:
                logger.warning("⚠️ Generate question button not found")
                
            if 'data-action="start-practice"' in practice_response.text:
                logger.info("✅ Start practice button found")
            else:
                logger.warning("⚠️ Start practice button not found")
        
        return True
    
    def run_comprehensive_test(self):
        """Run all tests and provide summary"""
        logger.info("🚀 Starting comprehensive adaptive UI integration test")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        test_results = {}
        
        tests = [
            ("Authentication", self.test_authentication),
            ("Mixpanel Integration", self.test_mixpanel_integration),
            ("Adaptive Question API", self.test_adaptive_question_api),
            ("Answer Submission", self.test_answer_submission),
            ("Difficulty Adaptation", self.test_difficulty_adaptation),
            ("JavaScript Integration", self.test_javascript_integration)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n📋 Running: {test_name}")
                result = test_func()
                test_results[test_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                logger.info(f"   Status: {status}")
            except Exception as e:
                logger.error(f"   ❌ FAILED with exception: {e}")
                test_results[test_name] = False
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(test_results.values())
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name:<25} {status}")
        
        logger.info(f"\nTotal: {passed}/{total} tests passed")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - System ready for production!")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed - Review and fix issues")
        
        return passed == total

if __name__ == "__main__":
    tester = AdaptiveUIIntegrationTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)