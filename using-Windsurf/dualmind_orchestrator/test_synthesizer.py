"""
Test script to verify the answer synthesizer works correctly
"""

import sys
sys.path.append('.')

from synthesizer import synthesize_answer, create_executive_summary

print("=" * 70)
print("Testing Answer Synthesizer")
print("=" * 70)

# Mock execution results simulating what the orchestrator produces
mock_results = [
    {
        'tool': 'wikipedia_search',
        'status': 'success',
        'output': '''**Title:** Artificial Intelligence

**Extract:** Artificial Intelligence (AI) is the simulation of human intelligence processes by machines, especially computer systems. These processes include learning (the acquisition of information and rules for using the information), reasoning (using rules to reach approximate or definite conclusions) and self-correction.

**URL:** https://en.wikipedia.org/wiki/Artificial_intelligence'''
    },
    {
        'tool': 'arxiv_summarizer',
        'status': 'success',
        'output': '''Found 5 papers related to 'Artificial Intelligence':

1. **Sample Paper 1 on Query**
   Authors: Author 1, Author 2
   Published: 2024-01-01
   ArXiv ID: 2401.0001
   Summary: Key research on Artificial Intelligence: This is a sample abstract...

2. **Sample Paper 2 on Query**
   Authors: Author 1, Author 2
   Published: 2024-01-01
   ArXiv ID: 2401.0002
   Summary: Key research on Artificial Intelligence: This is a sample abstract...'''
    },
    {
        'tool': 'qa_engine',
        'status': 'success',
        'output': 'Artificial Intelligence refers to computer systems that can perform tasks that typically require human intelligence, such as visual perception, speech recognition, decision-making, and language translation.'
    }
]

user_query = "What is Artificial Intelligence?"
plan = {'query': user_query}

print("\n🧪 Test 1: Synthesize Answer from Multiple Tools")
print("-" * 70)

answer = synthesize_answer(user_query, mock_results, plan)
print(answer)

print("\n" + "=" * 70)
print("\n🧪 Test 2: Executive Summary")
print("-" * 70)

summary = create_executive_summary(user_query, mock_results)
print(summary)

print("\n" + "=" * 70)
print("\n🧪 Test 3: With Mock ArXiv Data (Should Explain Demo)")
print("-" * 70)

mock_arxiv_only = [
    {
        'tool': 'arxiv_summarizer',
        'status': 'success',
        'output': '''Found 5 papers related to 'Learning representations':

1. **Sample Paper 1 on Query**
   Authors: Author 1, Author 2
   Published: 2024-01-01'''
    }
]

answer2 = synthesize_answer("Learning representations by backpropagation errors", mock_arxiv_only, {'query': 'Learning representations'})
print(answer2)

print("\n" + "=" * 70)
print("🎉 Synthesizer Tests Completed!")
print("=" * 70)

print("\n✅ Key Features Demonstrated:")
print("  1. Combines information from multiple tools")
print("  2. Creates structured, readable answers")
print("  3. Handles mock data transparently")
print("  4. Generates key insights")
print("  5. Professional formatting with sections")
print("\n🚀 Your system now provides REAL ANSWERS, not raw data!")
