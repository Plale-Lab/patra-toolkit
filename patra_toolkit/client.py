"""
Internal HTTP client for the Patra REST server (rest_server, FastAPI + PostgreSQL).

Not part of the public API — ModelCard and Datasheet call into this module
internally. No client object is exposed to end users.
"""
import logging
from typing import Any, Dict, List, Optional

import requests

from .exceptions import PatraDatasheetExistsError, PatraModelExistsError, PatraSubmissionError

DEFAULT_TIMEOUT = 30


def _headers(token: Optional[str]) -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Tapis-Token"] = token
    return headers


def _extract_detail(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text
    return str(data.get("detail", response.text))


def _request(method: str, url: str, *, token: Optional[str] = None,
             params: Optional[dict] = None, json_body: Optional[dict] = None) -> requests.Response:
    try:
        return requests.request(method, url, headers=_headers(token), params=params,
                                 json=json_body, timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise PatraSubmissionError(f"Failed to reach Patra server at {url}: {exc}") from exc


def _raise_for_read_status(response: requests.Response, what: str) -> None:
    if not response.ok:
        raise PatraSubmissionError(f"Failed to {what} ({response.status_code}): {_extract_detail(response)}")


def _raise_for_ingest_status(response: requests.Response, asset_label: str) -> None:
    if response.status_code == 409:
        detail = _extract_detail(response)
        if asset_label == "model card":
            raise PatraModelExistsError(detail)
        raise PatraDatasheetExistsError(detail)
    if not response.ok:
        raise PatraSubmissionError(
            f"{asset_label} submission failed ({response.status_code}): {_extract_detail(response)}"
        )


# ---- model cards ----

def list_model_cards(server_url: str, token: Optional[str] = None, q: Optional[str] = None,
                      skip: int = 0, limit: int = 50) -> List[dict]:
    params: Dict[str, Any] = {"skip": skip, "limit": limit}
    if q:
        params["q"] = q
    resp = _request("GET", f"{server_url.rstrip('/')}/modelcards", token=token, params=params)
    _raise_for_read_status(resp, "list model cards")
    return resp.json()


def get_model_card(server_url: str, uuid: str, token: Optional[str] = None) -> dict:
    resp = _request("GET", f"{server_url.rstrip('/')}/modelcard/{uuid}", token=token)
    _raise_for_read_status(resp, f"get model card {uuid}")
    return resp.json()


def submit_model_card(server_url: str, payload: dict, token: Optional[str] = None) -> dict:
    resp = _request("POST", f"{server_url.rstrip('/')}/v1/assets/model-cards", token=token, json_body=payload)
    _raise_for_ingest_status(resp, "model card")
    logging.info("Model card submitted successfully.")
    return resp.json()


# ---- datasheets ----

def list_datasheets(server_url: str, token: Optional[str] = None, q: Optional[str] = None,
                     skip: int = 0, limit: int = 50) -> List[dict]:
    params: Dict[str, Any] = {"skip": skip, "limit": limit}
    if q:
        params["q"] = q
    resp = _request("GET", f"{server_url.rstrip('/')}/datasheets", token=token, params=params)
    _raise_for_read_status(resp, "list datasheets")
    return resp.json()


def get_datasheet(server_url: str, uuid: str, token: Optional[str] = None) -> dict:
    resp = _request("GET", f"{server_url.rstrip('/')}/datasheet/{uuid}", token=token)
    _raise_for_read_status(resp, f"get datasheet {uuid}")
    return resp.json()


def submit_datasheet(server_url: str, payload: dict, token: Optional[str] = None) -> dict:
    resp = _request("POST", f"{server_url.rstrip('/')}/v1/assets/datasheets", token=token, json_body=payload)
    _raise_for_ingest_status(resp, "datasheet")
    logging.info("Datasheet submitted successfully.")
    return resp.json()
