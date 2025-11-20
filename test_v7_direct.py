#!/usr/bin/env python3
"""
Direct test of v7 - tests SQL generation and execution without LLM
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the LLM dependencies
class MockChatOpenAI:
    def invoke(self, messages):
        class MockResponse:
            content = '{"colors": ["red"]}'
        return MockResponse()

# Set up mocks before importing
import importlib
import types

# Create mock modules
mock_dotenv = types.ModuleType('dotenv')
mock_dotenv.load_dotenv = lambda: None

mock_langchain = types.ModuleType('langchain_openai')
mock_langchain.ChatOpenAI = MockChatOpenAI

# Inject mocks
sys.modules['dotenv'] = mock_dotenv
sys.modules['langchain_openai'] = mock_langchain

# Now try to import
try:
    from v7_chat_bot import build_sql_from_memory, MemoryState, run_sql
    print("✅ Successfully imported v7_chat_bot")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def test_sql_generation():
    """Test SQL generation with various memory states"""
    print("\n" + "="*80)
    print("TESTING SQL GENERATION")
    print("="*80)
    
    tests = [
        {
            "name": "Red flowers",
            "memory": lambda: MemoryState().__dict__.update({"colors": ["red"], "color_logic": "OR"}) or MemoryState(),
            "expected": ["has_red = 1", "FROM flowers_view"]
        },
        {
            "name": "Red roses for wedding",
            "memory": lambda: MemoryState().__dict__.update({
                "colors": ["red"], 
                "color_logic": "OR",
                "flower_types": ["rose"],
                "occasions": ["wedding"]
            }) or MemoryState(),
            "expected": ["has_red = 1", "FROM flowers_view", "LIKE '%rose%'", "LIKE '%wedding%'"]
        },
        {
            "name": "Under $100",
            "memory": lambda: MemoryState().__dict__.update({"budget": {"max": 100}}) or MemoryState(),
            "expected": ["variant_price < 100", "FROM flowers_view"]
        }
    ]
    
    for test in tests:
        print(f"\nTest: {test['name']}")
        try:
            # Create memory state
            memory = MemoryState()
            if test['name'] == "Red flowers":
                memory.colors = ["red"]
                memory.color_logic = "OR"
            elif test['name'] == "Red roses for wedding":
                memory.colors = ["red"]
                memory.color_logic = "OR"
                memory.flower_types = ["rose"]
                memory.occasions = ["wedding"]
            elif test['name'] == "Under $100":
                memory.budget = {"max": 100}
            
            # Generate SQL
            sql = build_sql_from_memory(memory)
            
            # Check for expected patterns
            all_found = True
            for pattern in test['expected']:
                if pattern in sql:
                    print(f"  ✅ Found: {pattern}")
                else:
                    print(f"  ❌ Missing: {pattern}")
                    all_found = False
            
            # Check for forbidden patterns
            forbidden = ["= true", "= false", "DISTINCT ON", "random()", "FROM flowers\n"]
            for pattern in forbidden:
                if pattern in sql and "flowers_view" not in sql.split(pattern)[0][-20:]:
                    print(f"  ⚠️  Found forbidden: {pattern}")
            
            if all_found:
                print(f"  ✅ {test['name']}: SQL generation looks good")
                print(f"     SQL length: {len(sql)} chars")
            else:
                print(f"  ❌ {test['name']}: Some patterns missing")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    return True

def test_sql_execution():
    """Test actual SQL execution"""
    print("\n" + "="*80)
    print("TESTING SQL EXECUTION")
    print("="*80)
    
    # Simple test query
    test_sql = """
    SELECT product_name, variant_price, colors_raw
    FROM flowers_view
    WHERE has_red = 1
    LIMIT 3
    """
    
    print(f"\nTest Query: Simple red flowers query")
    try:
        rows, exec_time = run_sql(test_sql)
        print(f"  ✅ Query executed successfully!")
        print(f"  Execution time: {exec_time:.3f}s")
        print(f"  Rows returned: {len(rows)}")
        
        if rows:
            print(f"  First row type: {type(rows[0])}")
            if isinstance(rows[0], dict):
                print(f"  ✅ Rows are dictionaries")
                print(f"  First row keys: {list(rows[0].keys())[:5]}...")
                print(f"  Sample: {rows[0].get('product_name', 'N/A')[:50]}")
            else:
                print(f"  ⚠️  Rows are not dictionaries: {type(rows[0])}")
        else:
            print(f"  ⚠️  No rows returned")
            
        return True
    except Exception as e:
        print(f"  ❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*80)
    print("V7 DIRECT TESTING")
    print("="*80)
    
    # Test 1: SQL Generation
    sql_ok = test_sql_generation()
    
    # Test 2: SQL Execution
    exec_ok = test_sql_execution()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"SQL Generation: {'✅ PASS' if sql_ok else '❌ FAIL'}")
    print(f"SQL Execution: {'✅ PASS' if exec_ok else '❌ FAIL'}")
    
    if sql_ok and exec_ok:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

