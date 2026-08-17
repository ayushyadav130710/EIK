import argparse
import json
import unittest

from EIK import (Finding, ReportModule, Runner, Target, _scope_entry_matches,
                 prepare_engagement)


class EngagementControlTests(unittest.TestCase):
    def test_scope_entries_cover_expected_hosts_and_networks(self):
        self.assertTrue(_scope_entry_matches("api.example.com", "example.com"))
        self.assertTrue(_scope_entry_matches("api.example.com", ".example.com"))
        self.assertFalse(_scope_entry_matches("example.com", ".example.com"))
        self.assertFalse(_scope_entry_matches("notexample.com", "example.com"))
        self.assertTrue(_scope_entry_matches("10.10.4.22", "10.10.0.0/16"))
        self.assertFalse(_scope_entry_matches("10.11.4.22", "10.10.0.0/16"))

    def test_live_run_requires_an_authorization_contract(self):
        args = argparse.Namespace(dry_run=False, authorized=False, engagement_id=None,
                                  scope=None, allow_active=False)
        with self.assertRaisesRegex(ValueError, "live runs require"):
            prepare_engagement(args, Target("https://example.com"), self.tmp, [1])

    def test_valid_engagement_writes_auditable_manifest(self):
        scope = self.tmp / "scope.txt"
        scope.write_text("# approved target\nexample.com\n", encoding="utf-8")
        args = argparse.Namespace(dry_run=False, authorized=True, engagement_id="SOW-42",
                                  scope=str(scope), allow_active=False)
        prepare_engagement(args, Target("https://api.example.com/health"), self.tmp, [1, 7])
        manifest = json.loads((self.tmp / "run_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["engagement_id"], "SOW-42")
        self.assertEqual(manifest["target_host"], "api.example.com")
        self.assertEqual(manifest["modules"], [1, 7])

    def test_active_modules_need_separate_opt_in(self):
        scope = self.tmp / "scope.txt"
        scope.write_text("example.com\n", encoding="utf-8")
        args = argparse.Namespace(dry_run=False, authorized=True, engagement_id="SOW-42",
                                  scope=str(scope), allow_active=False)
        with self.assertRaisesRegex(ValueError, "--allow-active"):
            prepare_engagement(args, Target("example.com"), self.tmp, [5])

    def test_reports_deduplicate_and_export_sarif(self):
        report = ReportModule(Runner(self.tmp), Target("https://example.com"), sarif=True)
        finding = Finding("Missing CSP", "Medium", evidence="https://example.com/")
        report.findings = [finding, finding]
        report._deduplicate()
        self.assertEqual(len(report.findings), 1)
        sarif = json.loads(report._write_sarif().read_text(encoding="utf-8"))
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertEqual(len(sarif["runs"][0]["results"]), 1)

    def test_http_baseline_artifact_becomes_a_report_finding(self):
        web = self.tmp / "web"
        web.mkdir()
        (web / "http_baseline.json").write_text(json.dumps({"findings": [{
            "title": "Missing HSTS header", "severity": "Medium",
            "description": "HTTPS response has no HSTS.", "evidence": "",
            "remediation": "Set HSTS.",
        }]}), encoding="utf-8")
        report = ReportModule(Runner(self.tmp), Target("https://example.com"))
        report._from_http_baseline()
        self.assertEqual(report.findings[0].title, "Missing HSTS header")
        self.assertEqual(report.findings[0].severity, "Medium")

    def setUp(self):
        import tempfile
        self.tempdir = tempfile.TemporaryDirectory()
        self.tmp = __import__("pathlib").Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()
