#!/usr/bin/env python3
"""
Test xAI Integration Script
Tests GRE algebra question generation to verify OpenAI format compatibility
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from xai_question_generator import XAIQuestionGenerator

def test_xai_integration():
    """Test xAI integration with GRE algebra question"""
    print("🧪 Testing xAI Integration...")
    
    try:
        # Initialize generator
        generator = XAIQuestionGenerator()
        
        # Test with GRE quant algebra as requested
        print("📚 Generating GRE algebra question...")
        questions = generator.generate_questions("GRE", "algebra", 1)
        
        if not questions:
            print("❌ Test FAILED: No questions generated")
            return False
            
        question = questions[0]
        print("✅ Question generated successfully")
        
        # Verify OpenAI format compatibility
        required_fields = ['question', 'options', 'answer', 'explanation']
        missing_fields = [field for field in required_fields if field not in question]
        
        if missing_fields:
            print(f"❌ Test FAILED: Missing fields: {missing_fields}")
            return False
            
        print("✅ All required fields present")
        
        # Verify options format
        if not isinstance(question['options'], dict) or set(question['options'].keys()) != {'A', 'B', 'C', 'D'}:
            print(f"❌ Test FAILED: Invalid options format: {question['options']}")
            return False
            
        print("✅ Options format validated")
        
        # Verify answer is valid
        if question['answer'] not in ['A', 'B', 'C', 'D']:
            print(f"❌ Test FAILED: Invalid answer format: {question['answer']}")
            return False
            
        print("✅ Answer format validated")
        
        # Display sample question
        print("\n📋 Sample Generated Question:")
        print("-" * 50)
        print(f"Question: {question['question']}")
        print("\nOptions:")
        for key, value in question['options'].items():
            print(f"  {key}: {value}")
        print(f"\nCorrect Answer: {question['answer']}")
        print(f"Explanation: {question['explanation'][:100]}...")
        print("-" * 50)
        
        print("\n🎉 xAI Integration Test PASSED!")
        print("✅ OpenAI format compatibility confirmed")
        print("✅ Ready for production deployment")
        
        return True
        
    except Exception as e:
        print(f"❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_xai_integration()
    sys.exit(0 if success else 1)