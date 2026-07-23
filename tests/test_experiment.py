import io
import json
import unittest
from unittest.mock import MagicMock, patch

import torch
import torchvision
from PIL import Image

from patra_toolkit.experiment import (
    _build_event,
    _envelope,
    _extract_image_base_url,
    _iso_to_epoch_millis,
    _kafka_client_config,
    run_experiment,
)

# _load_model() always builds a stock torchvision.models.mobilenet_v2(weights=None), whose
# classifier head defaults to 1000 output classes -- the fixture must match that shape (a real
# deployment's inference_labels would be the real 1000 ImageNet category names).
FIXTURE_CATEGORIES = [f"class_{i}" for i in range(1000)]
MODEL_CARD_FIXTURE = {
    "ai_model": {
        "location": "http://fake-model-host/weights.pth",
        "inference_labels": FIXTURE_CATEGORIES,
    }
}
DATASHEET_FIXTURE = {
    "alternate_identifiers": [
        {"alternate_identifier": "https://fake-picsum.example", "alternate_identifier_type": "URL"}
    ]
}


def _fake_weights_bytes():
    buf = io.BytesIO()
    model = torchvision.models.mobilenet_v2(weights=None)
    torch.save(model.state_dict(), buf)
    return buf.getvalue()


def _fake_image_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), color=(120, 130, 140)).save(buf, format="JPEG")
    return buf.getvalue()


def _mock_requests_get(url, stream=True, timeout=None):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    if "weights" in url:
        resp.content = _fake_weights_bytes()
    else:
        resp.content = _fake_image_bytes()
    return resp


class HelperTestCase(unittest.TestCase):
    """Dependency-free tests for the pure-data helpers."""

    def test_extract_image_base_url(self):
        self.assertEqual(_extract_image_base_url(DATASHEET_FIXTURE), "https://fake-picsum.example")

    def test_extract_image_base_url_missing_raises(self):
        with self.assertRaises(ValueError):
            _extract_image_base_url({"alternate_identifiers": []})

    def test_build_event_fields(self):
        event = _build_event(
            image_name="0.jpg", running_count=1, top_label="cat", top_prob=0.9,
            topk_scores=[{"label": "cat", "probability": 0.9}],
            experiment_id="exp-1", user_id="u1", device_id="d1", model_id="m1",
        )
        self.assertEqual(event["domain"], "digital-ag")
        self.assertEqual(event["model_id"], "m1")
        self.assertEqual(event["label"], "cat")
        self.assertEqual(event["image_count"], 1)
        self.assertIsInstance(json.loads(event["flattened_scores"]), list)

    def test_iso_to_epoch_millis(self):
        self.assertIsNone(_iso_to_epoch_millis(None))
        self.assertEqual(_iso_to_epoch_millis("1970-01-01T00:00:00Z"), 0)

    def test_envelope_converts_timestamps(self):
        event = _build_event(
            image_name="0.jpg", running_count=1, top_label="cat", top_prob=0.9,
            topk_scores=[], experiment_id="exp-1", user_id="u1", device_id="d1", model_id="m1",
        )
        wrapped = _envelope(event)
        self.assertIn("schema", wrapped)
        self.assertIn("payload", wrapped)
        self.assertIsInstance(wrapped["payload"]["image_receiving_timestamp"], int)

    def test_kafka_client_config_ssl_default(self):
        config = _kafka_client_config("broker.example:443", use_ssl=True)
        self.assertEqual(config["security.protocol"], "SSL")

    def test_kafka_client_config_no_ssl(self):
        config = _kafka_client_config("broker.example:9092", use_ssl=False)
        self.assertNotIn("security.protocol", config)


class RunExperimentTestCase(unittest.TestCase):

    @patch("confluent_kafka.admin.AdminClient")
    @patch("confluent_kafka.Producer")
    @patch("requests.get", side_effect=_mock_requests_get)
    @patch("patra_toolkit.client.get_datasheet", return_value=DATASHEET_FIXTURE)
    @patch("patra_toolkit.client.get_model_card", return_value=MODEL_CARD_FIXTURE)
    def test_run_experiment_success(self, mock_get_mc, mock_get_ds, mock_requests_get,
                                     mock_producer_cls, mock_admin_cls):
        mock_admin_cls.return_value.list_topics.return_value = None
        mock_producer = mock_producer_cls.return_value

        result = run_experiment(
            model_card_uuid="mc-uuid", datasheet_uuid="ds-uuid",
            patra_server_url="http://patra.example", ckn_broker_url="broker.example:443",
            user_id="demo-user", num_images=2,
        )

        self.assertEqual(result["num_events_produced"], 2)
        self.assertEqual(len(result["events"]), 2)
        self.assertTrue(result["experiment_id"].startswith("experiment-"))
        self.assertEqual(
            result["results_url"],
            "http://patra.example/experiments/digital-ag/users/demo-user/summary",
        )
        for event in result["events"]:
            self.assertEqual(event["model_id"], "mc-uuid")
            self.assertEqual(event["user_id"], "demo-user")
            self.assertEqual(event["device_id"], "demo-edge-device")
            self.assertEqual(event["domain"], "digital-ag")

        self.assertEqual(mock_producer.produce.call_count, 2)
        self.assertEqual(mock_producer.flush.call_count, 1)

        # Default use_schema_envelope=True: payload sent to Kafka should be enveloped
        # with epoch-millis timestamps, not the raw event's ISO strings.
        sent_payload = json.loads(mock_producer.produce.call_args_list[0][0][1])
        self.assertIn("schema", sent_payload)
        self.assertIsInstance(sent_payload["payload"]["image_receiving_timestamp"], int)

        # Default use_ssl=True: the Producer/AdminClient should be configured for SSL --
        # needed for brokers reached through a TLS-terminating proxy (e.g. Tapis Pods).
        self.assertEqual(mock_producer_cls.call_args[0][0]["security.protocol"], "SSL")
        self.assertEqual(mock_admin_cls.call_args[0][0]["security.protocol"], "SSL")

    @patch("confluent_kafka.admin.AdminClient")
    @patch("confluent_kafka.Producer")
    @patch("requests.get", side_effect=_mock_requests_get)
    @patch("patra_toolkit.client.get_datasheet", return_value=DATASHEET_FIXTURE)
    @patch("patra_toolkit.client.get_model_card", return_value=MODEL_CARD_FIXTURE)
    def test_run_experiment_bare_json_when_envelope_disabled(self, mock_get_mc, mock_get_ds,
                                                               mock_requests_get, mock_producer_cls,
                                                               mock_admin_cls):
        mock_admin_cls.return_value.list_topics.return_value = None
        mock_producer = mock_producer_cls.return_value

        run_experiment(
            model_card_uuid="mc-uuid", datasheet_uuid="ds-uuid",
            patra_server_url="http://patra.example", ckn_broker_url="broker.example:443",
            user_id="demo-user", num_images=1, use_schema_envelope=False,
        )

        sent_payload = json.loads(mock_producer.produce.call_args_list[0][0][1])
        self.assertNotIn("schema", sent_payload)
        self.assertIsInstance(sent_payload["image_receiving_timestamp"], str)

    @patch("confluent_kafka.admin.AdminClient")
    @patch("confluent_kafka.Producer")
    @patch("patra_toolkit.client.get_datasheet", return_value=DATASHEET_FIXTURE)
    @patch("patra_toolkit.client.get_model_card", return_value=MODEL_CARD_FIXTURE)
    def test_run_experiment_broker_unreachable_raises(self, mock_get_mc, mock_get_ds,
                                                        mock_producer_cls, mock_admin_cls):
        mock_admin_cls.return_value.list_topics.side_effect = Exception("connection refused")

        with self.assertRaises(ConnectionError):
            run_experiment(
                model_card_uuid="mc-uuid", datasheet_uuid="ds-uuid",
                patra_server_url="http://patra.example", ckn_broker_url="broker.example:443",
                user_id="demo-user", num_images=1,
            )

    @patch("patra_toolkit.client.get_datasheet", return_value=DATASHEET_FIXTURE)
    @patch("patra_toolkit.client.get_model_card", return_value={"ai_model": {"location": "http://x", "inference_labels": []}})
    def test_run_experiment_missing_inference_labels_raises(self, mock_get_mc, mock_get_ds):
        with self.assertRaises(ValueError):
            run_experiment(
                model_card_uuid="mc-uuid", datasheet_uuid="ds-uuid",
                patra_server_url="http://patra.example", ckn_broker_url="broker.example:443",
                user_id="demo-user",
            )

    @patch("confluent_kafka.admin.AdminClient")
    @patch("confluent_kafka.Producer")
    @patch("requests.get", side_effect=_mock_requests_get)
    @patch("patra_toolkit.client.get_datasheet", return_value=DATASHEET_FIXTURE)
    @patch("patra_toolkit.client.get_model_card",
           return_value={"ai_model": {"location": "http://fake-model-host/weights.pth"}})
    def test_run_experiment_categories_param_overrides_missing_inference_labels(
            self, mock_get_mc, mock_get_ds, mock_requests_get, mock_producer_cls, mock_admin_cls):
        # Regression test: GET /modelcard/{uuid} doesn't echo back ai_model.inference_labels
        # (confirmed against a real deployment), so the model card fixture here omits it
        # entirely -- run_experiment() must still succeed when categories is passed explicitly.
        mock_admin_cls.return_value.list_topics.return_value = None

        result = run_experiment(
            model_card_uuid="mc-uuid", datasheet_uuid="ds-uuid",
            patra_server_url="http://patra.example", ckn_broker_url="broker.example:443",
            user_id="demo-user", num_images=1, categories=FIXTURE_CATEGORIES,
        )

        self.assertEqual(result["num_events_produced"], 1)
        self.assertIn(result["events"][0]["label"], FIXTURE_CATEGORIES)


if __name__ == '__main__':
    unittest.main()
