import json
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path


REPORT_PATH = Path(__file__).resolve().parent / "reports" / "test-results.json"


def build_message(report, sender, recipient):
    summary = report["summary"]
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = (
        f"[DevOps 014] {report['overall_status'].upper()} "
        f"{report['repository']} {report['commit_sha'][:7]}"
    )
    lines = [
        f"Repository: {report['repository']}",
        f"Branch: {report['branch']}",
        f"Commit: {report['commit_sha']}",
        f"Run: {report['pipeline_run_id']} (attempt {report.get('run_attempt', '1')})",
        f"Executed: {report['execution_timestamp']}",
        f"Overall result: {report['overall_status']}",
        f"Tests: {summary['total']} total, {summary['passed']} passed, {summary['failed']} failed",
        "",
        "Individual results:",
    ]
    lines.extend(f"- {test['name']}: {test['result']}" for test in report["tests"])
    lines.extend(["", "The attached JSON includes the complete results and failure messages."])
    message.set_content("\n".join(lines))
    message.add_attachment(
        (json.dumps(report, indent=2) + "\n").encode("utf-8"),
        maintype="application", subtype="json", filename="test-report.json",
    )
    return message


def main():
    required = ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("Missing email configuration: " + ", ".join(missing), file=sys.stderr)
        return 1

    try:
        port = int(os.getenv("SMTP_PORT") or "465")
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        message = build_message(report, os.environ["SMTP_USER"], os.environ["EMAIL_TO"])
        context = ssl.create_default_context()
        if port == 465:
            connection = smtplib.SMTP_SSL(
                os.environ["SMTP_HOST"], port, timeout=30, context=context
            )
        else:
            connection = smtplib.SMTP(os.environ["SMTP_HOST"], port, timeout=30)

        with connection as server:
            if port != 465:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            server.send_message(message)
    except (OSError, ValueError, KeyError, smtplib.SMTPException) as error:
        print(f"Email delivery failed: {error}", file=sys.stderr)
        return 1

    print("The test report was sent by email.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
