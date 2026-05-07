# AgentD - Quick Start Guide

**Self-contained, production-ready LLM agent framework**

---

## 🚀 Start Using AgentD Right Now

### From `/root/agentD` directory:

```bash
cd /root/agentD
./start.sh
```

That's it. Everything works from here.

---

## 📋 What You Can Do

### Inside the TUI (after running `./start.sh`):

**Pentester Research:**
```
/pentester-threat "RCE vulnerabilities 2026"
/pentester-apt "APT28"
/pentester-library
/pentester-retrieve spring-boot
```

**Memory & Knowledge:**
```
/remember
/threads
/tokens
```

**Chat:**
```
Just type normally to chat with Claude
Use research findings in your questions
```

---

## 📁 Directory Structure

```
/root/agentD/
├── venv/                          ← Self-contained environment
├── agentd/                        ← Python package
│   ├── pentester_skill.py        ← Threat intelligence
│   ├── browser_tools.py          ← Browser automation
│   └── ... (other modules)
├── start.sh                       ← Run this to start
├── setup.py                       ← Package config
├── README.md                      ← Project info
├── PENTESTER_TUI_INTEGRATION.md   ← Full guide
└── ... (documentation)
```

---

## 🎯 Common Usage

### 1. Research Threats
```bash
./start.sh
# Then: /pentester-threat "Your topic"
```

### 2. Research APT Groups
```bash
./start.sh
# Then: /pentester-apt "APT28"
```

### 3. View Saved Research
```bash
./start.sh
# Then: /pentester-library
```

### 4. Chat with Claude
```bash
./start.sh
# Then: Just type your question
```

### 5. Check Token Usage
```bash
./start.sh
# Then: /tokens
```

---

## 💡 Advanced Usage

### Run Command Without TUI
```bash
./start.sh D "write a function to reverse a list"
```

### Direct Python Usage
```bash
source venv/bin/activate
python -c "from agentd import Agent; agent = Agent(model='haiku'); print(agent)"
```

### Use Research Skills Directly
```bash
source venv/bin/activate
python -c "from agentd import PentesterSkill; skill = PentesterSkill(); print(skill.list_skill_library())"
```

---

## 📚 Full Documentation

Inside `/root/agentD/`:
- `PENTESTER_TUI_INTEGRATION.md` - Complete TUI guide
- `BROWSER_RESEARCH_GUIDE.md` - Research capabilities
- `LIBRARY.md` - Installation & usage
- `SLASH_COMMANDS.md` - All commands

---

## ✅ Verification

Everything is installed and ready:

```bash
cd /root/agentD
source venv/bin/activate
python -c "from agentd import Agent, PentesterSkill, BrowserToolkit; print('✅ All systems ready')"
```

---

## 🎯 Start Now

```bash
cd /root/agentD
./start.sh
```

Then use `/pentester-threat`, `/pentester-apt`, or just chat! 🚀

---

## 🔧 If You Need to Reinstall

```bash
cd /root/agentD
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

**Everything is self-contained in `/root/agentD/`. Just run `./start.sh`!**
