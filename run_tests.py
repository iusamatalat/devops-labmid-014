import json
import os
import subprocess
import sys
import traceback
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPORT_PATH = ROOT / "reports" / "test-results.json"


class ReportResult(unittest.TextTestResult):
    """Record results reported by unittest while keeping normal terminal output."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({
            "name": test.id(), "result": "passed", "failure_message": None
        })

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.record_failure(test, error)

    def addError(self, test, error):
        super().addError(test, error)
        self.record_failure(test, error)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records.append({
            "name": test.id(), "result": "skipped", "failure_message": reason
        })

    def record_failure(self, test, error):
        self.records.append({
            "name": test.id(),
            "result": "failed",
            "failure_message": "".join(traceback.format_exception(*error)),
        })


def git_value(*arguments):
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *arguments],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "local"


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.unlink(missing_ok=True)

    suite = unittest.defaultTestLoader.discover(str(ROOT), pattern="test_app.py")
    result = unittest.TextTestRunner(
        verbosity=2, resultclass=ReportResult
    ).run(suite)

    passed = sum(test["result"] == "passed" for test in result.records)
    failed = sum(test["result"] == "failed" for test in result.records)
    skipped = sum(test["result"] == "skipped" for test in result.records)
    # All required tests must actually execute and pass.
    success = result.wasSuccessful() and passed == result.testsRun and passed >= 3
    now = datetime.now(timezone.utc)

    report = {
        "repository": os.getenv("GITHUB_REPOSITORY") or ROOT.name,
        "branch": os.getenv("GITHUB_REF_NAME") or git_value("branch", "--show-current"),
        "commit_sha": os.getenv("GITHUB_SHA") or git_value("rev-parse", "HEAD"),
        "pipeline_run_id": os.getenv("GITHUB_RUN_ID") or now.strftime("local-%Y%m%dT%H%M%S%fZ"),
        "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT") or "1",
        "execution_timestamp": now.isoformat(),
        "tests": result.records,
        "summary": {
            "total": result.testsRun,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        },
        "overall_status": "passed" if success else "failed",
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nActual test report written to: {REPORT_PATH}", flush=True)
    print(f"Overall status: {report['overall_status']}", flush=True)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
