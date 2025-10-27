# Quick Start: Scientific Research Mode 🔬

## ✅ What Was Added

**3 powerful research tools integrated into your system:**

1. **Semantic Scholar** - 200M+ papers, all disciplines, with citation metrics
2. **PubMed Search** - 35M+ biomedical articles
3. **PDF Parser** - Extract text from research papers

## 🚀 Setup (5 minutes)

### Step 1: Install PDF Libraries

```bash
pip install PyPDF2 pdfplumber
```

### Step 2: Test Tools

```bash
python test_research_tools.py
```

**Expected output:**
```
✅ Semantic Scholar is working!
✅ PubMed is working!
✅ PDF Parser is working!
✅ Orchestrator loaded successfully!
🎉 All tests passed! Research tools are ready to use.
```

### Step 3: Start System

```bash
python main.py
```

## 🎯 Try These Queries

### Example 1: Simple Research Query
```
Find papers on quantum computing applications
```

**What happens:**
- Semantic Scholar finds highly-cited papers
- ArXiv finds recent preprints
- QA Engine synthesizes comprehensive answer

---

### Example 2: Medical Research
```
Research AI applications in cancer detection. Find clinical studies 
from PubMed and compare with academic papers from Semantic Scholar.
```

**What happens:**
- PubMed finds clinical studies
- Semantic Scholar finds ML/AI papers
- Both perspectives synthesized
- Citations provided

---

### Example 3: Comprehensive Literature Review
```
Conduct a literature review on CRISPR gene editing safety. Find papers 
from multiple sources, identify top researchers, analyze citation impact, 
and provide comprehensive analysis.
```

**What happens:**
- Semantic Scholar: papers with citation counts
- PubMed: medical/clinical studies
- News: recent developments
- Wikipedia: background
- QA Engine: comprehensive synthesis
- Data Plotter: visualization
- All sources shown for verification

---

## 📊 What Changed

### Files Added:
```
tools/semantic_scholar.py      - New research tool
tools/pubmed_search.py         - New biomedical tool
tools/pdf_parser.py            - New PDF tool
test_research_tools.py         - Verification script
SCIENTIFIC_RESEARCH_SETUP.md   - Full documentation
```

### Files Modified:
```
tools_description.json         - Added 3 new tool descriptions
orchestrator.py               - Registered new tools (line 57)
```

### No Changes Needed:
- Existing tools still work
- QA engine already receives context
- Synthesizer already handles multiple sources
- Everything backwards compatible

## 🎓 Tool Selection Logic

The planner will automatically choose appropriate tools based on your query:

**For "quantum computing":**
- ✓ ArXiv (physics/CS)
- ✓ Semantic Scholar (broader coverage)
- ✓ Wikipedia (background)
- ✓ QA Engine (synthesis)

**For "cancer treatment AI":**
- ✓ PubMed (clinical studies)
- ✓ Semantic Scholar (AI papers)
- ✓ News (recent breakthroughs)
- ✓ QA Engine (synthesis)

**For "analyze paper.pdf":**
- ✓ PDF Parser (extract text)
- ✓ Semantic Scholar (find related papers)
- ✓ QA Engine (compare and analyze)

## 💡 Pro Tips

### Tip 1: Use Multiple Sources
```
"Research [topic] using Semantic Scholar, PubMed, and ArXiv"
```
Gets comprehensive multi-source results.

### Tip 2: Request Citation Analysis
```
"Find highly-cited papers on [topic] and identify key researchers"
```
Semantic Scholar provides citation metrics!

### Tip 3: Medical + AI Queries
```
"Research AI in [medical application] from both ML and clinical perspectives"
```
Gets PubMed + Semantic Scholar automatically.

### Tip 4: Verify Everything
All sources are shown below the answer - cross-check any claims!

## ⚡ Expected Performance

- **Query time:** 20-40 seconds (multiple tools + synthesis)
- **Semantic Scholar:** ~2-3 seconds
- **PubMed:** ~3-5 seconds
- **QA synthesis:** ~5-10 seconds

## 🔍 Example Full Output

**Query:** "Research machine learning in drug discovery"

**You'll see:**

```
## 💡 Comprehensive Analysis

### Overview
Machine learning has revolutionized drug discovery by enabling...
[1500+ words of detailed analysis]

### Key Papers
According to Semantic Scholar paper "Deep Learning for Drug Discovery" 
(Chen et al., 2023, 1,234 citations)...

According to PubMed clinical study "ML-guided Drug Design" 
(PMID: 12345678, Nature Medicine, 2024)...

[Continues with specific details from actual papers]

---

## 📚 Factual Sources Used

### 🎓 Semantic Scholar Results
Found 10 highly-cited papers:

1. **Deep Learning for Drug Discovery**
   - Authors: Chen, Wang, Zhang et al.
   - Year: 2023
   - Citations: 1,234 total, 234 influential
   - Impact Score: 19.0% influential
   - URL: https://semanticscholar.org/...

[... 9 more papers ...]

### 🏥 PubMed Results
Found 10 biomedical articles:

1. **ML-Guided Drug Design in Cancer Therapy**
   - Authors: Smith J, Johnson K, Brown M
   - Journal: Nature Medicine
   - Year: 2024
   - PubMed ID: 12345678
   - URL: https://pubmed.ncbi.nlm.nih.gov/12345678/

[... 9 more articles ...]

---

## 📊 Generated Resources
📈 Chart: output/bar_chart_research_metrics.png
```

## 📖 Full Documentation

See `SCIENTIFIC_RESEARCH_SETUP.md` for:
- Detailed tool documentation
- API limits and quotas
- Advanced usage examples
- Troubleshooting guide
- Power user tips

## ✅ Verification Checklist

Before starting:
- [ ] Installed PyPDF2: `pip install PyPDF2`
- [ ] Installed pdfplumber: `pip install pdfplumber`
- [ ] Ran test script: `python test_research_tools.py`
- [ ] All tests passed ✅

Ready to use:
- [ ] Started system: `python main.py`
- [ ] Tested simple query
- [ ] Checked output has multiple sources
- [ ] Verified citations present

## 🎉 You're Ready!

Your DualMind Orchestrator is now a **professional-grade Research Assistant**!

**Start with:**
```
Research [your favorite topic] comprehensively
```

**And watch it:**
1. Search 200M+ papers (Semantic Scholar)
2. Find medical studies (PubMed)
3. Get recent preprints (ArXiv)
4. Provide background (Wikipedia)
5. Synthesize everything (QA Engine)
6. Show all sources for verification
7. Create visualizations (Data Plotter)

**All factually grounded and fully cited!** 🚀

---

## 🆘 Need Help?

**Common Issues:**

1. **"Import Error"**
   - Run: `pip install PyPDF2 pdfplumber`

2. **"No results from Semantic Scholar"**
   - Check internet connection
   - Try broader search terms

3. **"PubMed timeout"**
   - Query might be too complex
   - Try simpler search terms

4. **"Tools not found"**
   - Run: `python test_research_tools.py`
   - Check all files are in `tools/` directory

**Still stuck?** Check `SCIENTIFIC_RESEARCH_SETUP.md` for detailed troubleshooting.

---

**Happy Researching! 🎓📚🔬**
