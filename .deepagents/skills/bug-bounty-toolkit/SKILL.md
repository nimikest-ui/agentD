---
name: bug-bounty-toolkit
description: "Curated resource guide and workflow for bug bounty hunters. Use when hunting for vulnerabilities in bug bounty programs."
license: MIT
source: Awesome-Hacking research (https://github.com/Hack-with-Github/Awesome-Hacking)
---

# Bug Bounty Toolkit Skill

A practical workflow and resource index for bug bounty hunters.

## Core Resources

| Resource | Purpose |
|---|---|
| [Awesome Bug Bounty](https://github.com/djadmin/awesome-bug-bounty) | Program lists + write-up index |
| [Bug Bounty Reference](https://github.com/ngalongc/bug-bounty-reference) | Write-ups categorized by bug type |
| [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) | Payloads and bypass techniques |
| [SecLists](https://github.com/danielmiessler/SecLists) | All wordlist types |
| [Hacker101](https://github.com/Hacker0x01/hacker101) | Free web security course by HackerOne |
| [API Security Checklist](https://github.com/shieldfy/API-Security-Checklist) | API-specific vuln checklist |
| [OWASP CheatSheetSeries](https://github.com/OWASP/CheatSheetSeries) | Vuln class reference + remediation |
| [CyberChef](https://gchq.github.io/CyberChef/) | Encoding/decoding/transform in browser |

---

## Workflow

### 1. Choose a Target
- Start with programs on HackerOne, Bugcrowd, Intigriti, Synack
- Prefer programs with wide scope and good payout history
- Read the program policy carefully — know what's in/out of scope

### 2. Recon
- Subdomains: amass, subfinder, assetfinder
- URLs: waybackurls, gau, hakrawler
- Parameters: arjun, paramspider
- JS files: linkfinder, secretfinder (look for keys, endpoints)

Use **SecLists** DNS wordlists for brute-forcing subdomains.

### 3. Hunt by Bug Class

**IDOR / Access Control**
- Change numeric IDs in requests (user IDs, order IDs, document IDs)
- Test horizontal (same role) and vertical (different role) access
- Check UUID predictability

**SSRF**
- Look for URL parameters, webhooks, import-from-URL features
- Payloads: http://169.254.169.254/ (AWS metadata), http://localhost/
- Reference: PayloadsAllTheThings /SSRF Injection/

**XSS**
- Reflected: inject in search, error messages, URL params
- Stored: inject in profile fields, comments, file names
- DOM-based: trace document.write, innerHTML, eval() sources
- Reference: PayloadsAllTheThings /XSS Injection/

**SQLi**
- Test all input fields, headers, cookies
- Tools: sqlmap (carefully, check scope)
- Reference: PayloadsAllTheThings /SQL Injection/

**Subdomain Takeover**
- Find CNAMEs pointing to unclaimed services (Heroku, GitHub Pages, etc.)
- Tools: subjack, can-i-take-over-xyz

**Open Redirect**
- Look for ?redirect=, ?url=, ?next=, ?return_to=
- Payloads: //evil.com, \/\/evil.com, %2F%2Fevil.com

**SSTI (Server-Side Template Injection)**
- Test {{7*7}}, ${7*7}, <%= 7*7 %>
- Reference: PayloadsAllTheThings /SSTI/

### 4. API Hunting
Follow the **[API Security Checklist](https://github.com/shieldfy/API-Security-Checklist)**:
- Auth: broken auth, JWT weaknesses, API key exposure
- Rate limiting: test for absence
- Mass assignment: send extra fields in POST/PUT
- Verbose errors: check for stack traces, internal paths

### 5. Write a Good Report

Structure:
1. **Title**: [Component] Vuln Type allows [Impact]
2. **Severity**: CVSS score or P1-P4
3. **Description**: What the bug is, why it's vulnerable
4. **Steps to Reproduce**: Numbered, precise, reproducible
5. **Impact**: What an attacker can actually do
6. **Evidence**: Screenshots, request/response, PoC video

Do:
- Report clearly and professionally
- Include a minimal, clean PoC
- Suggest a fix

Don't:
- Exaggerate severity
- Access user data beyond what's needed to prove the bug
- Publicly disclose before the program resolves it

---

## Learning Resources

- **[Hacker101](https://github.com/Hacker0x01/hacker101)** — start here if new
- **[Bug Bounty Reference write-ups](https://github.com/ngalongc/bug-bounty-reference)** — learn from others
- **[The Art of Hacking (h4cker)](https://github.com/The-Art-of-Hacking/h4cker)** — thousands of references
- **[Web Security (qazbnm456)](https://github.com/qazbnm456/awesome-web-security)** — deep web security material

---

## Common Bypass Techniques

| Filter | Bypass |
|---|---|
| WAF blocking script tags | img src=x onerror=alert(1), SVG payloads |
| SQL filter on single quote | double quote, backtick, Unicode equivalents |
| SSRF filter on localhost | 127.0.0.1, ::1, 0.0.0.0, DNS rebinding |
| Path traversal filter | URL encoding %2F, double encoding %252F |
| Open redirect filter | //attacker.com, \/attacker.com |

Full bypasses: **PayloadsAllTheThings** (each vuln directory has a Bypass section)
