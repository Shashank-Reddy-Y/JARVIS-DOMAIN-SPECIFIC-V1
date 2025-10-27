"""
Test script for new scientific research tools
Run this to verify all tools are working correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_semantic_scholar():
    """Test Semantic Scholar tool"""
    print("\n" + "="*60)
    print("Testing Semantic Scholar Tool")
    print("="*60)
    
    try:
        from tools.semantic_scholar import semantic_scholar_tool
        
        result = semantic_scholar_tool("machine learning")
        print("\n✅ Semantic Scholar is working!")
        print(f"Result length: {len(result)} characters")
        print("\nFirst 500 characters:")
        print(result[:500] + "...\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Semantic Scholar failed: {e}")
        return False

def test_pubmed():
    """Test PubMed tool"""
    print("\n" + "="*60)
    print("Testing PubMed Tool")
    print("="*60)
    
    try:
        from tools.pubmed_search import pubmed_tool
        
        result = pubmed_tool("cancer immunotherapy")
        print("\n✅ PubMed is working!")
        print(f"Result length: {len(result)} characters")
        print("\nFirst 500 characters:")
        print(result[:500] + "...\n")
        return True
        
    except Exception as e:
        print(f"\n❌ PubMed failed: {e}")
        return False

def test_pdf_parser():
    """Test PDF Parser tool"""
    print("\n" + "="*60)
    print("Testing PDF Parser Tool")
    print("="*60)
    
    try:
        from tools.pdf_parser import pdf_parser_tool
        
        # Test with non-existent file (should handle gracefully)
        result = pdf_parser_tool("test.pdf")
        print("\n✅ PDF Parser is working!")
        print(f"Result length: {len(result)} characters")
        print("\nResult:")
        print(result[:500] + "...\n")
        
        # Check if libraries are installed
        from tools.pdf_parser import PDFParserTool
        tool = PDFParserTool()
        if tool.has_pypdf2:
            print("  ✓ PyPDF2 is installed")
        else:
            print("  ⚠ PyPDF2 not installed (install with: pip install PyPDF2)")
            
        if tool.has_pdfplumber:
            print("  ✓ pdfplumber is installed")
        else:
            print("  ⚠ pdfplumber not installed (install with: pip install pdfplumber)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ PDF Parser failed: {e}")
        return False

def test_orchestrator_integration():
    """Test that orchestrator can load all tools"""
    print("\n" + "="*60)
    print("Testing Orchestrator Integration")
    print("="*60)
    
    try:
        from orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        print(f"\n✅ Orchestrator loaded successfully!")
        print(f"Total tools loaded: {len(orch.tools)}")
        print("\nAvailable tools:")
        for tool_name in sorted(orch.tools.keys()):
            print(f"  ✓ {tool_name}")
        
        # Check for new tools
        expected_new_tools = ['semantic_scholar', 'pubmed_search', 'pdf_parser']
        all_present = True
        print("\nNew research tools:")
        for tool in expected_new_tools:
            if tool in orch.tools:
                print(f"  ✓ {tool} - registered")
            else:
                print(f"  ✗ {tool} - NOT FOUND")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"\n❌ Orchestrator integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# DualMind Research Tools - Verification")
    print("#"*60)
    
    results = {
        "Semantic Scholar": test_semantic_scholar(),
        "PubMed": test_pubmed(),
        "PDF Parser": test_pdf_parser(),
        "Orchestrator": test_orchestrator_integration()
    }
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All tests passed! Research tools are ready to use.")
        print("\nNext steps:")
        print("1. Install PDF libraries: pip install PyPDF2 pdfplumber")
        print("2. Start the system: python main.py")
        print("3. Try a research query!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\nCommon fixes:")
        print("- Ensure internet connection is active")
        print("- Install missing libraries: pip install PyPDF2 pdfplumber")
        print("- Check that all tool files are in the tools/ directory")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
