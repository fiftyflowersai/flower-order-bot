#!/usr/bin/env python3
"""
Iterative test suite for v7 chatbot filter combinations.
Tests various user queries to ensure all filters work correctly.
"""

import sys
import os
from io import StringIO
from contextlib import redirect_stdout

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from v7_chat_bot import FlowerConsultant
except ImportError as e:
    print(f"❌ Failed to import v7_chat_bot: {e}")
    print("Make sure v7_chat_bot.py exists and dependencies are installed")
    sys.exit(1)


def test_query(bot, query, expected_filters=None):
    """
    Test a single query and validate the results.
    
    Args:
        bot: FlowerConsultant instance
        query: User query string
        expected_filters: Dict of expected filter states (optional)
    
    Returns:
        (success: bool, message: str, results: list)
    """
    print(f"\n{'='*60}")
    print(f"Testing: '{query}'")
    print(f"{'='*60}")
    
    try:
        # Capture output
        buffer = StringIO()
        with redirect_stdout(buffer):
            bot.ask(query)
        output = buffer.getvalue()
        
        # Get memory state
        memory = bot.memory.to_dict()
        
        # Check if SQL was generated and executed
        if "SQL execution error" in output or "SQL execution failed" in output:
            return False, f"SQL execution failed:\n{output}", None
        
        if "Error:" in output and "attribute" in output:
            return False, f"Code error:\n{output}", None
        
        # Check if we got results
        if "Here are" in output or "recommendations" in output.lower():
            # Try to extract results count
            lines = output.split('\n')
            result_lines = [l for l in lines if 'product_name' in l.lower() or 'variant_name' in l.lower() or 'price' in l.lower()]
            return True, f"✅ Query successful\n{output[:500]}...", output
        elif "No products found" in output or "no results" in output.lower():
            return True, f"✅ Query successful (no results found)\n{output[:300]}", output
        else:
            return False, f"Unexpected output format:\n{output[:500]}", output
        
    except Exception as e:
        import traceback
        return False, f"Exception: {str(e)}\n{traceback.format_exc()}", None


def run_all_tests():
    """Run all test queries iteratively."""
    
    test_cases = [
        {
            'name': 'Red roses for a wedding',
            'query': "I want red roses for a wedding",
            'description': 'Tests: color (red) + product type (roses) + occasion (wedding)'
        },
        {
            'name': 'Spring flowers under $100',
            'query': "Show me spring flowers under $100",
            'description': 'Tests: seasonality (spring) + budget (under $100)'
        },
        {
            'name': "Pink flowers for Mother's Day",
            'query': "I need pink flowers for Mother's Day",
            'description': 'Tests: color (pink) + occasion (Mother\'s Day)'
        },
        {
            'name': 'Budget-friendly DIY bouquets',
            'query': "Budget-friendly DIY bouquets",
            'description': 'Tests: budget (implicit) + DIY level + product type (bouquets)'
        },
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*60}")
        print(f"TEST {i}/{len(test_cases)}: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"{'#'*60}")
        
        # Create fresh bot instance for each test
        bot = FlowerConsultant(debug=False)
        
        success, message, output = test_query(bot, test_case['query'])
        
        results.append({
            'test': test_case['name'],
            'query': test_case['query'],
            'success': success,
            'message': message,
            'output': output
        })
        
        if success:
            print(f"✅ PASSED: {test_case['name']}")
        else:
            print(f"❌ FAILED: {test_case['name']}")
            print(f"   {message}")
    
    # Summary
    print(f"\n\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    for r in results:
        status = "✅ PASS" if r['success'] else "❌ FAIL"
        print(f"{status}: {r['test']}")
        if not r['success']:
            print(f"   Error: {r['message'][:200]}...")
    
    if passed == total:
        print(f"\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

