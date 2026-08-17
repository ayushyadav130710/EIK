# 🚀 EIK - Ethical Intelligence Toolkit v3.0

```
╔═════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                         ║
║  ███████╗██╗██╗  ██╗      ██╗  ██╗                                                     ║
║  ██╔════╝██║██║ ██╔╝      ██║ ██╔╝                                                     ║
║  █████╗  ██║██║██╔╝   ██████╗██╔╝                                                      ║
║  ██╔══╝  ██║██║███╗   ██╔════╝███╗                                                     ║
║  ███████╗██║██║██║    ██║     ██║ ██╗                                                  ║
║  ╚══════╝╚═╝╚═╝╚═╝    ╚═╝     ╚═╝ ╚═╝                                                  ║
║                                                                                         ║
║         ETHICAL INTELLIGENCE TOOLKIT v3.0 - COMPREHENSIVE                             ║
║         🤖 AI-POWERED PENETRATION TESTING SUITE 🤖                                    ║
║                                                                                         ║
║         ✓ 100+ Vulnerability Vectors       ✓ 10 Major Categories                      ║
║         ✓ Enterprise-Grade Scanning        ✓ AI-Assisted Analysis                     ║
║                                                                                         ║
║              [ HACK RESPONSIBLY | DEFEND FEARLESSLY ]                                  ║
║                  Founded by Ayush Yadav                                               ║
║                                                                                         ║
║    🟢 Status: ACTIVE | 🤖 AI: READY | 🔍 Vectors: 100+ | ⚡ Speed: FAST               ║
║                                                                                         ║
╚═════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 📋 Quick Navigation
| 🎯 | 📖 | 🔥 | 💻 | 📊 | ⚙️ | 📋 |
|----|----|----|----|----|----|----|
| [What is EIK?](#-what-is-eik) | [Quick Start](#-quick-start) | [10 Categories](#-the-10-vulnerability-categories) | [Usage Guide](#-usage-guide) | [Reports](#-understanding-reports) | [Advanced](#-advanced-features) | [Compliance](#-compliance--standards) |

---

## 🎯 What is EIK?

**EIK** is an **enterprise-grade penetration testing framework** with **100+ automated vulnerability vectors** across **10 major categories**. Powered by **EvilGPT (Gemini AI)** for intelligent analysis.

### ✅ What You Can Do
- 🔍 **Comprehensive Scanning** - Test all major vulnerability categories
- 🎯 **Targeted Exploitation** - 100+ specific attack vectors  
- 📊 **AI-Powered Analysis** - EvilGPT analyzes results & suggests fixes
- 📈 **Compliance Reporting** - GDPR, PCI-DSS, HIPAA, SOC2 ready
- 🔄 **CI/CD Integration** - Automate security testing in pipelines
- 📱 **Multiple Formats** - JSON, Markdown, HTML reports

### ⚠️ Legal Notice
**AUTHORIZED TESTING ONLY**: Use only on systems you own or have explicit written permission to test.

---

## ⚡ Quick Start (60 Seconds)

### Kali Linux setup (recommended)

Run EIK from Kali Linux for the external web-security tools. First copy or clone
this project into Kali, then install the standard web-assessment dependencies:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
  whois dnsutils nmap sslscan whatweb nikto nuclei \
  gobuster ffuf wpscan

cd ~/EIK
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Verify the local installation before scanning:

```bash
python EIK.py --help
python -m unittest discover -s tests -v
```

For an authorized standard website assessment, create a scope file containing
only the domain you own:

```bash
printf 'your-site.example\n' > scope.txt
python EIK.py -t https://your-site.example --assessment-profile standard \
  --authorized --engagement-id my-website-2026 --scope scope.txt \
  --sarif --fail-on high
```

`--engagement-id` is just a label you choose; it is not a government ID. The
`standard` profile runs reconnaissance, port/service checks, web checks, and
reporting. Keep `active` testing disabled unless you explicitly need it for an
approved engagement.

### Step 1: Navigate to EIK
```bash
cd c:\EIK
```

### Step 2: Run a Scan
```bash
# Create an approved scope file (one entry per line)
printf "yourdomain.com\n" > scope.txt

# Non-invasive assessment (modules 1-4,7,8)
python3 EIK.py -t https://yourdomain.com -m 1,2,3,7 \
  --authorized --engagement-id SOW-123 --scope scope.txt

# Or run interactively
python3 EIK.py

# Preview the full command plan without executing it
python3 EIK.py -t https://yourdomain.com -m all --dry-run
```

### Authorization & Scope (v3.1)

Live runs require all of `--authorized`, `--engagement-id`, and `--scope FILE`.
`--engagement-id` is only a label you choose for the scan (for example,
`my-website-2026`); it is **not** a government or platform identity check.
The scope file accepts one domain, URL, IP address, or CIDR block per line; comments
begin with `#`. EIK writes `run_manifest.json` beside the results so each run records
its approved target and engagement ID. Modules 5 and 6 additionally require
`--allow-active`, because they can change target state or generate payloads.

```bash
# Only for an explicitly authorized active test
python3 EIK.py -t https://yourdomain.com -m 5 \
  --authorized --engagement-id SOW-123 --scope scope.txt --allow-active
```

### Step 3: View Results
```
output/yourdomain.com/
├── comprehensive_exploitation_report_v2.json   ← MAIN FINDINGS
├── findings.json
├── report.md
└── exploit/
    ├── injection_flaws/
    ├── auth_vulnerabilities/
    ├── access_control_flaws/
    ├── server_side_vulns/
    ├── client_side_vulns/
    ├── misconfigurations/
    ├── business_logic/
    ├── cryptographic_flaws/
    ├── dos_resource/
    └── memory_structural/
```

---

## 🔥 The 10 Vulnerability Categories

### **1️⃣ Injection & Input Flaws** (15+ vectors)
**Risk:** 🔴 **CRITICAL** | **OWASP:** A03 | **CWE:** 89, 90, 79

Attackers inject malicious input to execute arbitrary code or bypass security controls.

**Types:** SQLi | Blind SQLi | NoSQL | LDAP | XPath | OS Command | SSTI | XXE | GraphQL | CRLF | Prototype Pollution

**Quick Fix:**
```python
# ✗ VULNERABLE
query = f"SELECT * FROM users WHERE name='{user_input}'"

# ✓ SECURE
cursor.execute("SELECT * FROM users WHERE name=%s", (user_input,))
```

---

### **2️⃣ Broken Authentication** (12+ vectors)
**Risk:** 🔴 **CRITICAL** | **OWASP:** A07 | **CWE:** 307, 345, 347

Weaknesses in user identification & session management.

**Types:** Credential Stuffing | Brute Force | Session Fixation | JWT Bypass | OAuth Issues | MFA Bypass | Default Credentials

**Quick Fix:**
```python
# Use strong hashing
from werkzeug.security import generate_password_hash
hashed = generate_password_hash(password, method='pbkdf2:sha256')

# Secure sessions
session.cookie_secure = True
session.cookie_httponly = True
session.cookie_samesite = 'Strict'
```

---

### **3️⃣ Access Control Vulnerabilities** (10+ vectors)
**Risk:** 🟠 **HIGH** | **OWASP:** A01 | **CWE:** 639, 640, 434

Broken authorization checks allowing unauthorized access.

**Types:** IDOR | Privilege Escalation | CORS Misconfiguration | Path Traversal | File Upload | API Bypass

**Quick Fix:**
```python
# Check authorization for every resource
@require_login
def get_user(user_id):
    user = User.query.get(user_id)
    if user.id != current_user.id:
        abort(403)  # Forbidden
    return user
```

---

### **4️⃣ Server-Side Vulnerabilities** (11+ vectors)
**Risk:** 🔴 **CRITICAL** | **OWASP:** A06 | **CWE:** 94, 434, 611

Server-side processing flaws leading to remote compromise.

**Types:** SSRF | LFI | RFI | RCE | Deserialization | HTTP Smuggling | WebSocket Issues

**Quick Fix:**
```python
# Validate URLs for SSRF
from urllib.parse import urlparse
parsed = urlparse(url)
if parsed.hostname in ['127.0.0.1', 'localhost']:
    raise ValueError("Internal addresses blocked")
```

---

### **5️⃣ Client-Side Vulnerabilities** (10+ vectors)
**Risk:** 🟠 **HIGH** | **OWASP:** A03, A04 | **CWE:** 79, 352

Browser-based attacks affecting end-users.

**Types:** XSS | CSRF | Clickjacking | Open Redirect | DOM XSS | Cookie Issues

**Quick Fix:**
```html
<!-- Escape all user input -->
<p><%= escapeHtml(userInput) %></p>

<!-- Content Security Policy -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; script-src 'self'">

<!-- CSRF Token -->
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

---

### **6️⃣ Security Misconfiguration** (11+ vectors)
**Risk:** 🟠 **HIGH** | **OWASP:** A05 | **CWE:** 16, 22, 552

Insecure default settings & missing security controls.

**Types:** Default Credentials | Directory Listing | Cloud Bucket Misconfiguration | Subdomain Takeover | Weak TLS | Missing Headers | Debug Mode

**Quick Fix:**
```nginx
# Add security headers
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

# Disable directory listing
Options -Indexes

# Disable debug mode
DEBUG = False
```

---

### **7️⃣ Business Logic Flaws** (10+ vectors)
**Risk:** 🟠 **HIGH** | **OWASP:** A04 | **CWE:** 863, 307

Flaws in application flow allowing unauthorized actions.

**Types:** Price Manipulation | Race Conditions | Coupon Abuse | API Key Exposure | Parameter Tampering | Inventory Attacks

**Quick Fix:**
```python
# Prevent race conditions with locks
from threading import Lock
cart_lock = Lock()
with cart_lock:
    if inventory[item] > 0:
        inventory[item] -= 1
```

---

### **8️⃣ Cryptographic Flaws** (9+ vectors)
**Risk:** 🔴 **CRITICAL** | **OWASP:** A02 | **CWE:** 326, 327, 916

Weak encryption & insecure data transmission.

**Types:** Weak Algorithms | Hardcoded Keys | Insufficient Entropy | Broken SSL/TLS | Unencrypted Data | Weak Hashing

**Quick Fix:**
```python
# Modern encryption
from cryptography.fernet import Fernet
cipher = Fernet(Fernet.generate_key())
encrypted = cipher.encrypt(data)

# Secure hashing
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```

---

### **9️⃣ Denial of Service (DoS)** (8+ vectors)
**Risk:** 🟠 **HIGH** | **OWASP:** A08 | **CWE:** 400, 770, 776

Attacks that exhaust resources or crash services.

**Types:** ReDoS | Billion Laughs | Slowloris | Hash Collision | Unbounded Queries | Resource Exhaustion | DDoS

**Quick Fix:**
```python
# Rate limiting
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login(): pass
```

---

### **🔟 Memory & Buffer Overflows** (5+ vectors)
**Risk:** 🔴 **CRITICAL** | **OWASP:** A08 | **CWE:** 120, 787, 190

Low-level memory manipulation leading to crashes/RCE.

**Types:** Buffer Overflow | Integer Overflow | Format String | Use-After-Free | Double Free

**Quick Fix:**
```c
// ✗ VULNERABLE
char buffer[10];
strcpy(buffer, user_input);

// ✓ SECURE
char buffer[10];
strncpy(buffer, user_input, sizeof(buffer) - 1);
buffer[sizeof(buffer) - 1] = '\0';
```

---

## 📖 Usage Guide

### 🎯 Command Reference

```bash
# Show help
python3 EIK.py --help

# Interactive mode
python3 EIK.py

# Scan an authorized in-scope target
python3 EIK.py -t https://example.com -m 1,2,3,7 \
  --authorized --engagement-id SOW-123 --scope scope.txt

# Run multiple modules
python3 EIK.py -t http://example.com -m 1,3,5

# Preview all modules without network activity
python3 EIK.py -t https://example.com -m all --dry-run

# Fast scan
python3 EIK.py -t http://example.com --fast

# Stealth scan
python3 EIK.py -t http://example.com --stealth

# AI analysis
python3 EIK.py -t http://example.com --ask "What are critical findings?"

# AI interactive chat
python3 EIK.py -t http://example.com --chat

# Show version
python3 EIK.py --version

# Show about
python3 EIK.py --about

# Dry run
python3 EIK.py -t http://example.com --dry-run
```

### 📚 Module Descriptions

| # | Module | Purpose | Tools |
|---|--------|---------|-------|
| 1 | 🔍 Reconnaissance | OSINT & enumeration | whois, dig, subfinder |
| 2 | 🔫 Port Scan | Network scanning | masscan, nmap, sslscan |
| 3 | 🌐 Web Scan | Web vulnerabilities | whatweb, nikto, nuclei |
| 4 | ⚙️ Service Enum | Service discovery | enum4linux, smbmap |
| 5 | 💣 **Exploitation** | **100+ vectors v2.0** | **sqlmap, hydra, metasploit** |
| 6 | 📤 Post-Exploit | Payload generation | msfvenom |
| 7 | 📊 Report | Report generation | JSON, Markdown |
| 8 | 🤖 AI Hub | AI analysis | EvilGPT |

---

## 📊 Understanding Reports

### 📁 Output Structure
```
output/example.com/
├── comprehensive_exploitation_report_v2.json  ← MAIN FINDINGS
├── findings.json
├── report.md
└── exploit/
    ├── injection_flaws/
    ├── auth_vulnerabilities/
    ├── access_control_flaws/
    ├── server_side_vulns/
    ├── client_side_vulns/
    ├── misconfigurations/
    ├── business_logic/
    ├── cryptographic_flaws/
    ├── dos_resource/
    └── memory_structural/
```

### 🎯 Severity Levels
| Level | Icon | Meaning | Action |
|-------|------|---------|--------|
| CRITICAL | 🔴 | Immediate exploitation | Fix NOW |
| HIGH | 🟠 | Likely exploitation | Fix ASAP |
| MEDIUM | 🟡 | Possible exploitation | Fix Soon |
| LOW | 🔵 | Unlikely exploitation | Plan fix |
| INFO | ⚪ | Informational | Document |

---

## ⚙️ Advanced Features

### 🤖 AI-Powered Analysis (EvilGPT)
```bash
# Set Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Ask AI question
python3 EIK.py --ask "What are top 3 critical risks?"

# Interactive AI chat
python3 EIK.py -t http://example.com --chat
```

### 📊 Dashboard & Metrics
Automatically generated showing:
- ⭐ Risk scores (0-100)
- 📋 Compliance status (GDPR/PCI-DSS/HIPAA/SOC2)
- 📈 Trend analysis
- 🔧 Auto-remediation suggestions

### 📋 Remediation Reports
Detailed fix instructions:
- ❌ Vulnerable code
- ✅ Secure code
- 📚 Best practices
- 🔗 References

---

## 📋 Compliance & Standards

### OWASP Top 10 2021
| EIK Category | OWASP | Risk |
|--------------|-------|------|
| Injection | A03 | CRITICAL |
| Authentication | A07 | CRITICAL |
| Access Control | A01 | CRITICAL |
| Server-Side | A06 | CRITICAL |
| Client-Side | A03, A04 | HIGH |
| Misconfiguration | A05 | HIGH |
| Business Logic | A04 | HIGH |
| Cryptography | A02 | CRITICAL |
| DoS | A08 | HIGH |
| Memory | A08 | CRITICAL |

### CWE Coverage
✅ CWE-79 (XSS) | ✅ CWE-89 (SQLi) | ✅ CWE-352 (CSRF) | ✅ CWE-434 (Upload) | ✅ CWE-639 (AuthZ Bypass) | ✅ CWE-862 (Access Control) | And 50+ more

### Standards
📋 GDPR | 📋 PCI-DSS | 📋 HIPAA | 📋 SOC 2 | 📋 ISO 27001

---

## 💻 CI/CD Integration

### Automation & regression testing (v3.1)

Every report run writes `report/summary.json` with stable finding fingerprints,
severity counts, and—when requested—the delta from a prior run. This gives CI a
reliable machine-readable result instead of parsing terminal output.

Module 3 also includes a built-in low-impact HTTP hardening baseline. It checks
HTTPS enforcement, HSTS, CSP, clickjacking and MIME protections, CORS, exposed
server details, and cookie security attributes without requiring extra tools.

```bash
python3 EIK.py -t https://yourdomain.com --assessment-profile standard \
  --authorized --engagement-id WEB-001 --scope scope.txt \
  --sarif --baseline previous-summary.json --fail-on high
```

Profiles are `passive` (recon/report), `standard` (recon, network/web checks,
report), and `active` (all modules; also requires `--allow-active`). With
`--fail-on high`, EIK exits with code `3` when a high or critical finding exists.

### GitHub Actions
```yaml
name: EIK Security Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run EIK
        run: python3 EIK.py -t http://localhost -m all
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: security-reports
          path: output/
```

### Docker
```bash
docker build -t eik .
docker run -v $(pwd)/output:/app/output eik \
  python3 EIK.py -t http://target.com -m all
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "command not found" | `sudo apt install -y nmap sqlmap nikto` |
| Permission denied | `chmod +x EIK.py` |
| No results | `ping example.com` |
| Rate limits | `python3 EIK.py --stealth` |

---

## 🔗 Resources

- 📖 [OWASP Top 10](https://owasp.org/Top10/)
- 📖 [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- 📖 [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- 🛠️ [Kali Linux](https://www.kali.org/)
- 🛠️ [Metasploit](https://www.metasploit.com/)

---

## 📄 Legal

**⚠️ AUTHORIZED TESTING ONLY**

✅ Test systems YOU own  
✅ Test WITH explicit written permission  
❌ DO NOT test without authorization  
❌ Unauthorized testing IS ILLEGAL  

---

**Founder:** Ayush Yadav | **Version:** 3.0 | **Status:** 🟢 Production Ready | **Updated:** 2026-08-17
