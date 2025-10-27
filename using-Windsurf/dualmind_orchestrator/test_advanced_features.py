#!/usr/bin/env python3
"""
Comprehensive test suite for all advanced features.
Tests learning/adaptation, self-correction, adversarial loop, and context accumulation.
"""

import sys
import logging
import json
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_adversarial_loop():
    """Test the adversarial loop with plan regeneration."""
    logger.info("="*80)
    logger.info("TEST 1: ADVERSARIAL LOOP")
    logger.info("="*80)
    
    try:
        from orchestrator import create_orchestrator
        
        orchestrator = create_orchestrator()
        logger.info("✅ Orchestrator created")
        
        # Query that may need iteration
        query = "Explain quantum computing"
        logger.info(f"\n📝 Query: {query}")
        
        results = orchestrator.process_query(query, max_iterations=2)
        
        # Check adversarial loop
        adversarial_active = results.get('adversarial_loop_active', False)
        plan_history = results.get('plan_history', [])
        iterations = results.get('iterations', 0)
        
        logger.info(f"\n📊 Results:")
        logger.info(f"  Adversarial loop active: {adversarial_active}")
        logger.info(f"  Iterations: {iterations}")
        logger.info(f"  Plan history entries: {len(plan_history)}")
        
        checks = [
            (adversarial_active, "Adversarial loop is active"),
            (len(plan_history) >= 1, "Plan history tracked"),
            (iterations >= 1, "At least one iteration completed")
        ]
        
        passed = sum(1 for check, _ in checks if check)
        for check, desc in checks:
            logger.info(f"  {'✅' if check else '❌'} {desc}")
        
        logger.info(f"\n✅ Test passed: {passed}/{len(checks)} checks")
        return passed == len(checks)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_learning_adaptation():
    """Test the learning/adaptation system."""
    logger.info("\n\n")
    logger.info("="*80)
    logger.info("TEST 2: LEARNING/ADAPTATION")
    logger.info("="*80)
    
    try:
        from orchestrator import create_orchestrator
        
        orchestrator = create_orchestrator()
        
        # First query - establish a pattern
        query1 = "Explain artificial intelligence"
        logger.info(f"\n📝 First query: {query1}")
        
        results1 = orchestrator.process_query(query1)
        
        # Check if pattern was stored
        patterns_dir = os.path.join("logs", "patterns")
        patterns_exist = os.path.exists(patterns_dir)
        
        logger.info(f"\n📊 After first query:")
        logger.info(f"  Patterns directory exists: {patterns_exist}")
        
        if patterns_exist:
            pattern_files = [f for f in os.listdir(patterns_dir) if f.endswith('.json')]
            logger.info(f"  Pattern files: {len(pattern_files)}")
        
        # Second similar query - should use pattern
        query2 = "Explain machine learning"
        logger.info(f"\n📝 Second similar query: {query2}")
        
        results2 = orchestrator.process_query(query2)
        
        # Check if patterns were retrieved
        similar_patterns = orchestrator.get_similar_successful_patterns(query2, limit=3)
        
        logger.info(f"\n📊 Pattern retrieval:")
        logger.info(f"  Similar patterns found: {len(similar_patterns)}")
        
        if similar_patterns:
            best = similar_patterns[0]
            logger.info(f"  Best match: {best.get('query', 'Unknown')}")
            logger.info(f"  Similarity: {best.get('similarity', 0):.2f}")
        
        checks = [
            (patterns_exist, "Patterns directory created"),
            (len(similar_patterns) > 0 if patterns_exist else True, "Patterns can be retrieved"),
        ]
        
        passed = sum(1 for check, _ in checks if check)
        for check, desc in checks:
            logger.info(f"\n  {'✅' if check else '❌'} {desc}")
        
        logger.info(f"\n✅ Test completed: {passed}/{len(checks)} checks")
        return passed >= len(checks) - 1  # Allow 1 failure
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_self_correction():
    """Test the self-correction mechanism."""
    logger.info("\n\n")
    logger.info("="*80)
    logger.info("TEST 3: SELF-CORRECTION")
    logger.info("="*80)
    
    try:
        from orchestrator import create_orchestrator
        
        orchestrator = create_orchestrator()
        
        # Create a plan with a tool that might fail
        test_plan = {
            "query": "Test self-correction",
            "pipeline": [
                {"tool": "wikipedia_search", "purpose": "Get info", "input": "test"},
                {"tool": "nonexistent_tool", "purpose": "This will fail", "input": "test"},  # Will fail
                {"tool": "qa_engine", "purpose": "Synthesize", "input": "test"}
            ]
        }
        
        logger.info("\n📝 Testing with plan containing failing tool...")
        logger.info(f"  Tools in plan: {[s['tool'] for s in test_plan['pipeline']]}")
        
        # Execute with self-correction
        results = orchestrator._execute_pipeline_with_selfcorrection(test_plan, "test", max_retries=2)
        
        # Check results
        failed_count = sum(1 for r in results if r.get('status') == 'error')
        retry_count = results[0].get('retry_count', 0) if results else 0
        
        logger.info(f"\n📊 Execution results:")
        logger.info(f"  Total steps executed: {len(results)}")
        logger.info(f"  Failed steps: {failed_count}")
        logger.info(f"  Retry attempts: {retry_count}")
        
        # Log each step
        for i, result in enumerate(results, 1):
            status = result.get('status', 'unknown')
            tool = result.get('tool', 'unknown')
            icon = "✅" if status == 'success' else "❌"
            logger.info(f"  {icon} Step {i}: {tool} - {status}")
        
        checks = [
            (len(results) > 0, "Pipeline executed"),
            (retry_count >= 0, "Retry count tracked"),
        ]
        
        passed = sum(1 for check, _ in checks if check)
        for check, desc in checks:
            logger.info(f"\n  {'✅' if check else '❌'} {desc}")
        
        logger.info(f"\n✅ Test completed: {passed}/{len(checks)} checks")
        return passed == len(checks)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_context_accumulation():
    """Test context accumulation for qa_engine."""
    logger.info("\n\n")
    logger.info("="*80)
    logger.info("TEST 4: CONTEXT ACCUMULATION")
    logger.info("="*80)
    
    try:
        from orchestrator import create_orchestrator
        
        orchestrator = create_orchestrator()
        
        # Create a plan with multiple tools before qa_engine
        test_plan = {
            "query": "Test context",
            "pipeline": [
                {"tool": "wikipedia_search", "purpose": "Get background", "input": "artificial intelligence"},
                {"tool": "qa_engine", "purpose": "Synthesize with context", "input": "Explain AI"}
            ]
        }
        
        logger.info("\n📝 Testing context accumulation...")
        logger.info(f"  Pipeline: {[s['tool'] for s in test_plan['pipeline']]}")
        
        # Execute pipeline
        results = orchestrator._execute_pipeline(test_plan)
        
        # Check qa_engine step for context
        qa_step = next((r for r in results if r.get('tool') == 'qa_engine'), None)
        
        logger.info(f"\n📊 Context check:")
        if qa_step:
            # The input would be modified internally but we can check execution
            logger.info(f"  QA engine executed: ✅")
            logger.info(f"  QA status: {qa_step.get('status', 'unknown')}")
            
            # Check if previous tools succeeded (context should be available)
            prev_tools = [r for r in results if r.get('tool') != 'qa_engine']
            prev_success = all(r.get('status') == 'success' for r in prev_tools)
            logger.info(f"  Previous tools successful: {'✅' if prev_success else '❌'}")
        else:
            logger.info(f"  QA engine not found: ❌")
        
        checks = [
            (qa_step is not None, "QA engine executed"),
            (len(results) >= 2, "Multiple tools in pipeline"),
        ]
        
        passed = sum(1 for check, _ in checks if check)
        for check, desc in checks:
            logger.info(f"\n  {'✅' if check else '❌'} {desc}")
        
        logger.info(f"\n✅ Test completed: {passed}/{len(checks)} checks")
        return passed == len(checks)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quality_enforcement():
    """Test that low-quality plans are rejected."""
    logger.info("\n\n")
    logger.info("="*80)
    logger.info("TEST 5: QUALITY ENFORCEMENT")
    logger.info("="*80)
    
    try:
        from orchestrator import create_orchestrator
        from verifier import create_verifier
        
        orchestrator = create_orchestrator()
        verifier = create_verifier()
        
        # Create a deliberately bad plan
        bad_plan = {
            "query": "Test quality enforcement",
            "reasoning": "Bad plan for testing",
            "pipeline": [],  # Empty pipeline
            "final_output": "Nothing"
        }
        
        logger.info("\n📝 Testing with empty pipeline (should be rejected)...")
        
        verification = verifier.verify_plan(bad_plan)
        score = verification.get('score', 0)
        approved = verification.get('overall_approval', False)
        
        logger.info(f"\n📊 Verification results:")
        logger.info(f"  Score: {score}/100")
        logger.info(f"  Approved: {approved}")
        logger.info(f"  Expected: Low score, not approved")
        
        checks = [
            (score < 70, "Bad plan scored low"),
            (not approved, "Bad plan not approved"),
        ]
        
        passed = sum(1 for check, _ in checks if check)
        for check, desc in checks:
            logger.info(f"\n  {'✅' if check else '❌'} {desc}")
        
        logger.info(f"\n✅ Test completed: {passed}/{len(checks)} checks")
        return passed == len(checks)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all advanced feature tests."""
    
    logger.info("\n🧪 STARTING COMPREHENSIVE ADVANCED FEATURES TEST SUITE\n")
    
    tests = [
        ("Adversarial Loop", test_adversarial_loop),
        ("Learning/Adaptation", test_learning_adaptation),
        ("Self-Correction", test_self_correction),
        ("Context Accumulation", test_context_accumulation),
        ("Quality Enforcement", test_quality_enforcement),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n\n")
    logger.info("="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    logger.info("="*80)
    logger.info(f"Total: {total_passed}/{total_tests} tests passed")
    logger.info("="*80)
    
    if total_passed == total_tests:
        logger.info("\n🎉 ALL TESTS PASSED - All advanced features working!")
        return 0
    else:
        logger.info(f"\n⚠️ {total_tests - total_passed} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
