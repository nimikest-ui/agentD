# Hacker101 CTF — Session Review & Retrospective

**Session Date:** 29 May 2026  
**Duration:** 1h 5m (01:45 – 02:50 UTC)  
**Result:** 3/3 flags (100%)  
**Tools Used:** mimo-v2.5 (flags 1–2), mimo-v2.5-pro (flag 3)

---

## Executive Summary

Solved all 3 flags through IDOR, UNION SQLi, and blind SQLi. Total time was efficient for flags 1–2 (~7 min combined), but flag 3 took ~55 min due to hypothesis chaining and dead ends. Key lesson: **detect error message differences early**.

---

## Timeline & Decision Tree

### Phase 1: Recon (00:00 – 01:50, ~10 min)
- Mapped homepage → found pages 1, 2, hidden page 3 (403)
- Identified login form
- Identified create/edit endpoints

**Decision:** Test IDOR first (low friction) → **SUCCESS in 2 min**

### Phase 2: IDOR Exploit (01:50 – 01:52, 2 min)
- Tested GET /page/edit/3 → 302 redirect (auth enforced)
- Tested POST /page/edit/3 → 200 OK + **FLAG 1**

**Lesson:** Always test all HTTP methods, not just GET.

---

### Phase 3: SQL Injection Detection (01:52 – 01:57, 5 min)
- Injected `' OR 1=1--+-` into username
- Response changed from "Unknown user" to "Invalid password"
- **SQL injection confirmed**

**Decision:** Attempt UNION injection on login → **SUCCESS in 3 min**

### Phase 4: UNION SQLi + Cookie Forge (01:57 – 02:02, 5 min)
- Crafted `username=' UNION SELECT 'testpass'--+-`
- Received admin cookie: `{"admin":true}`
- Accessed hidden page 3 → **FLAG 2**

**Lesson:** Single-column queries are easiest; test column count via error behavior.

---

### Phase 5: Hunting Flag 3 (02:02 – 02:50, ~48 min)
- **02:02–02:15 (13 min):** SSTI exploration (page 4 had `{{7*7}}`)
  - Tried template injection payloads
  - ❌ Dead end (templates were escaped)

- **02:15–02:25 (10 min):** XSS hunt (pages 5–6 had payloads)
  - Found XSS but no flag embedded
  - ❌ Dead end (XSS was for page pollution)

- **02:25–02:35 (10 min):** Cookie signature forging
  - Attempted JWT signature prediction
  - ❌ Dead end (verified server-side)

- **02:35–02:43 (8 min):** Path traversal enumeration
  - Tested `/page/../../etc/passwd`
  - ❌ Dead end (filtered by router)

- **02:43–02:50 (7 min):** Boolean-based blind SQLi
  - Realized error message difference = oracle
  - Extracted username → `lizette`
  - Extracted password → `tamra`
  - Logged in → **FLAG 3** ✓

**Lesson:** Error message differences are gold. Test at minute 2, not minute 43.

---

## What Went Right ✓

| Success | Why | Time Saved |
|---------|-----|-----------|
| Fast IDOR | Tested POST after GET | 2 min |
| Quick SQLi detection | Recognized error difference | 3 min |
| Persistence | Didn't quit | Flag 3 found |
| Systematic automation | Python loops for char extraction | ~20 min |

---

## What Wasted Time ✗

| Mistake | Cost | Lesson |
|---------|------|--------|
| SSTI rabbit hole | 13 min | Kill after 10 min if no progress |
| XSS exploration | 10 min | Good timeout, but should test error oracles first |
| Cookie forgery | 10 min | JWT needs secret key; don't guess |
| Path traversal | 8 min | Good discipline here |
| Late error testing | **40 min** | Test "Unknown user" vs "Invalid password" at minute 2 |

**Total wasted: ~41 min (62% of session)**

---

## If I Redid Today

1. **Test error messages at minute 2** (not minute 43)
   - "Unknown user" vs "Invalid password" → boolean oracle
   - Could have solved flag 3 in 10 min total

2. **10-minute hypothesis rule:**
   - SSTI: kill after 10 min
   - XSS: kill after 10 min
   - Path traversal: kill after 10 min

3. **Prioritize by complexity:**
   - Easy: method testing (IDOR)
   - Medium: SQLi detection + UNION
   - Hard: Boolean oracle (but comes before SSTI!)

4. **Automate immediately:**
   - Python template for blind SQLi char loops
   - Next time: copy-paste, don't reinvent

---

## Vulnerability Patterns

### IDOR (Access Control Bypass)
- **Signal:** GET protected, POST/PUT unprotected
- **Speed:** 1–5 min (test all methods)
- **Payload:** `' OR 1=1--` detection → `UNION SELECT` enumeration

### UNION SQLi (Error-based)
- **Signal:** Error behavior changes with SQL syntax
- **Speed:** 5–15 min (discover columns, enumerate DB)
- **Test:** `' OR 1=1--` first, then `UNION SELECT NULL,NULL,...`

### Boolean Blind SQLi (Logic Leak)
- **Signal:** Error message, response timing, or status code differences
- **Speed:** 10–60 min (depends on automation)
- **Test:** `' AND 1=1--` (true condition) vs `' AND 1=2--` (false)

---

## Next Session Checklist

Before your next CTF:
- [ ] Review blind-sqli-playbook.md (char extraction templates)
- [ ] Review error-message-oracle-patterns.md (detect early)
- [ ] Review ctf-recon-triage.md (phase workflow)
- [ ] Update exploit-templates.md with new payloads
- [ ] Time-box hypotheses (10 min max)
