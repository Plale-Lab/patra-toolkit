import json
import os
import unittest
from unittest.mock import patch

from patra_toolkit import Datasheet
from patra_toolkit.exceptions import PatraDatasheetExistsError, PatraSubmissionError


class DatasheetTestCase(unittest.TestCase):

    def setUp(self):
        self.ds = Datasheet(publication_year=2025, version="1.0")
        self.ds.add_title("My Dataset")
        self.ds.add_creator("Jane Doe")
        self.ds_save_location = "./test_ds.json"

    def tearDown(self):
        if os.path.exists(self.ds_save_location):
            os.remove(self.ds_save_location)

    def test_builder_methods(self):
        self.ds.add_subject("machine learning")
        self.ds.add_description("A test dataset", "Abstract")
        self.ds.add_date("2025-01-01", "Issued")
        self.ds.add_funding_reference("NSF", award_number="12345")
        self.ds.set_publisher("Test Publisher")

        self.assertEqual(len(self.ds.subjects), 1)
        self.assertEqual(self.ds.subjects[0].subject, "machine learning")
        self.assertEqual(len(self.ds.descriptions), 1)
        self.assertEqual(len(self.ds.dates), 1)
        self.assertEqual(len(self.ds.funding_references), 1)
        self.assertEqual(self.ds.funding_references[0].award_number, "12345")
        self.assertEqual(self.ds.publisher.name, "Test Publisher")

    def test_json_round_trip(self):
        ds_json = str(self.ds)
        parsed = json.loads(ds_json)
        self.assertEqual(parsed["titles"][0]["title"], "My Dataset")
        self.assertEqual(parsed["creators"][0]["creator_name"], "Jane Doe")
        self.assertEqual(parsed["publication_year"], 2025)

    def test_validate_true_with_title_and_creator(self):
        self.assertTrue(self.ds.validate())

    def test_validate_false_when_empty(self):
        empty_ds = Datasheet()
        self.assertFalse(empty_ds.validate())

    def test_validate_false_missing_creator_only(self):
        ds = Datasheet()
        ds.add_title("Only A Title")
        self.assertFalse(ds.validate())

    def test_save_writes_json_file(self):
        self.ds.save(self.ds_save_location)
        self.assertTrue(os.path.exists(self.ds_save_location))
        with open(self.ds_save_location) as f:
            saved = json.load(f)
        self.assertEqual(saved["titles"][0]["title"], "My Dataset")

    @patch("patra_toolkit.client.submit_datasheet")
    def test_submit_success_sets_uuid(self, mock_submit):
        mock_submit.return_value = {"asset_type": "datasheet", "asset_uuid": "new-ds-uuid", "created": True}
        result = self.ds.submit("http://localhost:8000", token="tok")
        self.assertEqual(self.ds.uuid, "new-ds-uuid")
        self.assertEqual(result["asset_uuid"], "new-ds-uuid")
        mock_submit.assert_called_once()

    @patch("patra_toolkit.client.submit_datasheet")
    def test_submit_validation_failure_raises_without_network_call(self, mock_submit):
        empty_ds = Datasheet()
        with self.assertRaises(PatraSubmissionError):
            empty_ds.submit("http://localhost:8000")
        mock_submit.assert_not_called()

    @patch("patra_toolkit.client.submit_datasheet")
    def test_submit_duplicate_propagates(self, mock_submit):
        mock_submit.side_effect = PatraDatasheetExistsError("Datasheet already exists with id 1")
        with self.assertRaises(PatraDatasheetExistsError):
            self.ds.submit("http://localhost:8000")


if __name__ == '__main__':
    unittest.main()
