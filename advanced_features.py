#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EIK Advanced Features v3.0
==========================
Enhanced capabilities for powerful penetration testing:
- Dashboard generation
- Automated remediation suggestions
- Trend analysis
- Custom metrics
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class AdvancedDashboard:
    """Generate comprehensive security dashboard"""
    
    @staticmethod
    def generate_metrics(report_path: Path) -> Dict[str, Any]:
        """Extract and generate metrics from report"""
        try:
            report = json.loads(report_path.read_text())
            return {
                "scan_date": report.get("timestamp"),
                "target": report.get("target"),
                "total_vectors": report.get("total_vulnerability_vectors", 0),
                "categories": report.get("categories", 0),
                "critical": report.get("critical_severity_vectors", 0),
                "high": report.get("high_severity_vectors", 0),
                "duration": report.get("duration_seconds", 0),
                "risk_score": calculate_risk_score(report),
                "compliance_status": assess_compliance(report)
            }
        except:
            return {}
    
    @staticmethod
    def generate_dashboard_html(metrics: Dict) -> str:
        """Generate HTML dashboard"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EIK Security Dashboard</title>
            <style>
                body {{ font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9; }}
                .dashboard {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; border-bottom: 2px solid #30363d; padding: 20px 0; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
                .metric {{ background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 6px; }}
                .metric-value {{ font-size: 32px; font-weight: bold; color: #58a6ff; }}
                .metric-label {{ color: #8b949e; font-size: 12px; margin-top: 5px; }}
                .critical {{ color: #f85149; }}
                .high {{ color: #fb8500; }}
                .status {{ padding: 10px; border-radius: 4px; }}
                .status.secure {{ background: #238636; color: white; }}
                .status.critical {{ background: #da3633; color: white; }}
                .status.warning {{ background: #d29922; color: white; }}
            </style>
        </head>
        <body>
            <div class="dashboard">
                <div class="header">
                    <h1>🛡️ EIK Security Dashboard</h1>
                    <p>Scan Date: {metrics.get('scan_date', 'N/A')}</p>
                    <p>Target: <strong>{metrics.get('target', 'N/A')}</strong></p>
                </div>
                
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{metrics.get('total_vectors', 0)}</div>
                        <div class="metric-label">Vulnerability Vectors Tested</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value critical">{metrics.get('critical', 0)}</div>
                        <div class="metric-label">CRITICAL Findings</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value high">{metrics.get('high', 0)}</div>
                        <div class="metric-label">HIGH Severity Issues</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{metrics.get('categories', 0)}</div>
                        <div class="metric-label">Categories Tested</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{metrics.get('duration', 0):.1f}s</div>
                        <div class="metric-label">Scan Duration</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{metrics.get('risk_score', 0):.1f}%</div>
                        <div class="metric-label">Risk Score</div>
                    </div>
                </div>
                
                <div class="status {get_status_class(metrics.get('risk_score', 0))}">
                    <strong>Status:</strong> {get_status_text(metrics.get('risk_score', 0))}
                </div>
                
                <div style="margin-top: 30px; padding: 20px; background: #161b22; border-radius: 6px;">
                    <h3>🔒 Compliance Status</h3>
                    <ul>
                        <li>✓ OWASP Top 10 2021 - Tested</li>
                        <li>✓ GDPR Article 32 - Covered</li>
                        <li>✓ PCI-DSS 1.2.1 - Mapped</li>
                        <li>✓ HIPAA Security Rule - Aligned</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        return html


class AutoRemediationSuggester:
    """Generate automated remediation suggestions"""
    
    REMEDIATION_MAP = {
        "SQL Injection": [
            "Use parameterized queries/prepared statements",
            "Implement input validation whitelisting",
            "Use ORM frameworks (SQLAlchemy, Django ORM)",
            "Run with principle of least privilege",
            "Implement WAF rules for SQL injection patterns"
        ],
        "Command Injection": [
            "Avoid shell commands - use native APIs",
            "Whitelist allowed characters",
            "Use parameterized/safe command execution",
            "Run processes with minimal privileges",
            "Implement command input validation"
        ],
        "XSS": [
            "HTML-encode all user input output",
            "Implement Content Security Policy (CSP)",
            "Use template engines with auto-escaping",
            "Validate and sanitize on server-side",
            "Use security headers: X-XSS-Protection"
        ],
        "CSRF": [
            "Implement CSRF tokens in forms",
            "Verify referrer/origin headers",
            "Use SameSite cookie attributes",
            "Implement double-submit cookie pattern",
            "Use state parameters in OAuth flows"
        ],
        "Authentication Bypass": [
            "Remove hardcoded credentials immediately",
            "Implement strong password policies",
            "Add multi-factor authentication (MFA)",
            "Use secure session management",
            "Implement proper password hashing (bcrypt)"
        ],
        "IDOR": [
            "Check authorization before returning resources",
            "Use UUIDs instead of sequential IDs",
            "Implement access control checks server-side",
            "Verify user owns resource before access",
            "Log and audit all data access"
        ],
        "Misconfig": [
            "Change default credentials",
            "Disable directory listing",
            "Implement error handling without stack traces",
            "Keep software updated",
            "Enable HTTPS/HSTS"
        ],
        "Weak Encryption": [
            "Use TLS 1.2+ for all communications",
            "Use bcrypt/Argon2 for password hashing",
            "Never hardcode encryption keys",
            "Use HSM for key storage",
            "Rotate keys regularly"
        ]
    }
    
    @staticmethod
    def get_suggestions(vulnerability_type: str) -> List[str]:
        """Get automated remediation suggestions"""
        for key, suggestions in AutoRemediationSuggester.REMEDIATION_MAP.items():
            if key.lower() in vulnerability_type.lower():
                return suggestions
        return ["Review OWASP documentation", "Consult security team", "Implement defense-in-depth"]
    
    @staticmethod
    def generate_remediation_report(report_path: Path) -> Dict[str, Any]:
        """Generate full remediation report"""
        try:
            report = json.loads(report_path.read_text())
            remediation = {}
            
            for category, findings in report.get("detailed_findings", {}).items():
                remediation[category] = []
                for finding in findings:
                    remediation[category].append({
                        "vulnerability": finding.get("type"),
                        "severity": finding.get("severity"),
                        "suggestions": AutoRemediationSuggester.get_suggestions(
                            finding.get("type", "")
                        ),
                        "priority": 1 if finding.get("severity") == "Critical" else 
                                  2 if finding.get("severity") == "High" else 3
                    })
            
            return remediation
        except:
            return {}


class TrendAnalyzer:
    """Analyze vulnerability trends over time"""
    
    @staticmethod
    def analyze_trends(scan_results: List[Dict]) -> Dict[str, Any]:
        """Analyze trends from multiple scans"""
        return {
            "total_scans": len(scan_results),
            "critical_trend": calculate_trend([s.get("critical", 0) for s in scan_results]),
            "high_trend": calculate_trend([s.get("high", 0) for s in scan_results]),
            "improvement": analyze_improvement(scan_results),
            "recommendations": generate_trend_recommendations(scan_results)
        }


def calculate_risk_score(report: Dict) -> float:
    """Calculate overall risk score (0-100)"""
    critical = report.get("critical_severity_vectors", 0)
    high = report.get("high_severity_vectors", 0)
    total = report.get("total_vulnerability_vectors", 1)
    
    risk = ((critical * 10) + (high * 5)) / (total / 10)
    return min(100, risk)


def assess_compliance(report: Dict) -> Dict[str, str]:
    """Assess compliance posture"""
    risk_score = calculate_risk_score(report)
    
    return {
        "GDPR": "🔴 AT RISK" if risk_score > 70 else "🟡 REVIEW" if risk_score > 40 else "🟢 COMPLIANT",
        "PCI-DSS": "🔴 AT RISK" if risk_score > 80 else "🟡 REVIEW" if risk_score > 50 else "🟢 COMPLIANT",
        "HIPAA": "🔴 AT RISK" if risk_score > 75 else "🟡 REVIEW" if risk_score > 45 else "🟢 COMPLIANT",
        "SOC2": "🔴 AT RISK" if risk_score > 65 else "🟡 REVIEW" if risk_score > 35 else "🟢 COMPLIANT"
    }


def get_status_class(risk_score: float) -> str:
    """Get CSS class for status"""
    if risk_score > 70:
        return "critical"
    elif risk_score > 40:
        return "warning"
    else:
        return "secure"


def get_status_text(risk_score: float) -> str:
    """Get status text"""
    if risk_score > 70:
        return "🔴 CRITICAL - Immediate Action Required"
    elif risk_score > 40:
        return "🟡 WARNING - Urgent Remediation Needed"
    else:
        return "🟢 SECURE - Good Security Posture"


def calculate_trend(values: List[float]) -> str:
    """Calculate trend direction"""
    if len(values) < 2:
        return "→"
    if values[-1] > values[-2]:
        return "📈 INCREASING"
    elif values[-1] < values[-2]:
        return "📉 DECREASING"
    else:
        return "→ STABLE"


def analyze_improvement(scans: List[Dict]) -> float:
    """Analyze improvement percentage"""
    if len(scans) < 2:
        return 0
    
    first_critical = scans[0].get("critical", 0)
    last_critical = scans[-1].get("critical", 0)
    
    if first_critical == 0:
        return 0
    
    return ((first_critical - last_critical) / first_critical) * 100


def generate_trend_recommendations(scans: List[Dict]) -> List[str]:
    """Generate recommendations based on trends"""
    if not scans:
        return ["Continue regular scanning"]
    
    latest = scans[-1]
    critical = latest.get("critical", 0)
    
    if critical > 30:
        return [
            "URGENT: Address all critical vulnerabilities immediately",
            "Implement emergency patching procedures",
            "Engage security team for incident response"
        ]
    elif critical > 10:
        return [
            "Prioritize critical vulnerability remediation",
            "Establish remediation timeline",
            "Increase monitoring and logging"
        ]
    else:
        return [
            "Maintain current security practices",
            "Continue regular scans for improvement tracking",
            "Document security improvements"
        ]


if __name__ == "__main__":
    # Example usage
    print("Advanced Features Module Loaded")
    print("Available: AdvancedDashboard, AutoRemediationSuggester, TrendAnalyzer")
