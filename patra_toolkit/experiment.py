"""
Runs a small image-classification inference experiment against a Model Card + Datasheet
already registered on Patra, and streams per-image metrics to CKN (Kafka) as it goes.

Requires the optional `experiments` extra: pip install patra-toolkit[experiments]
"""
import io
import json
import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import requests

from .datasheet import Datasheet
from .patra_model_card import ModelCard

_STRING_FIELDS = [
    "domain", "device_id", "experiment_id", "user_id", "model_id", "UUID",
    "image_name", "ground_truth", "image_decision", "label", "flattened_scores",
]
_INT_FIELDS = [
    "image_count", "total_images", "total_predictions", "total_ground_truth_objects",
    "true_positives", "false_positives", "false_negatives",
]
_FLOAT_FIELDS = ["probability", "precision", "recall", "f1_score", "mean_iou", "map_50", "map_50_95"]
_TIMESTAMP_FIELDS = ["image_receiving_timestamp", "image_scoring_timestamp", "image_store_delete_time"]

# The CKN Postgres sink connector's value converter has schemas.enable=true, so bare flat
# JSON is rejected -- messages must be wrapped in a {"schema": ..., "payload": ...} envelope
# (toggle via use_schema_envelope if a given deployment's connector differs). Timestamp
# fields additionally need Kafka Connect's logical Timestamp type (epoch millis), not plain
# ISO-8601 strings, or the JDBC sink fails inserting into the timestamptz columns.
_CONNECT_SCHEMA = {
    "type": "struct",
    "optional": False,
    "name": "oracle_event",
    "fields": (
        [{"field": f, "type": "string", "optional": True} for f in _STRING_FIELDS]
        + [{"field": f, "type": "int32", "optional": True} for f in _INT_FIELDS]
        + [{"field": f, "type": "double", "optional": True} for f in _FLOAT_FIELDS]
        + [
            {"field": f, "type": "int64", "optional": True,
             "name": "org.apache.kafka.connect.data.Timestamp", "version": 1}
            for f in _TIMESTAMP_FIELDS
        ]
    ),
}


def _extract_image_base_url(datasheet: dict) -> str:
    for identifier in datasheet.get("alternate_identifiers", []):
        if identifier.get("alternate_identifier_type") == "URL":
            return identifier["alternate_identifier"].rstrip("/")
    raise ValueError(
        "Datasheet has no alternate_identifiers entry with alternate_identifier_type='URL' "
        "to use as the image source."
    )


def _download_bytes(url: str, timeout: int) -> bytes:
    resp = requests.get(url, stream=True, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def _load_model(weights_bytes: bytes):
    import torch
    import torchvision

    model = torchvision.models.mobilenet_v2(weights=None)
    model.load_state_dict(torch.load(io.BytesIO(weights_bytes), map_location="cpu"))
    model.eval()
    return model


def _classify_image(model, preprocess, image_bytes: bytes, categories: List[str],
                     top_k: int = 5) -> Tuple[str, float, list]:
    import torch
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    input_tensor = preprocess(img).unsqueeze(0)

    with torch.no_grad():
        output = model(input_tensor)
    probs = torch.nn.functional.softmax(output[0], dim=0)
    topk_prob, topk_idx = torch.topk(probs, top_k)

    top_label = categories[topk_idx[0].item()]
    top_prob = topk_prob[0].item()
    topk_scores = [
        {"label": categories[idx.item()], "probability": round(prob.item(), 4)}
        for prob, idx in zip(topk_prob, topk_idx)
    ]
    return top_label, top_prob, topk_scores


def _build_event(image_name: str, running_count: int, top_label: str, top_prob: float,
                  topk_scores: list, experiment_id: str, user_id: str, device_id: str,
                  model_id: str, domain: str = "digital-ag") -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "domain": domain,
        "device_id": device_id,
        "experiment_id": experiment_id,
        "user_id": user_id,
        "model_id": model_id,  # bare model card uuid -- no "-model" suffix needed
        "UUID": str(uuid_lib.uuid4()),  # renamed to the `uuid` column by the sink connector's transform
        "image_name": image_name,
        "ground_truth": None,  # no real label available for these photos
        "image_count": running_count,
        "image_receiving_timestamp": now,
        "image_scoring_timestamp": now,
        "image_store_delete_time": now,
        "image_decision": "Save",
        "label": top_label,
        "probability": round(float(top_prob), 7),
        "flattened_scores": json.dumps(topk_scores),
        # Illustrative placeholders only -- plain image classification has no real ground truth
        # here, unlike the camera-trap/object-detection use case these columns were designed for.
        "total_images": running_count,
        "total_predictions": 1,
        "total_ground_truth_objects": 0,
        "true_positives": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "precision": round(float(top_prob), 5),
        "recall": round(float(top_prob), 5),
        "f1_score": round(float(top_prob), 5),
        "mean_iou": 0.0,
        "map_50": 0.0,
        "map_50_95": 0.0,
    }


def _iso_to_epoch_millis(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _envelope(event: dict) -> dict:
    payload = dict(event)
    for field in _TIMESTAMP_FIELDS:
        if field in payload:
            payload[field] = _iso_to_epoch_millis(payload[field])
    return {"schema": _CONNECT_SCHEMA, "payload": payload}


def _delivery_report(err, msg) -> None:
    if err is not None:
        logging.error("Delivery failed: %s", err)
    else:
        logging.info("Produced event to '%s' [partition %s]", msg.topic(), msg.partition())


def _produce_event(producer, topic: str, event: dict, use_schema_envelope: bool) -> None:
    payload = _envelope(event) if use_schema_envelope else event
    producer.produce(topic, json.dumps(payload), callback=_delivery_report)
    producer.poll(0)


def _check_broker_reachable(ckn_broker_url: str, timeout: int = 10) -> None:
    from confluent_kafka.admin import AdminClient

    try:
        AdminClient({"bootstrap.servers": ckn_broker_url}).list_topics(timeout=timeout)
    except Exception as exc:
        raise ConnectionError(f"Could not reach CKN broker at {ckn_broker_url}: {exc}") from exc


def run_experiment(
        model_card_uuid: str,
        datasheet_uuid: str,
        patra_server_url: str,
        ckn_broker_url: str,
        user_id: str,
        device_id: str = "demo-edge-device",
        experiment_id: Optional[str] = None,
        domain: str = "digital-ag",
        num_images: int = 20,
        ckn_topic: str = "oracle-events",
        use_schema_envelope: bool = True,
        token: Optional[str] = None,
) -> dict:
    """
    Fetches a Model Card + Datasheet from Patra, downloads the referenced model and sample
    images, runs inference over them, and streams per-image metrics to CKN as they're produced.

    Args:
        model_card_uuid (str): uuid of a Model Card already submitted to Patra, with
            ai_model.location (a downloadable weights URL) and ai_model.inference_labels set.
        datasheet_uuid (str): uuid of a Datasheet already submitted to Patra, with an
            alternate_identifiers entry of type "URL" pointing at the image source.
        patra_server_url (str): base URL of the Patra server to fetch the model card/datasheet from.
        ckn_broker_url (str): CKN Kafka broker address, e.g. "cknbroker.pods.icicleai.tapis.io:443".
        user_id (str): must already be registered in the users table wherever the events land --
            there is no auto-registration and no safe default.
        device_id (str): auto-registers on first use; no setup needed.
        experiment_id (Optional[str]): auto-generated if not provided.
        domain (str): tag applied to every event; must be a domain the Patra Experiments page
            recognizes (e.g. "digital-ag").
        num_images (int): how many sample images to fetch and run inference over.
        ckn_topic (str): Kafka topic to produce to.
        use_schema_envelope (bool): whether the target Kafka Connect sink requires the
            {"schema": ..., "payload": ...} envelope. Flip to False if a given deployment's
            connector accepts bare JSON instead.
        token (Optional[str]): X-Tapis-Token, if the model card/datasheet are private.

    Returns:
        dict: summary with experiment_id, num_events_produced, the built events, and results_url.
    """
    try:
        import torch  # noqa: F401
        import torchvision  # noqa: F401
        from torchvision import transforms
        from PIL import Image  # noqa: F401
        from confluent_kafka import Producer
        from confluent_kafka.admin import AdminClient  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "torch, torchvision, pillow, and confluent-kafka are required to run inference "
            "experiments. Install them with: pip install patra-toolkit[experiments]"
        ) from exc

    logging.info("Downloading model card %s from %s", model_card_uuid, patra_server_url)
    model_card = ModelCard.get_model_card(patra_server_url, model_card_uuid, token=token)

    logging.info("Downloading data sheet %s from %s", datasheet_uuid, patra_server_url)
    datasheet = Datasheet.get_datasheet(patra_server_url, datasheet_uuid, token=token)

    model_location = model_card["ai_model"]["location"]
    categories = model_card["ai_model"].get("inference_labels") or []
    if not categories:
        raise ValueError(f"Model card {model_card_uuid} has no ai_model.inference_labels.")
    image_base_url = _extract_image_base_url(datasheet)

    logging.info("Connecting to CKN broker at %s", ckn_broker_url)
    producer = Producer({"bootstrap.servers": ckn_broker_url})
    _check_broker_reachable(ckn_broker_url)

    logging.info("Downloading model weights from %s", model_location)
    model = _load_model(_download_bytes(model_location, timeout=60))
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    if experiment_id is None:
        experiment_id = f"experiment-{uuid_lib.uuid4().hex[:8]}"

    events = []
    for i in range(num_images):
        image_name = f"{i}.jpg"
        image_bytes = _download_bytes(f"{image_base_url}/id/{i}/224/224", timeout=30)
        top_label, top_prob, topk_scores = _classify_image(model, preprocess, image_bytes, categories)

        event = _build_event(
            image_name=image_name, running_count=i + 1,
            top_label=top_label, top_prob=top_prob, topk_scores=topk_scores,
            experiment_id=experiment_id, user_id=user_id, device_id=device_id,
            model_id=model_card_uuid, domain=domain,
        )
        events.append(event)
        _produce_event(producer, ckn_topic, event, use_schema_envelope)
        logging.info("Image %d/%d processed: %s (%.3f)", i + 1, num_images, top_label, top_prob)

    producer.flush(timeout=10)
    logging.info(
        "Experiment completed: %d events streamed to CKN topic '%s' for experiment '%s'",
        len(events), ckn_topic, experiment_id,
    )

    results_url = f"{patra_server_url.rstrip('/')}/experiments/{domain}/users/{user_id}/summary"
    logging.info("View results in Patra at %s", results_url)

    return {
        "experiment_id": experiment_id,
        "model_card_uuid": model_card_uuid,
        "datasheet_uuid": datasheet_uuid,
        "user_id": user_id,
        "device_id": device_id,
        "domain": domain,
        "num_events_produced": len(events),
        "events": events,
        "ckn_topic": ckn_topic,
        "ckn_broker_url": ckn_broker_url,
        "results_url": results_url,
    }
