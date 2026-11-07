# DevOps Lab Mid - 014

A minimal assignment submission portal built with Flask and SQLite.
The project contains the application, three required tests, a GitHub Actions
workflow, and automatic HTTP delivery of the actual test report to your computer.
It also includes optional GitHub Pages deployment and email reporting. Enable
each bonus only after its account configuration below is complete.

## Setup on Windows PowerShell

Run from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The environment's Python is called directly; activation is optional.

## Run the application

```powershell
.\.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:5000 in a browser. Stop the server with Ctrl+C.
Valid submissions persist in `submissions.db` beside `app.py`.

## Run the tests

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

Tests use a new temporary database for each case. They do not change the
application's saved submissions. No browser or running web server is needed.

1. Valid details: save the submission and display it in the submission list.
2. Missing registration number: return a validation message and save nothing.
3. Invalid submission URL: return a validation message and save nothing.

## Generate and receive the actual JSON report

In terminal A, from the project folder:

```powershell
.\.venv\Scripts\python.exe receiver.py
```

Keep it running. It listens on `http://127.0.0.1:8001/report`.
The latest received report is saved outside the project and runner checkout at:

```text
C:\Users\YOUR_WINDOWS_USER\DevOpsLabMidReports\test-report.json
```

The receiver also archives every run by its pipeline run ID and attempt number.
This preserves passing, failing, and corrected evidence when the latest file changes.

In terminal B, from the same project folder:

```powershell
.\.venv\Scripts\python.exe run_tests.py
.\.venv\Scripts\python.exe send_report.py
Get-Content "$env:USERPROFILE\DevOpsLabMidReports\test-report.json"
```

`run_tests.py` runs the tests and writes `reports/test-results.json` using their
actual results. It exits with code 1 when tests fail, are skipped, or fewer than
three tests pass. `send_report.py` POSTs this JSON to the HTTP receiver, which
automatically writes `test-report.json`. Viewing the received file is only an
inspection step; no manual file copying or downloading is involved in delivery.

Locally, a run has a unique `local-...` identifier. In GitHub Actions the script
uses the actual repository, branch, commit SHA, run ID, and attempt supplied by
GitHub, together with a UTC execution timestamp. Each test includes its name,
result, and failure traceback if applicable. The report includes total, passed,
failed, and skipped counts and the overall status.

## GitHub Actions and localhost

The workflow is `.github/workflows/ci.yml`. It triggers on every push and uses a
Windows x64 self-hosted runner on your computer. This makes the receiver on your
computer reachable through `127.0.0.1`; a GitHub-hosted runner has a different
localhost. Keep the receiver and runner running during the demonstration.

1. Create an empty GitHub repository for this project. A public repository allows
   the later GitHub Pages bonus on GitHub Free. Leave the generated README,
   license, and .gitignore options unchecked because these files already exist.
2. In that repository open Settings > Actions > Runners > New self-hosted runner.
   Select Windows and x64. Use the download and configuration commands shown by
   GitHub, including its current version, hash, and temporary registration token.
3. Install the runner in its own directory, such as `D:\actions-runner-labmid-014`,
   outside the project. Keep the default `self-hosted`, `Windows`, and `X64` labels.
   Run it interactively using `run.cmd`; service installation is unnecessary.
4. Start the receiver in a separate terminal. Verify the runner terminal says
   `Listening for Jobs` before pushing the project.
5. Initialize Git in the project folder, commit the source, connect the empty
   repository, and push. If a runner is offline, the job waits until it is online.

The runner needs Python and Git available on PATH under the same Windows account
used for the portal. The workflow uses Windows PowerShell and creates a separate
Python environment in the runner checkout.

A failed test step remains failed. The report delivery step uses `always()` and
checks that the test step ran, so it still delivers results after a test failure.
No `continue-on-error` setting hides the failing result.

## Passing, failing, and corrected demonstrations

Capture evidence after each push before starting the next demonstration:

1. Push the working code. Confirm three passing tests in GitHub Actions and the
   received JSON with matching commit SHA/run ID and overall status `passed`.
2. Introduce an application defect in `validate_submission`: replace
   `if not data[field]:` with
   `if field != "registration_number" and not data[field]:`. This bypasses
   registration-number validation. Push it. The missing-registration test must
   fail, the test stage must fail, and the receiver must save the failing report.
3. Restore the original line and push. Confirm all three tests pass again and the
   receiver saves a new passing report for the corrected commit.

Use the application defect only for the controlled failing demonstration and
finish with the corrected code.

The initial connection-refused error during report delivery does not demonstrate
an application test failure: in that run the tests passed. If the deliberate
application-defect and correction demonstration is omitted, that requirement
remains unfulfilled even if the final workflow is green.

## Enable the GitHub Pages bonus

1. On GitHub open Settings > Pages. Under Build and deployment, select
   GitHub Actions as the source.
2. Open Settings > Secrets and variables > Actions > Variables. Add the repository
   variable `ENABLE_PAGES` with the value `true` (lowercase).
3. Push the update to `main`. After the test/reporting job succeeds, the separate
   deployment job publishes the `demo` folder. Its environment displays the URL.

For this repository the expected address after successful deployment is:

https://iusamatalat.github.io/devops-labmid-014/

GitHub Pages hosts the static browser demo. It stores submissions in that
browser's localStorage. The local Flask application continues to use SQLite.
The deployment job depends on a successful test/reporting job and a push to
`main`. When that job fails, deployment is skipped and the published site is
unchanged. If `ENABLE_PAGES` is absent, the optional deployment job is skipped.

## Enable the email bonus

1. Open Settings > Secrets and variables > Actions > Secrets, then add these
   repository secrets using the SMTP account you control:

| Secret | Value |
| --- | --- |
| `SMTP_HOST` | Your provider's SMTP hostname; Gmail example: `smtp.gmail.com` |
| `SMTP_PORT` | `465` for SMTP over SSL; `587` for STARTTLS |
| `SMTP_USER` | Your sender email address |
| `SMTP_PASSWORD` | Your provider's SMTP credential or app password |
| `EMAIL_TO` | The address that should receive the reports |

2. For a personal Gmail account, enable 2-Step Verification and create an app
   password at https://myaccount.google.com/apppasswords if available. Store its
   16-character value without display spaces in `SMTP_PASSWORD`. Account policy
   can make app passwords unavailable; another authenticated SMTP provider is
   also supported. Keep credentials in GitHub Secrets, not in source files.
3. Under the Actions Variables tab, add `EMAIL_ENABLED` with the value `true`.
4. Push a commit or manually run the workflow. Confirm the email step succeeds
   and the message arrives at `EMAIL_TO` with `test-report.json` attached.

The email step runs after both passing and failing test stages through an
`always()` condition. It contains the commit SHA, overall status, test counts,
individual results, and the full JSON attachment. When `EMAIL_ENABLED` is absent,
this optional step is skipped and no email is sent. Enabling it before the SMTP
secrets are configured will cause an email configuration error.

## Daily demonstration terminals

Keep `receiver.py` and the self-hosted runner's `run.cmd` running in separate
terminals before each push. A receiver health check is:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```

The expected value is `receiver_status: ready`. This prevents the previously
observed connection-refused error from a stopped receiver. Use a third terminal
for Git commands. The report receiver archives each run and attempt separately.

## Submission evidence

Submit the repository URL and this README with screenshots of the portal and
the three required demonstrations. For each demonstration, capture the workflow
result and the automatically received local JSON with matching commit and run ID.
For the bonuses, include the live Pages URL, deployment evidence, and received
email evidence. Code configuration alone is not evidence that the external
deployment or email delivery has completed.

## References

- Flask quickstart: https://flask.palletsprojects.com/en/stable/quickstart/
- Self-hosted runners: https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners
- GitHub Pages workflows: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Python SMTP: https://docs.python.org/3.14/library/smtplib.html
- Gmail app passwords: https://support.google.com/accounts/answer/185833

## How the application works

- GET `/` reads submissions from SQLite and renders the page.
- POST `/` receives the form and checks all required fields on the server.
- Submission URLs must use HTTP or HTTPS, have a host, and have no whitespace.
- Invalid input returns HTTP 400 and an error message without an INSERT.
- Valid input is inserted using SQL placeholders, then committed.
- A redirect after a successful POST displays the updated list and avoids
  submitting the same form again when the browser page is refreshed.
- The form has `novalidate` so server-side validation can be demonstrated
  even for missing inputs or malformed links.
- `create_app(database_path)` lets each automated test use its own database.

## File guide

| File | Purpose |
| --- | --- |
| `app.py` | Routes, validation, and database operations |
| `templates/index.html` | Plain form, validation messages, and submission list |
| `test_app.py` | The three required automated tests |
| `requirements.txt` | Flask dependency |
| `.gitignore` | Excludes environments, generated databases, and local files |
| `run_tests.py` | Runs tests, collects individual results, and writes JSON |
| `send_report.py` | Sends the completed JSON report to the HTTP receiver |
| `receiver.py` | Receives reports, saves the latest JSON, and archives runs |
| `.github/workflows/ci.yml` | Tests each pushed revision and delivers reports |
| `email_report.py` | Sends the actual results and JSON attachment over authenticated SMTP |
| `demo/index.html` | Static browser demo published to GitHub Pages |
