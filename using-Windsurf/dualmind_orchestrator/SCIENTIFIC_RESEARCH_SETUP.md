# Scientific Research Tools - Setup & Usage Guide

## 🎓 Overview

Your DualMind Orchestrator is now enhanced with **3 powerful scientific research tools**, transforming it into a comprehensive **Academic Research Assistant**.

### New Tools Added:

1. **🎓 Semantic Scholar** - 200M+ papers across ALL disciplines
2. **🏥 PubMed Search** - 35M+ biomedical/life sciences articles  
3. **📄 PDF Parser** - Extract text from research papers

Combined with existing tools (ArXiv, Wikipedia, News, QA Engine), you now have **complete research coverage**.

---

## 🚀 Installation

### Step 1: Install Required Dependencies

```bash
# For PDF parsing (choose one or both):
pip install PyPDF2        # Basic PDF text extraction
pip install pdfplumber    # Better quality, handles complex layouts

# Already installed (no changes needed):
# - requests (for Semantic Scholar and PubMed)
# - xml (standard library, for PubMed XML parsing)
```

### Step 2: Verify Installation

```python
# Test Semantic Scholar
from tools.semantic_scholar import semantic_scholar_tool
result = semantic_scholar_tool("machine learning")
print(result)

# Test PubMed
from tools.pubmed_search import pubmed_tool  
result = pubmed_tool("cancer immunotherapy")
print(result)

# Test PDF Parser
from tools.pdf_parser import pdf_parser_tool
result = pdf_parser_tool("path/to/paper.pdf")
print(result)
```

---

## 📚 Tool Details

### 1. Semantic Scholar 🎓

**What it does:** Searches academic papers across ALL disciplines with citation metrics

**Best for:**
- Cross-disciplinary research
- Finding highly-cited papers
- Citation analysis
- Impact assessment
- Any academic field (not just CS/Physics like ArXiv)

**API:**
- **Endpoint:** api.semanticscholar.org
- **Free Tier:** 100 requests per 5 minutes (no API key needed!)
- **Coverage:** 200M+ papers

**Output Includes:**
- Paper title, authors, year
- Full abstract
- Citation count
- Influential citation count
- Impact score (% of citations that are influential)
- Semantic Scholar ID and URL
- Publication venue

**Example Query:**
```python
"quantum computing applications"
"climate change machine learning"  
"CRISPR gene editing"
"neural network optimization"
```

**Sample Output:**
```
### 1. **Attention Is All You Need**

- **Authors**: Vaswani, Shazeer, Parmar et al. (8 total)
- **Year**: 2017
- **Venue**: NeurIPS
- **Citations**: 75,234 total, 12,456 influential
- **Impact Score**: 16.5% influential
- **Semantic Scholar ID**: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- **URL**: https://www.semanticscholar.org/paper/...

**Abstract**: The dominant sequence transduction models are based on 
complex recurrent or convolutional neural networks...
```

---

### 2. PubMed Search 🏥

**What it does:** Searches peer-reviewed biomedical and life sciences literature

**Best for:**
- Medical research
- Drug discovery
- Clinical studies
- Genomics and biology
- Healthcare applications
- Disease research

**API:**
- **Endpoint:** eutils.ncbi.nlm.nih.gov
- **Free Tier:** Unlimited (with rate limiting)
- **Coverage:** 35M+ citations from MEDLINE

**Output Includes:**
- Article title, authors
- Journal name
- Publication year
- PubMed ID (PMID)
- Abstract
- Direct link to PubMed

**Example Query:**
```python
"COVID-19 vaccine efficacy"
"Alzheimer's disease biomarkers"
"cancer immunotherapy"
"diabetes treatment machine learning"
```

**Sample Output:**
```
### 1. **Deep Learning for Early Detection of Diabetic Retinopathy**

- **Authors**: Gulshan V, Peng L, Coram M et al. (12 total)
- **Journal**: JAMA - Journal of the American Medical Association
- **Year**: 2016
- **PubMed ID**: 27898976
- **URL**: https://pubmed.ncbi.nlm.nih.gov/27898976/

**Abstract**: Deep learning algorithms have achieved expert-level 
performance in image classification tasks. We trained a deep convolutional 
neural network...
```

---

### 3. PDF Parser 📄

**What it does:** Extracts full text from PDF research papers

**Best for:**
- Analyzing downloaded papers
- Extracting quotes and references
- Full-text search
- Local document analysis

**Libraries Used:**
- **pdfplumber** (recommended) - Better quality
- **PyPDF2** (fallback) - Simpler, faster

**Output Includes:**
- Full extracted text
- File metadata (size, word count)
- Text preview

**Example Usage:**
```python
# In queries, specify file path:
"Analyze the paper at papers/nature_2024.pdf"
"Extract key findings from downloaded/smith_2023.pdf"
```

**Sample Output:**
```
## 📄 PDF Parsing Results

**File**: nature_2024_ml_climate.pdf
**Size**: 2,458,392 bytes
**Text Length**: 45,678 characters
**Word Count**: 7,234 words

### 📖 Text Preview (first 1000 characters):

Deep Learning for Climate Prediction: A Review

Abstract

Machine learning, particularly deep learning, has emerged as a 
powerful tool for climate prediction and modeling...
```

---

## 🎯 How to Use in Queries

### Example 1: Comprehensive Literature Review

**Query:**
```
Research machine learning applications in drug discovery. Find papers from 
Semantic Scholar and PubMed, compare approaches, identify key researchers, 
and generate a comprehensive literature review.
```

**What happens:**
1. Semantic Scholar finds CS/ML papers on drug discovery
2. PubMed finds biomedical papers on the same topic
3. Wikipedia provides background
4. QA Engine synthesizes everything into comprehensive review
5. Data plotter visualizes paper counts by year/topic

---

### Example 2: Medical Research Analysis

**Query:**
```
Analyze recent advances in cancer immunotherapy. Find clinical studies 
from PubMed, identify breakthrough papers with high citations from 
Semantic Scholar, and summarize the current state of the field.
```

**What happens:**
1. PubMed finds clinical trials and medical studies
2. Semantic Scholar finds highly-cited breakthrough papers
3. News fetcher finds recent developments
4. QA Engine creates comprehensive medical research summary
5. All sources shown for verification

---

### Example 3: Cross-Disciplinary Research

**Query:**
```
Investigate the intersection of quantum computing and cryptography. 
Find papers from ArXiv and Semantic Scholar, compare citation impact, 
and identify future research directions.
```

**What happens:**
1. ArXiv finds preprints on quantum cryptography
2. Semantic Scholar finds published papers with citation metrics
3. Wikipedia provides background on both fields
4. QA Engine synthesizes cross-disciplinary insights
5. Data plotter shows research trends

---

### Example 4: PDF Analysis with Context

**Query:**
```
Analyze the paper at papers/nature_ml_2024.pdf and compare its 
findings with recent research from Semantic Scholar on the same topic.
```

**What happens:**
1. PDF Parser extracts text from local file
2. Semantic Scholar searches related papers
3. QA Engine compares findings
4. Comprehensive analysis generated

---

## 🏆 Research Capabilities Comparison

| Tool | Coverage | Best For | Citation Data | Free Tier |
|------|----------|----------|---------------|-----------|
| **Semantic Scholar** | 200M+ (all fields) | Any discipline | Yes (with impact scores) | 100 req/5min |
| **PubMed** | 35M+ (biomedical) | Medical/health research | No | Unlimited |
| **ArXiv** | 2M+ (CS/Physics) | Preprints, recent work | No | Good limits |
| **Wikipedia** | General knowledge | Background/context | No | Good limits |
| **PDF Parser** | Local files | Full-text analysis | N/A | Unlimited |

---

## 🔥 Power User Tips

### Tip 1: Use Multiple Research Tools Together

Best practice for comprehensive research:
```
1. Semantic Scholar → Find highly-cited papers (all disciplines)
2. PubMed → Add medical/clinical perspective (if relevant)
3. ArXiv → Include latest preprints
4. QA Engine → Synthesize everything with citations
```

### Tip 2: Citation-Driven Research

Find the most impactful papers:
```
"Find papers on [topic] with >100 citations from Semantic Scholar, 
analyze their impact, and identify common themes"
```

Semantic Scholar's "influential citation" metric is gold for this!

### Tip 3: Medical + AI Research

For healthcare AI queries:
```
"Research AI in medical diagnosis using both Semantic Scholar 
(for ML papers) and PubMed (for clinical studies)"
```

Gets both technical ML perspective AND clinical validation.

### Tip 4: Verify with Multiple Sources

For critical research:
```
"Find papers on [controversial topic] from Semantic Scholar, 
cross-reference with PubMed studies, and provide balanced analysis"
```

Multiple sources prevent single-source bias.

### Tip 5: Local Paper Analysis

When you have papers downloaded:
```
"Parse papers/important_paper.pdf, find related work from Semantic 
Scholar, and identify how it fits into current research landscape"
```

---

## 📊 Expected Query Flow

### For: "Research CRISPR gene editing safety concerns"

**Step 1: Planning**
```
Planner selects:
1. pubmed_search (biomedical focus)
2. semantic_scholar (broader academic view)
3. news_fetcher (recent safety incidents)
4. data_plotter (visualize paper counts)
5. qa_engine (synthesize comprehensive answer)
```

**Step 2: Execution**
```
PubMed: Found 127 articles
  - "Safety of CRISPR-Cas9 therapy..." (2023, NEJM)
  - "Off-target effects in gene editing..." (2024, Nature)
  
Semantic Scholar: Found 89 papers
  - "CRISPR Safety: 1,234 citations, 89 influential
  - Identifies key researchers: Doudna, Zhang, etc.
  
News: Found 15 recent articles
  - FDA approves first CRISPR therapy
  - Safety concerns in clinical trials
```

**Step 3: Synthesis**
```
QA Engine creates comprehensive answer:
- Current state of CRISPR safety
- Key safety concerns from medical literature
- Citation-backed evidence
- Recent developments
- Expert perspectives
- Future directions

All grounded in actual papers found!
```

---

## 🎯 Best Queries for Scientific Research

### General Science
```
"Review recent machine learning breakthroughs"
"Analyze quantum computing progress in the last 2 years"
"Research climate change prediction models"
```

### Medical/Healthcare
```
"Investigate AI applications in cancer detection"
"Research COVID-19 vaccine development timeline"
"Analyze mental health interventions using digital therapeutics"
```

### Cross-Disciplinary
```
"Explore AI applications in drug discovery"
"Research quantum machine learning algorithms"
"Analyze neuromorphic computing for robotics"
```

### Citation Analysis
```
"Find the most influential papers on transformer models"
"Identify key researchers in CRISPR gene editing"
"Analyze citation networks for climate AI research"
```

---

## 🔧 Troubleshooting

### Issue: "No results from Semantic Scholar"

**Solutions:**
- Check internet connection
- Try broader search terms
- API might be rate-limited (wait 5 minutes)

### Issue: "PubMed returns no articles"

**Solutions:**
- Query might be too specific
- Try medical terminology (e.g., "myocardial infarction" vs "heart attack")
- Add year range to query

### Issue: "PDF parsing fails"

**Solutions:**
- Install pdfplumber: `pip install pdfplumber`
- Check file path is absolute and correct
- Some PDFs are image-based (OCR needed)

---

## 📈 Performance Notes

- **Semantic Scholar**: ~2-3 seconds per query
- **PubMed**: ~3-5 seconds per query (fetches full details)
- **PDF Parser**: ~1-2 seconds per MB of PDF

---

## 🚀 Next Steps

1. **Test the tools** with sample queries
2. **Try complex multi-tool queries** for research
3. **Experiment with PDF analysis** of downloaded papers
4. **Compare ArXiv vs Semantic Scholar** for your field

---

## 💡 Example Research Session

```bash
python main.py
```

**Try this comprehensive query:**

```
Research the current state of large language models in healthcare. 
Find papers from both Semantic Scholar and PubMed, identify the top 
5 most-cited papers, analyze clinical applications, summarize safety 
concerns, and create a visual timeline of breakthroughs. Provide a 
comprehensive analysis with citations.
```

**You'll get:**
- 10+ papers from Semantic Scholar (with citation counts)
- 10+ clinical studies from PubMed
- Background from Wikipedia
- Recent news coverage
- Comprehensive LLM-synthesized analysis (1500+ words)
- Citations for every claim
- Visual chart of research metrics
- All sources shown for verification

**This is your research assistant in action!** 🎓

---

## ✅ Summary

**Your system now provides:**
- ✅ Comprehensive academic paper search (200M+ papers)
- ✅ Medical/biomedical research access (35M+ articles)
- ✅ Citation and impact metrics
- ✅ Full-text PDF analysis
- ✅ Multi-source verification
- ✅ Factually-grounded synthesis
- ✅ Professional research reports

**Perfect for:**
- Literature reviews
- Research gap analysis
- Citation analysis
- Medical research
- Cross-disciplinary studies
- Academic writing support

**Your DualMind Orchestrator is now a professional-grade Research Assistant!** 🚀
