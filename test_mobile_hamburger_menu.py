#!/usr/bin/env python3
"""
Test Mobile Hamburger Menu Functionality
Quick test to validate the hamburger menu is working in mobile view
"""

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hamburger_menu():
    """Test hamburger menu implementation"""
    try:
        # Test base template contains hamburger menu elements
        response = requests.get('http://localhost:5000/')
        
        if response.status_code == 200:
            content = response.text
            
            # Check for hamburger menu elements
            checks = {
                'Mobile menu toggle element': 'mobile-menu-toggle' in content,
                'Main navigation element': 'main-nav' in content,
                'Hamburger spans': '<span></span>' in content,
                'Mobile CSS styles': '@media (max-width: 768px)' in content,
                'Toggle active class': 'mobile-menu-toggle.active' in content,
                'Navigation active class': 'nav.active' in content or 'main-nav.active' in content,
                'JavaScript event listener': 'addEventListener' in content,
                'Console logging': 'Hamburger menu clicked' in content,
                'Accessibility attributes': 'aria-expanded' in content
            }
            
            print("🔍 Hamburger Menu Test Results:")
            print("=" * 50)
            
            passed = 0
            total = len(checks)
            
            for check_name, result in checks.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{check_name:<30}: {status}")
                if result:
                    passed += 1
            
            print("=" * 50)
            print(f"📊 Summary: {passed}/{total} checks passed")
            
            if passed == total:
                print("🎉 Hamburger menu implementation: COMPLETE")
                return True
            else:
                print("⚠️ Hamburger menu implementation: INCOMPLETE")
                return False
                
        else:
            print(f"❌ Failed to fetch page: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🍔 Testing Mobile Hamburger Menu Functionality")
    print()
    
    success = test_hamburger_menu()
    
    if success:
        print("\n✅ Hamburger menu is ready for mobile testing!")
        print("📱 To test on mobile:")
        print("   1. Open browser dev tools")
        print("   2. Switch to mobile view (360px width)")
        print("   3. Click the hamburger menu (top right)")
        print("   4. Verify menu opens/closes smoothly")
    else:
        print("\n❌ Hamburger menu needs additional fixes")