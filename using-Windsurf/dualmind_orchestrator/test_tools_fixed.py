"""
Test script to verify the fixed tools (data_plotter and document_writer)
"""

import sys
import json
sys.path.append('.')

from tools.data_plotter import data_plotter_tool
from tools.document_writer import document_writer_tool

print("=" * 60)
print("Testing Fixed Tools - Data Plotter & Document Writer")
print("=" * 60)

# Test 1: Data Plotter with valid JSON
print("\n🧪 Test 1: Data Plotter with VALID JSON")
valid_json = json.dumps({"Research": 45, "Development": 30, "Testing": 25})
result = data_plotter_tool(valid_json, "bar", "Project Distribution")
print(f"Result: {result}")
if "successfully" in result:
    print("✅ PASS")
else:
    print("❌ FAIL")

# Test 2: Data Plotter with invalid JSON (should handle gracefully)
print("\n🧪 Test 2: Data Plotter with INVALID JSON (should fallback)")
invalid_json = "This is not JSON at all"
result = data_plotter_tool(invalid_json, "bar", "Fallback Chart")
print(f"Result: {result}")
if "successfully" in result or "created" in result:
    print("✅ PASS - Gracefully handled")
else:
    print("❌ FAIL")

# Test 3: Data Plotter with empty string
print("\n🧪 Test 3: Data Plotter with EMPTY STRING (should fallback)")
result = data_plotter_tool("", "pie", "Empty Data")
print(f"Result: {result}")
if "successfully" in result or "created" in result:
    print("✅ PASS - Gracefully handled")
else:
    print("❌ FAIL")

# Test 4: Document Writer with valid JSON
print("\n🧪 Test 4: Document Writer with VALID JSON")
valid_content = json.dumps({
    "sections": [
        {"title": "Introduction", "content": "This is a test report."},
        {"title": "Findings", "content": "All systems operational."}
    ]
})
result = document_writer_tool(valid_content, "Test Report")
print(f"Result: {result}")
if "successfully" in result:
    print("✅ PASS")
else:
    print("❌ FAIL")

# Test 5: Document Writer with invalid JSON (should handle gracefully)
print("\n🧪 Test 5: Document Writer with INVALID JSON (should fallback)")
invalid_content = "Just some plain text content"
result = document_writer_tool(invalid_content, "Fallback Report")
print(f"Result: {result}")
if "successfully" in result or "created" in result:
    print("✅ PASS - Gracefully handled")
else:
    print("❌ FAIL")

# Test 6: Document Writer with partial JSON (missing sections)
print("\n🧪 Test 6: Document Writer with PARTIAL JSON (should auto-fix)")
partial_json = json.dumps({"title": "My Title", "content": "Some content"})
result = document_writer_tool(partial_json, "Partial Report")
print(f"Result: {result}")
if "successfully" in result or "created" in result:
    print("✅ PASS - Auto-fixed structure")
else:
    print("❌ FAIL")

print("\n" + "=" * 60)
print("🎉 All Tool Tests Completed!")
print("=" * 60)
print("\nCheck the 'output/' directory for generated files:")
print("  - Bar charts (PNG files)")
print("  - Pie charts (PNG files)")
print("  - PDF reports")
