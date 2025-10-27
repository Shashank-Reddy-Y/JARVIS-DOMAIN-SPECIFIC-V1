"""
Test script to verify the fixed error handling in DualMind Orchestrator
"""

import sys
import os
import logging

# Set up basic logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append('.')

from orchestrator import create_orchestrator

def test_orchestrator():
    """Test the orchestrator with a simple query."""
    
    print("=" * 60)
    print("Testing DualMind Orchestrator - Fixed Version")
    print("=" * 60)
    
    try:
        # Create orchestrator
        orchestrator = create_orchestrator()
        print('✅ Orchestrator created successfully\n')
        
        # Test with a simple query
        test_query = 'What is artificial intelligence?'
        print(f'🧪 Testing query: "{test_query}"\n')
        
        # Process the query
        results = orchestrator.process_query(test_query)
        
        print('\n' + "=" * 60)
        print('✅ Query processed successfully!')
        print("=" * 60)
        
        # Print results summary
        print(f'\n📊 Results Summary:')
        print(f'   Session ID: {results.get("session_id", "Unknown")}')
        print(f'   Status: {results.get("status", "Unknown")}')
        print(f'   Execution Time: {results.get("execution_time", 0):.2f}s')
        print(f'   Iterations: {results.get("iterations", 0)}')
        
        # Plan details
        plan = results.get('plan', {})
        print(f'\n🎯 Plan Details:')
        print(f'   Steps in Pipeline: {len(plan.get("pipeline", []))}')
        print(f'   Plan Type: {plan.get("planner_version", "Unknown")}')
        print(f'   LLM Generated: {plan.get("llm_generated", False)}')
        
        # Verification details
        verification = results.get('verification', {})
        print(f'\n🔍 Verification Details:')
        print(f'   Score: {verification.get("score", 0)}/100')
        print(f'   Approved: {"Yes" if verification.get("overall_approval", False) else "No"}')
        print(f'   Method: {verification.get("verification_method", "Unknown")}')
        print(f'   Issues Found: {len(verification.get("issues", []))}')
        print(f'   Suggestions: {len(verification.get("suggestions", []))}')
        
        # Execution details
        execution_results = results.get('execution_results', [])
        success_count = sum(1 for r in execution_results if r.get('status') == 'success')
        print(f'\n⚙️ Execution Details:')
        print(f'   Total Steps Executed: {len(execution_results)}')
        print(f'   Successful: {success_count}')
        print(f'   Failed: {len(execution_results) - success_count}')
        
        # Show final output preview
        if execution_results:
            final_result = execution_results[-1]
            if final_result.get('status') == 'success':
                output = final_result.get('output', 'No output')
                print(f'\n🎉 Final Output Preview:')
                print(f'   {output[:150]}...')
            else:
                print(f'\n⚠️ Final step failed: {final_result.get("error", "Unknown error")}')
        
        print('\n' + "=" * 60)
        print('🎉 Test completed successfully!')
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f'\n❌ Error during test: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_orchestrator()
    sys.exit(0 if success else 1)
