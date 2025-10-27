import sys
sys.path.append('c:\\\\CFiles\\\\PS3-1domain\\\\using-Windsurf\\\\dualmind_orchestrator')
from llm_client import llm_client

# Test a simple LLM call
response = llm_client.call_llm('Test prompt', 'Return only JSON: {\"test\": \"value\"}', 100)
print('LLM Response:', repr(response))
print('Length:', len(response) if response else 0)
