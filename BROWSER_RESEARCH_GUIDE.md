# AgentD Browser & Deep Research Guide

**Complete setup for web research, data extraction, and deep investigation with Claude Haiku 4.5**

---

## 📦 What's Installed

### ✅ Browser-Use (for interactive tasks)
- Full browser automation via Chrome DevTools Protocol
- Vision-based interaction (Claude sees the page)
- Form filling, authentication, multi-step workflows
- Google login support via Chrome profile reuse
- JavaScript rendering and network control

**GitHub:** [browser-use/browser-use](https://github.com/browser-use/browser-use)

### ✅ Firecrawl (for data extraction)
- Fast, LLM-optimized web scraping
- Returns clean Markdown/JSON
- JavaScript-rendered content support
- Sub-second extraction speed
- Perfect for bulk data gathering

**Website:** [firecrawl.dev](https://www.firecrawl.dev)

### ✅ Deep Research Agent
- Multi-agent research system
- Lead Researcher + 4 Subagents (Explorer, Extractor, Analyst, Verifier)
- Structured research workflow with verification
- Claude Haiku 4.5 for efficient processing

---

## 🚀 Quick Start

### 1. Check Browser Tools Status

```bash
source /root/lang/.venv/bin/activate
python -c "from agentd import get_browser_status; import json; print(json.dumps(get_browser_status(), indent=2))"
```

**Expected output:**
```json
{
  "model": "haiku",
  "browser_use": true,
  "firecrawl": true,
  "features": {
    "web_scraping": true,
    "form_filling": true,
    "authentication": true,
    "google_login": true,
    "data_extraction": true,
    "search": true
  }
}
```

### 2. Run Deep Research

```bash
cd /root/lang
python deep_research_agent.py "Your research question"
```

**Example:**
```bash
python deep_research_agent.py "Latest AI safety research 2026"
```

Results saved to: `/root/lang/research_results.json`

---

## 💼 Use Cases

### Use Case 1: Research + Extract Data

```bash
python deep_research_agent.py "Cloud computing providers comparison 2026"
```

**What it does:**
1. **Web Exploration** → Finds sources (AWS, Google Cloud, Azure, etc.)
2. **Data Extraction** → Scrapes pricing, features, benchmarks
3. **Analysis** → Compares and synthesizes findings
4. **Verification** → Checks accuracy and sources
5. **Summary** → Provides comprehensive report

### Use Case 2: Google Form/Data Access

Requires authentication and form filling:

```bash
python deep_research_agent.py "Extract Google Forms responses from shared survey"
```

**Requires:**
- Chrome profile with Google login saved
- Browser-Use handles the authentication automatically

### Use Case 3: Real-Time Market Data

```bash
python deep_research_agent.py "Current cryptocurrency prices and trends May 2026"
```

Firecrawl extracts JavaScript-rendered price data, Haiku analyzes trends.

---

## 🔧 Configuration

### Enable Firecrawl Data Extraction (Optional)

Get free API key: https://firecrawl.dev

```bash
export FIRECRAWL_API_KEY="your-api-key-here"
python deep_research_agent.py "Your query"
```

### Switch to More Powerful Model

Edit `/root/lang/deep_research_agent.py`:

```python
RESEARCH_MODEL = "claude-sonnet-4-6"  # More capable
LEAD_MODEL = "claude-opus-4-7"        # Most capable
```

---

## 📊 Architecture

```
User Query
    ↓
Deep Research Agent (Lead Researcher)
    ├── Web Explorer Subagent
    │   └── Browser-Use: Search and identify sources
    │
    ├── Data Extractor Subagent
    │   ├── Firecrawl: Fast LLM-ready extraction
    │   └── Browser-Use: Interactive sites, forms
    │
    ├── Analyst Subagent
    │   └── Claude Haiku: Synthesize patterns
    │
    └── Verifier Subagent
        └── Claude Haiku: Verify accuracy
            ↓
        Comprehensive Research Report (JSON)
```

---

## 🔐 Google Credentials & Authentication

### Method 1: Chrome Profile Reuse (Recommended)

If Google account is logged in on your Chrome:

```bash
python deep_research_agent.py "Access Google Drive documents"
```

**How it works:**
- Browser-Use copies your Chrome profile
- Reuses existing authentication
- No password needed in code
- Session saved for future runs

### Method 2: Interactive Login

Browser-Use handles login form:
- Clicks login button
- Fills email field
- Handles password (visible in credentials vault)
- Manages 2FA if needed

---

## 📈 Model Comparison for Research

| Model | Speed | Accuracy | Cost | Best For |
|-------|-------|----------|------|----------|
| **Haiku 4.5** | ⚡ Fast | Good | ✅ Cheap | Quick research, summaries |
| **Sonnet 4.6** | ⚡ Fast | Excellent | Moderate | Complex analysis, synthesis |
| **Opus 4.7** | Medium | Best | Higher | Deep reasoning, verification |

**Default:** Haiku 4.5 (recommended for most research)

---

## 🎯 Example: Complete Research Workflow

```bash
# 1. Ask research question
python deep_research_agent.py "What's the best database for IoT applications 2026?"

# 2. Check results
cat /root/lang/research_results.json | jq .

# 3. Use with AgentD
D "Summarize the research results from research_results.json"

# 4. Extract specific data
D "Extract pricing information from the research"
```

---

## 🔍 Advanced: Custom Research Agent

Create `/root/lang/my_research.py`:

```python
import asyncio
from deep_research_agent import DeepResearchAgent

async def custom_research():
    agent = DeepResearchAgent(model="claude-haiku-4-5-20251001")
    
    # Research multiple queries
    topics = [
        "AI safety regulations 2026",
        "Quantum computing progress",
        "Climate tech innovations"
    ]
    
    results = {}
    for topic in topics:
        findings = await agent.research(topic)
        results[topic] = findings
    
    # Analyze cross-topic patterns
    synthesis = await agent._synthesize_findings(
        "Cross-topic analysis",
        results
    )
    
    print(synthesis)

if __name__ == "__main__":
    asyncio.run(custom_research())
```

Run it:
```bash
python /root/lang/my_research.py
```

---

## 🛠️ Troubleshooting

### Browser-Use Not Finding Elements

```bash
# Enable verbose logging
export DEBUG=browser_use
python deep_research_agent.py "query"
```

### Firecrawl Extraction Issues

Requires valid API key:
```bash
export FIRECRAWL_API_KEY="your-key"
# Test
python -c "from firecrawl import FirecrawlApp; FirecrawlApp()"
```

### Google Authentication Fails

1. **Check Chrome profile:** Must have Google logged in
2. **Check permissions:** Profile must be readable
3. **Use alternative:** Interactive login handled by Browser-Use

### Haiku Model Not Responding

Try fallback:
```python
RESEARCH_MODEL = "claude-sonnet-4-6"  # Better availability
```

---

## 📚 Integration with AgentD

### Use in Agent Scripts

```python
from agentd import Agent, BrowserToolkit

# Create agent with browser tools
agent = Agent(model="haiku")
toolkit = BrowserToolkit(model="haiku")

# Check capabilities
status = toolkit.get_status()
print(f"Browser tools ready: {status['browser_use']}")
```

### Combine with D Command

```bash
# Start interactive session
D

# In the TUI
/remember Browser tools available for research
# Use /skill:web-research or browser automation
```

---

## 🎓 Learning Resources

- **Browser-Use Docs:** https://github.com/browser-use/browser-use
- **Firecrawl Docs:** https://docs.firecrawl.dev
- **Claude API:** https://platform.anthropic.com/docs
- **AgentD:** /root/agentD/README.md

---

## 📋 Installed Packages

```
browser-use==0.12.6
firecrawl-py==4.25.2
anthropic==0.76.0
```

Check anytime:
```bash
source /root/lang/.venv/bin/activate
pip list | grep -E "browser|firecrawl"
```

---

## ✨ What's Next

1. ✅ Browser-Use installed and configured
2. ✅ Firecrawl installed (ready for API key)
3. ✅ Deep Research Agent ready to use
4. ✅ Integration with AgentD complete
5. 🚀 **Try your first research:**

```bash
python /root/lang/deep_research_agent.py "Your question here"
```

---

**Ready to research!** 🔍

All tools configured with Claude Haiku 4.5 for fast, efficient research workflows.
