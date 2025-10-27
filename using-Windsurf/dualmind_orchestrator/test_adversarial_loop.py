#!/usr/bin/env python3
"""
Test script for the adversarial loop implementation.
Tests that the planner-verifier loop actually iterates and improves plans.
"""

import sys
import logging
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
    """Test that the adversarial loop works correctly."""
    
    logger.info("="*80)
    logger.info("TESTING ADVERSARIAL LOOP IMPLEMENTATION")
    logger.info("="*80)
    
    try:
        from orchestrator import create_orchestrator
        
        # Create orchestrator
        logger.info("\n1️⃣ Creating orchestrator...")
        orchestrator = create_orchestrator()
        logger.info("✅ Orchestrator created successfully")
        
        # Test query that should trigger multiple iterations
        test_query = "What is quantum computing?"
        
        logger.info(f"\n2️⃣ Processing test query: '{test_query}'")
        logger.info("Max iterations: 3")
        logger.info("Expected: Planner creates plan → Verifier critiques → Planner improves → Loop continues")
        
        # Process query
        results = orchestrator.process_query(test_query, max_iterations=3)
        
        # Analyze results
        logger.info("\n3️⃣ Analyzing results...")
        logger.info("-"*80)
        
        # Check if adversarial loop is active
        adversarial_active = results.get('adversarial_loop_active', False)
        logger.info(f"Adversarial loop active: {adversarial_active}")
        
        # Check iterations
        iterations = results.get('iterations', 0)
        logger.info(f"Total iterations: {iterations}")
        
        # Check plan history
        plan_history = results.get('plan_history', [])
        logger.info(f"Plan history entries: {len(plan_history)}")
        
        if len(plan_history) > 1:
            logger.info("\n📊 PLAN EVOLUTION:")
            for i, entry in enumerate(plan_history):
                iter_num = entry.get('iteration', 0)
                score = entry.get('score', 0)
                approved = entry.get('approved', 'N/A')
                plan = entry.get('plan', {})
                pipeline = plan.get('pipeline', [])
                
                if iter_num == 0:
                    logger.info(f"  Initial Plan: {len(pipeline)} steps")
                else:
                    status = "✅ APPROVED" if approved else "❌ REJECTED"
                    logger.info(f"  Iteration {iter_num}: Score {score}/100 {status}")
                    logger.info(f"    Pipeline: {len(pipeline)} steps")
                    
                    # Show tools used
                    tools = [step.get('tool', 'unknown') for step in pipeline]
                    logger.info(f"    Tools: {', '.join(tools)}")
                    
                    # Show revision number if present
                    revision = plan.get('revision_number', 0)
                    if revision > 0:
                        logger.info(f"    Revision: {revision}")
            
            # Calculate improvement
            if len(plan_history) > 2:
                first_score = plan_history[1].get('score', 0)
                last_score = plan_history[-1].get('score', 0)
                improvement = last_score - first_score
                
                logger.info(f"\n📈 SCORE IMPROVEMENT:")
                logger.info(f"  First iteration: {first_score}/100")
                logger.info(f"  Last iteration: {last_score}/100")
                logger.info(f"  Improvement: {'+' if improvement >= 0 else ''}{improvement} points")
        
        # Check final status
        status = results.get('status', 'Unknown')
        final_score = results.get('final_plan_score', 0)
        plan_approved = results.get('plan_approved', False)
        
        logger.info(f"\n4️⃣ Final Status:")
        logger.info(f"Status: {status}")
        logger.info(f"Final Score: {final_score}/100")
        logger.info(f"Plan Approved: {'✅ YES' if plan_approved else '❌ NO'}")
        
        # Check if execution happened
        execution_results = results.get('execution_results', [])
        if execution_results:
            success_count = sum(1 for r in execution_results if r.get('status') == 'success')
            logger.info(f"Tools executed: {len(execution_results)} ({success_count} successful)")
        
        # Verification
        logger.info("\n5️⃣ Verification Checks:")
        
        checks = []
        
        # Check 1: Did multiple iterations occur?
        if iterations > 1:
            checks.append(("✅", "Multiple iterations occurred"))
        else:
            checks.append(("⚠️", "Only 1 iteration (plan approved immediately or loop failed)"))
        
        # Check 2: Was plan history tracked?
        if len(plan_history) > 1:
            checks.append(("✅", "Plan history tracked across iterations"))
        else:
            checks.append(("❌", "Plan history not tracked properly"))
        
        # Check 3: Did plans evolve?
        if len(plan_history) > 1:
            initial_pipeline = plan_history[0].get('plan', {}).get('pipeline', [])
            final_pipeline = plan_history[-1].get('plan', {}).get('pipeline', [])
            
            if initial_pipeline != final_pipeline:
                checks.append(("✅", "Plans evolved through iterations"))
            else:
                checks.append(("⚠️", "Plans did not change between iterations"))
        
        # Check 4: Was feedback used?
        final_plan = results.get('plan', {})
        revision_num = final_plan.get('revision_number', 0)
        if revision_num > 0:
            checks.append(("✅", f"Plan revised {revision_num} time(s) based on feedback"))
        else:
            checks.append(("⚠️", "No plan revisions detected"))
        
        # Check 5: Is adversarial loop active?
        if adversarial_active:
            checks.append(("✅", "Adversarial loop is active"))
        else:
            checks.append(("❌", "Adversarial loop not active"))
        
        # Print checks
        for icon, message in checks:
            logger.info(f"{icon} {message}")
        
        # Overall assessment
        logger.info("\n"+"="*80)
        passed_checks = sum(1 for icon, _ in checks if icon == "✅")
        total_checks = len(checks)
        
        if passed_checks == total_checks:
            logger.info("🎉 ALL CHECKS PASSED - Adversarial loop is working perfectly!")
        elif passed_checks >= total_checks * 0.6:
            logger.info(f"⚠️ PARTIAL SUCCESS - {passed_checks}/{total_checks} checks passed")
        else:
            logger.info(f"❌ TESTS FAILED - Only {passed_checks}/{total_checks} checks passed")
        
        logger.info("="*80)
        
        return passed_checks == total_checks
        
    except Exception as e:
        logger.error(f"❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_plan_rejection():
    """Test that plans with low scores are rejected properly."""
    
    logger.info("\n\n")
    logger.info("="*80)
    logger.info("TESTING PLAN REJECTION MECHANISM")
    logger.info("="*80)
    
    try:
        from orchestrator import create_orchestrator
        from planner import create_planner
        from verifier import create_verifier
        
        # Create components
        planner = create_planner()
        verifier = create_verifier()
        
        # Create a deliberately bad plan
        bad_plan = {
            "query": "Test query",
            "reasoning": "This is a test",
            "pipeline": [],  # Empty pipeline - should be rejected
            "final_output": "Nothing"
        }
        
        logger.info("\n1️⃣ Testing with empty pipeline (should be rejected)...")
        verification = verifier.verify_plan(bad_plan)
        score = verification.get('score', 0)
        approved = verification.get('overall_approval', False)
        
        logger.info(f"Score: {score}/100")
        logger.info(f"Approved: {'Yes' if approved else 'No'}")
        
        if score < 50:
            logger.info("✅ Bad plan correctly scored low")
        else:
            logger.info("⚠️ Bad plan should have lower score")
        
        if not approved:
            logger.info("✅ Bad plan correctly rejected")
        else:
            logger.info("❌ Bad plan should have been rejected")
        
        logger.info("="*80)
        
        return not approved and score < 50
        
    except Exception as e:
        logger.error(f"❌ ERROR during rejection testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    
    logger.info("\n🧪 STARTING ADVERSARIAL LOOP TESTS\n")
    
    # Test 1: Adversarial loop
    test1_passed = test_adversarial_loop()
    
    # Test 2: Plan rejection
    test2_passed = test_plan_rejection()
    
    # Summary
    logger.info("\n\n")
    logger.info("="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"Test 1 (Adversarial Loop): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    logger.info(f"Test 2 (Plan Rejection): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    logger.info("="*80)
    
    if test1_passed and test2_passed:
        logger.info("\n🎉 ALL TESTS PASSED - Implementation is correct!")
        return 0
    else:
        logger.info("\n⚠️ SOME TESTS FAILED - Review implementation")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
