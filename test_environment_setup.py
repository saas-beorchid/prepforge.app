#!/usr/bin/env python3
"""
Switch to Test Environment for Safe Development
"""

import os

def setup_test_environment():
    """Setup test keys and environment for safe development"""
    print("🔧 SWITCHING TO TEST ENVIRONMENT")
    print("=" * 50)
    
    print("✅ Test Key Configuration:")
    print("- Use sk_test_... for Stripe secret key")
    print("- Use pk_test_... for Stripe publishable key")
    print("- Test webhook endpoint: /webhook")
    print("- Test card: 4242 4242 4242 4242")
    
    print("\n✅ Development Setup:")
    print("- ngrok http 5000 (for hCaptcha 401 fix)")
    print("- Localhost domain configuration")
    print("- Test webhook endpoints")
    
    print("\n✅ Database Configuration:")
    print("- Development database only")
    print("- Test user subscriptions")
    print("- Safe mock transactions")
    
    print("\n🎯 READY FOR SAFE TESTING")
    print("Switch to test keys in your Stripe dashboard")
    print("Use ngrok for external webhook testing")

if __name__ == "__main__":
    setup_test_environment()