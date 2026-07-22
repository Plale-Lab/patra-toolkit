## [0.3.0]

> Migrates the toolkit from the legacy Neo4j-backed Patra server to the new PostgreSQL/FastAPI
> backend, and adds a `Datasheet` class for submitting dataset metadata.

### Added
- `Datasheet` class for building and submitting DataCite-style dataset metadata, with
  `add_creator()`/`add_title()`/`add_subject()`/`add_description()`/`add_date()`/
  `add_funding_reference()`/`set_publisher()` convenience builders.
- `ModelCard.list_model_cards()`/`ModelCard.get_model_card()` and
  `Datasheet.list_datasheets()`/`Datasheet.get_datasheet()` classmethods for querying the
  Patra server.
- `ModelCard` fields `documentation`, `training_datasheet_uuid`, `is_private`, `is_gated`.
- `PatraDatasheetExistsError` exception.

### Changed
- `ModelCard.submit()`/`Datasheet.submit()` now target the new backend's
  `/v1/assets/model-cards` and `/v1/assets/datasheets` endpoints instead of the legacy
  `/upload_mc`; `submit()` now raises (`PatraSubmissionError`, `PatraModelExistsError`,
  `PatraDatasheetExistsError`) instead of logging and returning `None`.
- `ModelCard`/`AIModel` constructors now only require `name` — every other field is optional.
- `AIModel.metrics` renamed to `model_metrics`; `AIModel.inference_labels` changed from a
  string to a list of strings.
- `ModelCard.id` (a `<author>-<name>-<version>` PID string) replaced by `ModelCard.uuid`.

### Removed / Deprecated
- `ModelCard.populate_requirements()` and the `model_requirements` field — the new backend
  accepts but never persists this field.
- `submit()`'s `model`/`file_format`/`model_store`/`inference_labels`/`artifacts` kwargs (the
  Hugging Face/GitHub model-upload flow, since the credential-broker endpoints it relied on
  don't exist on the new backend). `model_store.py` remains in the codebase but is no longer
  called from `submit()`.

---

## [0.2.0]

> Introduces modular model uploads, richer logging, and a more resilient `submit()` workflow.

### Added
- Models in Patra are accessed by querying their model cards, which provide metadata and references. The actual model files are stored and managed externally.
- Patra includes an interoperability layer that enables seamless integration with external platforms such as Hugging Face and GitHub, allowing users to upload, retrieve, or link models across these services.

### Changed
- Upgraded schema validation and error messages for clarity.

### Fixed
- Robust schema validation messages with detailed logging of JSONSchema errors.

### Removed / Deprecated
- None.

---

## [0.1.1]

- First public release featuring structured metadata, automated scanners for fairness/explainability, schema validation, Patra Knowledge Base integration, and command-line tools for model submission and management.
