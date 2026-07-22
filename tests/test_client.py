import unittest
from unittest.mock import MagicMock, patch

import requests

from patra_toolkit import client
from patra_toolkit.exceptions import PatraDatasheetExistsError, PatraModelExistsError, PatraSubmissionError


def _mock_response(status_code=200, json_data=None, ok=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = ok if ok is not None else 200 <= status_code < 300
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text
    return resp


class ClientReadTestCase(unittest.TestCase):

    @patch("requests.request")
    def test_list_model_cards_success(self, mock_request):
        mock_request.return_value = _mock_response(200, [{"uuid": "abc", "name": "Model A"}])
        result = client.list_model_cards("http://localhost:8000", token="tok")
        self.assertEqual(result, [{"uuid": "abc", "name": "Model A"}])
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], "http://localhost:8000/modelcards")
        self.assertEqual(kwargs["headers"]["X-Tapis-Token"], "tok")

    @patch("requests.request")
    def test_list_model_cards_no_token_omits_header(self, mock_request):
        mock_request.return_value = _mock_response(200, [])
        client.list_model_cards("http://localhost:8000")
        _, kwargs = mock_request.call_args
        self.assertNotIn("X-Tapis-Token", kwargs["headers"])

    @patch("requests.request")
    def test_get_model_card_success(self, mock_request):
        mock_request.return_value = _mock_response(200, {"uuid": "abc", "name": "Model A"})
        result = client.get_model_card("http://localhost:8000", "abc")
        self.assertEqual(result["uuid"], "abc")

    @patch("requests.request")
    def test_get_model_card_not_found_raises_submission_error(self, mock_request):
        mock_request.return_value = _mock_response(404, {"detail": "not found"}, ok=False)
        with self.assertRaises(PatraSubmissionError):
            client.get_model_card("http://localhost:8000", "missing")

    @patch("requests.request")
    def test_list_datasheets_success(self, mock_request):
        mock_request.return_value = _mock_response(200, [{"uuid": "ds1", "title": "Dataset A"}])
        result = client.list_datasheets("http://localhost:8000")
        self.assertEqual(result[0]["title"], "Dataset A")

    @patch("requests.request")
    def test_get_datasheet_success(self, mock_request):
        mock_request.return_value = _mock_response(200, {"uuid": "ds1"})
        result = client.get_datasheet("http://localhost:8000", "ds1")
        self.assertEqual(result["uuid"], "ds1")


class ClientSubmitTestCase(unittest.TestCase):

    @patch("requests.request")
    def test_submit_model_card_success(self, mock_request):
        mock_request.return_value = _mock_response(
            201, {"asset_type": "model_card", "asset_uuid": "new-uuid", "created": True})
        result = client.submit_model_card("http://localhost:8000", {"name": "Model A"}, token="tok")
        self.assertEqual(result["asset_uuid"], "new-uuid")

    @patch("requests.request")
    def test_submit_model_card_duplicate_raises_model_exists(self, mock_request):
        mock_request.return_value = _mock_response(409, {"detail": "Model card already exists"}, ok=False)
        with self.assertRaises(PatraModelExistsError):
            client.submit_model_card("http://localhost:8000", {"name": "Model A"})

    @patch("requests.request")
    def test_submit_model_card_validation_error_raises_submission_error(self, mock_request):
        mock_request.return_value = _mock_response(422, {"detail": [{"msg": "bad field"}]}, ok=False)
        with self.assertRaises(PatraSubmissionError):
            client.submit_model_card("http://localhost:8000", {"name": "Model A"})

    @patch("requests.request")
    def test_submit_datasheet_duplicate_raises_datasheet_exists(self, mock_request):
        mock_request.return_value = _mock_response(409, {"detail": "Datasheet already exists"}, ok=False)
        with self.assertRaises(PatraDatasheetExistsError):
            client.submit_datasheet("http://localhost:8000", {"titles": []})

    @patch("requests.request")
    def test_submit_datasheet_success(self, mock_request):
        mock_request.return_value = _mock_response(
            201, {"asset_type": "datasheet", "asset_uuid": "ds-uuid", "created": True})
        result = client.submit_datasheet("http://localhost:8000", {"titles": []})
        self.assertEqual(result["asset_uuid"], "ds-uuid")

    @patch("requests.request")
    def test_connection_error_raises_submission_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.ConnectionError("boom")
        with self.assertRaises(PatraSubmissionError):
            client.list_model_cards("http://localhost:8000")


if __name__ == '__main__':
    unittest.main()
