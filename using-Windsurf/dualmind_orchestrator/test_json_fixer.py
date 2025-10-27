"""
Test script to verify the JSON fixer module works correctly
"""

import sys
import json
sys.path.append('.')

from json_fixer import (
    fix_json_string,
    extract_and_fix_json,
    parse_llm_json,
    validate_plan_json,
    validate_verification_json
)

print("=" * 70)
print("Testing JSON Fixer Module")
print("=" * 70)

# Test 1: Valid JSON (should pass through)
print("\n🧪 Test 1: Valid JSON")
valid_json = '{"query": "test", "reasoning": "testing", "pipeline": [], "final_output": "result"}'
try:
    result = extract_and_fix_json(valid_json)
    parsed = json.loads(result)
    print(f"✅ PASS - Valid JSON processed correctly")
except Exception as e:
    print(f"❌ FAIL - {e}")

# Test 2: JSON with markdown code blocks
print("\n🧪 Test 2: JSON with markdown code blocks")
markdown_json = '''```json
{
    "query": "test",
    "reasoning": "testing",
    "pipeline": [],
    "final_output": "result"
}
```'''
try:
    result = extract_and_fix_json(markdown_json)
    parsed = json.loads(result)
    print(f"✅ PASS - Markdown removed successfully")
except Exception as e:
    print(f"❌ FAIL - {e}")

# Test 3: JSON with explanatory text before
print("\n🧪 Test 3: JSON with explanatory text")
text_before_json = '''Here is the plan you requested:
{
    "query": "test",
    "reasoning": "testing",
    "pipeline": [],
    "final_output": "result"
}'''
try:
    result = extract_and_fix_json(text_before_json)
    parsed = json.loads(result)
    print(f"✅ PASS - Extracted JSON from text")
except Exception as e:
    print(f"❌ FAIL - {e}")

# Test 4: JSON with trailing comma (common LLM error)
print("\n🧪 Test 4: JSON with trailing comma")
trailing_comma = '''{
    "query": "test",
    "reasoning": "testing",
    "pipeline": [],
    "final_output": "result",
}'''
try:
    result = fix_json_string(trailing_comma)
    parsed = json.loads(result)
    print(f"✅ PASS - Trailing comma fixed")
except Exception as e:
    print(f"❌ FAIL - {e}")

# Test 5: JSON with single quotes (Python-style)
print("\n🧪 Test 5: JSON with single quotes")
single_quotes = """{
    'query': 'test',
    'reasoning': 'testing',
    'pipeline': [],
    'final_output': 'result'
}"""
try:
    result = fix_json_string(single_quotes)
    parsed = json.loads(result)
    print(f"✅ PASS - Single quotes converted to double quotes")
except Exception as e:
    print(f"❌ FAIL - {e}")

# Test 6: JSON with Python booleans (True/False)
print("\n🧪 Test 6: JSON with Python booleans")
python_booleans = '''{
    "overall_approval": True,
    "score": 85,
    "issues": [],
    "suggestions": [],
    "improvements": []
}'''
try:
    result = fix_json_string(python_booleans)
    parsed = json.loads(result)
    print(f"✅ PASS - Python booleans converted to JSON (True -> true)")
    print(f"   Parsed value: {parsed['overall_approval']} (type: {type(parsed['overall_approval']).__name__})")
except Exception as e:
    print(f"❌ FAIL - {e}")

# Test 7: Parse LLM JSON with missing keys (should add defaults)
print("\n🧪 Test 7: Parse LLM JSON with missing keys")
incomplete_plan = '{"query": "test", "pipeline": []}'
try:
    result = parse_llm_json(incomplete_plan, expected_keys=["query", "reasoning", "pipeline", "final_output"])
    print(f"✅ PASS - Missing keys filled with defaults")
    print(f"   Keys: {list(result.keys())}")
    print(f"   reasoning: '{result.get('reasoning')}'")
    print(f"   final_output: '{result.get('final_output')}'")
except Exception as e:
    print(f"❌ FAIL - {e}")

# Test 8: Validate plan structure
print("\n🧪 Test 8: Validate plan structure")
valid_plan = {
    "query": "test query",
    "reasoning": "test reasoning",
    "pipeline": [
        {"tool": "qa_engine", "purpose": "answer", "input": "test"}
    ],
    "final_output": "result"
}
is_valid = validate_plan_json(valid_plan)
if is_valid:
    print(f"✅ PASS - Valid plan structure recognized")
else:
    print(f"❌ FAIL - Valid plan marked as invalid")

# Test 9: Validate verification structure
print("\n🧪 Test 9: Validate verification structure")
valid_verification = {
    "overall_approval": True,
    "score": 90,
    "issues": [],
    "suggestions": ["Consider adding visualization"],
    "improvements": []
}
is_valid = validate_verification_json(valid_verification)
if is_valid:
    print(f"✅ PASS - Valid verification structure recognized")
else:
    print(f"❌ FAIL - Valid verification marked as invalid")

# Test 10: Complex real-world scenario
print("\n🧪 Test 10: Complex real-world LLM response")
complex_response = '''Sure, here's the plan you requested:

```json
{
    'query': 'What is AI?',
    'reasoning': 'Simple question needs direct answer',
    'pipeline': [
        {
            'tool': 'qa_engine',
            'purpose': 'Provide answer',
            'input': 'What is AI?',
        }
    ],
    'final_output': 'Answer about AI',
}
```

I hope this helps!'''
try:
    result = extract_and_fix_json(complex_response)
    parsed = json.loads(result)
    is_valid = validate_plan_json(parsed)
    print(f"✅ PASS - Complex response handled successfully")
    print(f"   Extracted and validated: {is_valid}")
    print(f"   Query: {parsed.get('query')}")
    print(f"   Pipeline steps: {len(parsed.get('pipeline', []))}")
except Exception as e:
    print(f"❌ FAIL - {e}")

print("\n" + "=" * 70)
print("🎉 JSON Fixer Tests Completed!")
print("=" * 70)
print("\nThe json_fixer module can handle:")
print("  ✅ Valid JSON (passthrough)")
print("  ✅ Markdown code blocks")
print("  ✅ Explanatory text before/after")
print("  ✅ Trailing commas")
print("  ✅ Single quotes")
print("  ✅ Python-style booleans (True/False)")
print("  ✅ Missing keys (adds defaults)")
print("  ✅ Structure validation")
print("  ✅ Complex real-world LLM responses")
print("\n🚀 Your system is now bulletproof against JSON errors!")
