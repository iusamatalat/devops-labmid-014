import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import create_app


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        self.app = create_app(self.database_path)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.valid_data = {
            "student_name": "Usama Talat",
            "registration_number": "014",
            "assignment_title": "DevOps Lab Mid",
            "submission_url": "https://example.com/assignment-014",
        }

    def saved_rows(self):
        database = sqlite3.connect(self.database_path)
        try:
            return database.execute(
                """SELECT student_name, registration_number,
                assignment_title, submission_url FROM submissions"""
            ).fetchall()
        finally:
            database.close()

    def test_valid_submission_is_saved_and_displayed(self):
        response = self.client.post("/", data=self.valid_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Submission saved.", response.data)
        self.assertEqual(self.saved_rows(), [tuple(self.valid_data.values())])

        # A separate GET verifies the saved record appears in the list.
        page = self.client.get("/").get_data(as_text=True)
        for value in self.valid_data.values():
            self.assertIn(value, page)

    def test_missing_registration_number_is_rejected(self):
        data = self.valid_data.copy()
        data.pop("registration_number")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Registration number is required.", response.data)
        self.assertEqual(self.saved_rows(), [])

    def test_invalid_submission_url_is_rejected(self):
        data = self.valid_data.copy()
        data["submission_url"] = "not-a-url"
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            b"Enter a valid http:// or https:// submission URL.", response.data
        )
        self.assertEqual(self.saved_rows(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
