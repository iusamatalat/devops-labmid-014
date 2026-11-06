import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


DEFAULT_OUTPUT = Path.home() / "DevOpsLabMidReports"


def write_json(path, report):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class ReportHandler(BaseHTTPRequestHandler):
    def reply(self, status, body):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            self.reply(200, {"receiver_status": "ready"})
        else:
            self.reply(404, {"error": "Use POST /report or GET /health."})

    def do_POST(self):
        if self.path != "/report":
            self.reply(404, {"error": "Unknown endpoint."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1_000_000:
                raise ValueError("Report body must be between 1 byte and 1 MB.")
            report = json.loads(self.rfile.read(length))
            required = {
                "repository", "branch", "commit_sha", "pipeline_run_id",
                "execution_timestamp", "tests", "summary", "overall_status",
            }
            if not isinstance(report, dict) or not required.issubset(report):
                raise ValueError("Missing required test report fields.")
            if not isinstance(report["tests"], list) or not isinstance(report["summary"], dict):
                raise ValueError("The report must contain individual tests and a summary.")
            if report["overall_status"] not in ("passed", "failed"):
                raise ValueError("Invalid overall test status.")
        except (ValueError, UnicodeError) as error:
            self.reply(400, {"error": str(error)})
            return

        output = self.server.output_directory
        run_id = re.sub(r"[^a-zA-Z0-9_-]", "_", str(report["pipeline_run_id"]))[:100] or "unknown"
        attempt = re.sub(r"[^a-zA-Z0-9_-]", "_", str(report.get("run_attempt", "1")))[:30] or "1"
        archive = output / f"run-{run_id}-attempt-{attempt}.json"
        latest = output / "test-report.json"

        try:
            write_json(archive, report)
            write_json(latest, report)
        except OSError as error:
            self.reply(500, {"error": f"Could not save the report: {error}"})
            return

        print(f"Received run {run_id}: {report['overall_status']} - saved {latest}", flush=True)
        self.reply(200, {"received": True, "saved_to": str(latest), "archive": str(archive)})


def create_receiver(output_directory=DEFAULT_OUTPUT, port=8001):
    output_directory = Path(output_directory).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    server = HTTPServer(("127.0.0.1", port), ReportHandler)
    server.output_directory = output_directory
    return server


def main():
    parser = argparse.ArgumentParser(description="Receive completed test reports over HTTP.")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    server = create_receiver(args.output_dir, args.port)
    print(f"Receiver: http://127.0.0.1:{server.server_port}/report", flush=True)
    print(f"Latest report: {server.output_directory / 'test-report.json'}", flush=True)
    print("Keep this terminal running during the demonstration. Ctrl+C stops it.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
