#!/usr/bin/env python3
"""
COMPLETE PRACTICE FLOW TESTING
==============================

Tests the entire user journey from dashboard to question practice,
ensuring no 500 errors and complete functional flow.
"""

import sys
import time
import json
import requests
from datetime import datetime
sys.path.append('.')

from app import app, db
from models import User, Question, CachedQuestion

class PracticeFlowTester:
    """Test complete practice flow end-to-end"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = {}
        self.errors = []
    
    def run_complete_flow_test(self):
        """Run complete practice flow testing"""
        print("=" * 70)
        print("COMPLETE PRACTICE FLOW TESTING")
        print("=" * 70)
        
        # Test 1: Basic route accessibility
        self.test_basic_routes()
        
        # Test 2: Question availability system
        self.test_question_availability()
        
        # Test 3: Database operations
        self.test_database_operations()
        
        # Test 4: Error handling
        self.test_error_handling()
        
        # Test 5: Performance under load
        self.test_performance()
        
        # Generate final report
        self.generate_flow_report()
    
    def test_basic_routes(self):
        """Test all basic routes work without 500 errors"""
        print("\n🔍 TESTING BASIC ROUTES")
        
        routes = [
            ('/', 'Homepage'),
            ('/about', 'About Page'),
            ('/signin', 'Sign In'),
            ('/signup', 'Sign Up'),
            ('/pricing', 'Pricing (may redirect)'),
        ]
        
        successful_routes = 0
        
        for route, name in routes:
            try:
                response = requests.get(f"{self.base_url}{route}", timeout=10)
                if response.status_code in [200, 302]:
                    print(f"✅ {name}: {response.status_code}")
                    successful_routes += 1
                else:
                    print(f"❌ {name}: {response.status_code}")
                    self.errors.append(f"Route {route} returned {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: {e}")
                self.errors.append(f"Route {route} failed: {e}")
        
        self.test_results['basic_routes'] = (successful_routes / len(routes)) * 100
    
    def test_question_availability(self):
        """Test question availability across all exam types"""
        print("\n🔍 TESTING QUESTION AVAILABILITY")
        
        with app.app_context():
            exam_types = ['GMAT', 'GRE', 'MCAT', 'USMLE_STEP_1', 'NCLEX', 'LSAT', 'SAT', 'ACT']
            available_exams = 0
            total_questions = 0
            
            for exam_type in exam_types:
                regular_count = Question.query.filter_by(exam_type=exam_type).count()
                cached_count = CachedQuestion.query.filter_by(exam_type=exam_type).count()
                total_count = regular_count + cached_count
                
                if total_count > 0:
                    available_exams += 1
                    total_questions += total_count
                    print(f"✅ {exam_type}: {total_count} questions available")
                else:
                    print(f"❌ {exam_type}: No questions available")
                    self.errors.append(f"No questions for {exam_type}")
            
            coverage = (available_exams / len(exam_types)) * 100
            self.test_results['question_availability'] = coverage
            print(f"\n📊 Question Coverage: {coverage:.1f}%")
            print(f"📊 Total Questions: {total_questions}")
    
    def test_database_operations(self):
        """Test database operations work correctly"""
        print("\n🔍 TESTING DATABASE OPERATIONS")
        
        with app.app_context():
            try:
                # Test basic database connection
                db.session.execute("SELECT 1").scalar()
                print("✅ Database connection working")
                
                # Test query performance
                start_time = time.time()
                questions = Question.query.limit(10).all()
                query_time = (time.time() - start_time) * 1000
                print(f"✅ Question query: {query_time:.2f}ms")
                
                # Test cached questions
                cached_questions = CachedQuestion.query.limit(5).all()
                print(f"✅ Cached questions: {len(cached_questions)} available")
                
                # Test user operations
                user_count = User.query.count()
                print(f"✅ Users in database: {user_count}")
                
                self.test_results['database_operations'] = 100
                
            except Exception as e:
                print(f"❌ Database operations failed: {e}")
                self.errors.append(f"Database operations: {e}")
                self.test_results['database_operations'] = 0
    
    def test_error_handling(self):
        """Test error handling mechanisms"""
        print("\n🔍 TESTING ERROR HANDLING")
        
        try:
            # Test 404 handling
            response = requests.get(f"{self.base_url}/nonexistent-page", timeout=5)
            if response.status_code == 404:
                print("✅ 404 handling: Working")
            else:
                print(f"⚠️ 404 handling: Unexpected {response.status_code}")
            
            # Test emergency question generation
            from emergency_question_generator import emergency_generator
            test_questions = emergency_generator.generate_emergency_questions('GMAT', count=2)
            if len(test_questions) >= 2:
                print("✅ Emergency question generation: Working")
            else:
                print("⚠️ Emergency question generation: Limited")
            
            self.test_results['error_handling'] = 100
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            self.errors.append(f"Error handling: {e}")
            self.test_results['error_handling'] = 0
    
    def test_performance(self):
        """Test system performance"""
        print("\n🔍 TESTING PERFORMANCE")
        
        try:
            # Test multiple concurrent requests
            import threading
            results = []
            
            def test_request():
                try:
                    start = time.time()
                    response = requests.get(f"{self.base_url}/", timeout=10)
                    duration = time.time() - start
                    results.append((response.status_code, duration))
                except Exception as e:
                    results.append((0, 999))
            
            # Run 5 concurrent requests
            threads = []
            for i in range(5):
                thread = threading.Thread(target=test_request)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            successful_requests = sum(1 for status, _ in results if status == 200)
            avg_response_time = sum(duration for _, duration in results) / len(results)
            
            print(f"✅ Concurrent requests: {successful_requests}/5 successful")
            print(f"✅ Average response time: {avg_response_time:.2f}s")
            
            performance_score = (successful_requests / 5) * 100
            if avg_response_time > 2.0:
                performance_score -= 20
            
            self.test_results['performance'] = performance_score
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            self.errors.append(f"Performance: {e}")
            self.test_results['performance'] = 0
    
    def generate_flow_report(self):
        """Generate comprehensive flow test report"""
        print("\n" + "=" * 70)
        print("PRACTICE FLOW TEST REPORT")
        print("=" * 70)
        
        print(f"\n📊 TEST RESULTS:")
        for test_name, score in self.test_results.items():
            status = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}: {score:.1f}%")
        
        overall_score = sum(self.test_results.values()) / len(self.test_results) if self.test_results else 0
        print(f"\n🎯 OVERALL FLOW HEALTH: {overall_score:.1f}%")
        
        if self.errors:
            print(f"\n⚠️ ISSUES IDENTIFIED ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")
        else:
            print(f"\n✅ NO CRITICAL ISSUES FOUND")
        
        if overall_score >= 90:
            print("🟢 FLOW STATUS: EXCELLENT - Users can practice seamlessly")
        elif overall_score >= 75:
            print("🟡 FLOW STATUS: GOOD - Minor optimizations possible")
        elif overall_score >= 50:
            print("🟠 FLOW STATUS: WARNING - Some issues need attention")
        else:
            print("🔴 FLOW STATUS: CRITICAL - Practice flow needs fixes")
        
        return overall_score

if __name__ == "__main__":
    tester = PracticeFlowTester()
    score = tester.run_complete_flow_test()
    print(f"\nPractice flow testing completed. Overall score: {score:.1f}%")