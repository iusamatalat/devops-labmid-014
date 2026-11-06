import argparse
import os
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="POST the actual test report to the receiver.")
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "test-results.json")
    parser.add_argument("--url", default=os.getenv("REPORT_URL") or "http://127.0.0.1:8001/report")
    args = parser.parse_args()

    try:
        body = args.report.read_bytes()
    except OSError as error:
        print(f"Cannot read the completed test report: {error}", file=sys.stderr)
        return 1

    for attempt in range(1, 4):
        request = Request(
            args.url, data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                print(response.read().decode("utf-8"))
            return 0
        except (URLError, TimeoutError, OSError) as error:
            print(f"Report delivery attempt {attempt}/3 failed: {error}", file=sys.stderr)
            if attempt < 3:
                time.sleep(1)

    print("Report delivery failed. Check that receiver.py is running.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
