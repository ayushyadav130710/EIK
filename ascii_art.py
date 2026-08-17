#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EIK ASCII Art Logo Generator & Banner
"""

def get_eik_ascii_logo():
    """Return EIK logo as ASCII art"""
    logo = r"""
    
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                               ║
    ║                    ███████╗██╗██╗  ██╗      ██╗  ██╗                           ║
    ║                    ██╔════╝██║██║ ██╔╝      ██║ ██╔╝                           ║
    ║                    █████╗  ██║██║██╔╝   ██████╗██╔╝                            ║
    ║                    ██╔══╝  ██║██║███╗   ██╔════╝███╗                           ║
    ║                    ███████╗██║██║██║    ██║     ██║ ██╗                        ║
    ║                    ╚══════╝╚═╝╚═╝╚═╝    ╚═╝     ╚═╝                            ║
    ║                                                                               ║
    ║           ╔══════════════════════════════════════════════════════════╗         ║
    ║           ║  ETHICAL INTELLIGENCE TOOLKIT v3.0 - COMPREHENSIVE      ║         ║
    ║           ║  🤖 AI-POWERED PENETRATION TESTING SUITE 🤖             ║         ║
    ║           ║                                                          ║         ║
    ║           ║  • 100+ Vulnerability Vectors                           ║         ║
    ║           ║  • 10 Major Categories                                  ║         ║
    ║           ║  • Enterprise-Grade Scanning                            ║         ║
    ║           ║  • AI-Assisted Analysis                                 ║         ║
    ║           ║                                                          ║         ║
    ║           ║         [ HACK RESPONSIBLY | DEFEND FEARLESSLY ]        ║         ║
    ║           ║              Founded by Ayush Yadav                      ║         ║
    ║           ╚══════════════════════════════════════════════════════════╝         ║
    ║                                                                               ║
    ║         Status: 🟢 ACTIVE | AI: 🤖 READY | Vectors: 100+ | Scan: ⚡ FAST    ║
    ║                                                                               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    
    """
    return logo

def get_module_banner():
    """Module selection banner"""
    banner = r"""
    
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃                    🔥 EIK EXPLOITATION MODULES 🔥                         ┃
    ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
    ┃                                                                            ┃
    ┃  [1] 🔍  RECONNAISSANCE      - OSINT, DNS, Domain Enumeration             ┃
    ┃  [2] 🔫  PORT SCAN           - Network Scanning, Service Detection        ┃
    ┃  [3] 🌐  WEB SCAN            - Web Vulnerabilities, CMS Detection         ┃
    ┃  [4] 🔐  SERVICE ENUM        - SMB, RDP, LDAP, Windows Enumeration       ┃
    ┃  [5] 💥  EXPLOITATION        - 100+ Vectors, Injection, Auth, Access     ┃
    ┃  [6] 🎯  POST-EXPLOIT        - Payload Generation, Persistence           ┃
    ┃  [7] 📋  REPORT              - JSON, Markdown, PDF Generation            ┃
    ┃  [8] 🧠  AI HUB              - EvilGPT Analysis, Smart Recommendations    ┃
    ┃  [9] 📊  DASHBOARD           - Real-time Metrics & Trends                ┃
    ┃  [10]🔄  AUTO-FIX            - Automated Remediation Suggestions          ┃
    ┃                                                                            ┃
    ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
    ┃                                                                            ┃
    ┃  Select module: (1-10 or 'all')                                           ┃
    ┃                                                                            ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    
    """
    return banner

def get_findings_banner():
    """Findings display banner"""
    banner = r"""
    
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                                                                            ║
    ║               🚨 VULNERABILITY FINDINGS REPORT GENERATED 🚨               ║
    ║                                                                            ║
    ║    ┌─────────────────────────────────────────────────────────────────┐   ║
    ║    │  Total Vectors Tested: 100+                                    │   ║
    ║    │  Categories: 10                                                │   ║
    ║    │                                                                 │   ║
    ║    │  🔴 CRITICAL:  38 vectors                                      │   ║
    ║    │  🟠 HIGH:      45 vectors                                      │   ║
    ║    │  🟡 MEDIUM:    12 vectors                                      │   ║
    ║    │  🟢 LOW:        5 vectors                                      │   ║
    ║    │                                                                 │   ║
    ║    │  ⏱️  Scan Duration: [TIME]                                      │   ║
    ║    │  📊 Report: comprehensive_exploitation_report_v2.json          │   ║
    ║    │  📈 Trend: Increasing vulnerabilities detected                 │   ║
    ║    └─────────────────────────────────────────────────────────────────┘   ║
    ║                                                                            ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    
    """
    return banner

if __name__ == "__main__":
    print(get_eik_ascii_logo())
    print(get_module_banner())
    print(get_findings_banner())
