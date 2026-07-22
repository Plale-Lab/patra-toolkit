import unittest
from unittest.mock import patch

from patra_toolkit import AIModel, BiasAnalysis, ExplainabilityAnalysis, ModelCard
from patra_toolkit.exceptions import PatraModelExistsError, PatraSubmissionError


class ModelCardSubmitTestCase(unittest.TestCase):

    def setUp(self):
        self.mc = ModelCard(name="TestModel", category="classification",
                             ai_model=AIModel(name="TestAIModel"))

    @patch("patra_toolkit.client.submit_model_card")
    def test_submit_success_sets_uuid(self, mock_submit):
        mock_submit.return_value = {"asset_type": "model_card", "asset_uuid": "new-uuid", "created": True}
        result = self.mc.submit("http://localhost:8000", token="tok")
        self.assertEqual(self.mc.uuid, "new-uuid")
        self.assertEqual(result["asset_uuid"], "new-uuid")
        mock_submit.assert_called_once()

    @patch("patra_toolkit.client.submit_model_card")
    def test_submit_validation_failure_raises_without_network_call(self, mock_submit):
        bad_mc = ModelCard(name="Bad", category="not-a-real-category")
        with self.assertRaises(PatraSubmissionError):
            bad_mc.submit("http://localhost:8000")
        mock_submit.assert_not_called()

    @patch("patra_toolkit.client.submit_model_card")
    def test_submit_duplicate_propagates(self, mock_submit):
        mock_submit.side_effect = PatraModelExistsError("Model card already exists")
        with self.assertRaises(PatraModelExistsError):
            self.mc.submit("http://localhost:8000")

    @patch("patra_toolkit.client.submit_model_card")
    def test_submit_strips_bias_and_xai_from_payload(self, mock_submit):
        mock_submit.return_value = {"asset_type": "model_card", "asset_uuid": "new-uuid", "created": True}
        self.mc.bias_analysis = BiasAnalysis(0.1, 0.2)
        self.mc.xai_analysis = ExplainabilityAnalysis("SHAP")
        self.mc.submit("http://localhost:8000")

        sent_payload = mock_submit.call_args[0][1]
        self.assertNotIn("bias_analysis", sent_payload)
        self.assertNotIn("xai_analysis", sent_payload)

    @patch("patra_toolkit.client.submit_model_card")
    def test_submit_strips_bias_and_xai_when_unset(self, mock_submit):
        # Default case: nothing calls populate_bias()/populate_xai(), so these
        # fields are None -- confirm they're still stripped rather than sent as null.
        mock_submit.return_value = {"asset_type": "model_card", "asset_uuid": "new-uuid", "created": True}
        self.mc.submit("http://localhost:8000")

        sent_payload = mock_submit.call_args[0][1]
        self.assertNotIn("bias_analysis", sent_payload)
        self.assertNotIn("xai_analysis", sent_payload)


if __name__ == '__main__':
    unittest.main()
