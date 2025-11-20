#!/usr/bin/env python3
"""
Iterative test script for v7 - tests the chatbot directly
Run this after starting web_demo_v2.py or use it standalone
"""
import sys
import io
from v7_chat_bot import FlowerConsultant

def test_query(bot, message, test_name):
    """Test a single query"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"Query: '{message}'")
    print('='*80)
    
    # Capture output
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    
    try:
        bot.ask(message)
        output = buffer.getvalue()
        sys.stdout = old_stdout
        
        # Check for errors
        if "error" in output.lower() or "SQL execution error" in output:
            print("❌ ERROR DETECTED:")
            print(output)
            return False
        elif len(output) < 50:
            print("⚠️  SHORT RESPONSE (might be empty):")
            print(output)
            return False
        else:
            print("✅ SUCCESS!")
            print(output[:400] + "..." if len(output) > 400 else output)
            return True
    except Exception as e:
        sys.stdout = old_stdout
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all test queries"""
    print("="*80)
    print("V7 ITERATIVE TEST SUITE")
    print("="*80)
    
    bot = FlowerConsultant(debug=False)
    results = []
    
    # Test suite
    tests = [
        ("red flowers", "Simple color filter"),
        ("under $100", "Budget filter"),
        ("ready to go flowers", "DIY level filter"),
        ("wedding flowers", "Occasion filter"),
        ("red roses for a wedding", "Complex: color + flower type + occasion"),
        ("red and white flowers under $200", "Complex: multiple colors + budget"),
        ("pink flowers for valentine's day", "Color + occasion"),
        ("show me roses", "Flower type only"),
    ]
    
    for message, test_name in tests:
        success = test_query(bot, message, test_name)
        results.append((test_name, success))
        # Small delay between tests
        import time
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nPassed: {passed}/{total} ({passed*100//total}%)")
    print("\nResults:")
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
    
    return passed == total

if __name__ == "__main__":
    try:
        all_passed = run_all_tests()
        sys.exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

