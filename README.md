<div align="center">

 <img src="docs/logo.png" alt="Patra Toolkit Logo" width="300"/>

# Patra Model Cards Toolkit

[![Documentation Status](https://img.shields.io/badge/docs-latest-blue.svg)](https://patra-toolkit.readthedocs.io/en/latest/)
[![Build Status](https://github.com/Plale-Lab/patra-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Plale-Lab/patra-toolkit/actions)
[![PyPI version](https://badge.fury.io/py/patra-toolkit.svg)](https://pypi.org/project/patra-toolkit/)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Example Notebook](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Plale-Lab/patra-toolkit/blob/main/examples/notebooks/GettingStarted.ipynb)

</div>

The Patra Toolkit is a component of the Patra AI Cards framework designed to simplify the process of creating and documenting AI/ML models. It provides a structured schema that guides users in providing essential information about their models, including details about the model's purpose, development process, and performance. The toolkit also includes features for semi-automating the capture of key information, such as fairness and explainability metrics, through integrated analysis tools. By reducing the manual effort involved in creating model cards, the Patra Toolkit encourages researchers and developers to adopt best practices for documenting their models, ultimately contributing to greater transparency and accountability in AI/ML development.

**Tags:** CI4AI, PADI

For guidance on what Tutorials, How-To Guides, and Explanation content covers, see [Diátaxis](https://diataxis.fr/).

### License

The **Patra Model Cards Toolkit** is copyrighted by **Plale Lab at The University of Oregon** and distributed under the **BSD 3-Clause License**. See the `LICENSE` file for more details.

## References

- [Documentation](https://patra-toolkit.readthedocs.io/en/latest/)
- [Schema descriptions](./docs/source/schema_description.md)
- [Example notebook](./examples/notebooks/GettingStarted.ipynb) and [example ModelCard](./examples/model_cards/tesorflow_adult_nn_MC.json)
- [Patra Knowledge Base server](https://github.com/Plale-Lab/patra-knowledge-base)

## Acknowledgements

This work has been funded by grants from the National Science Foundation, and in part through Plale Lab at The University of Oregon.

*National Science Foundation (NSF) funded AI institute for Intelligent Cyberinfrastructure with Computational Learning in the Environment (ICICLE) (OAC 2112606)*

## Issue reporting

Report issues via [GitHub Issues](https://github.com/Plale-Lab/patra-toolkit/issues).

---

# Tutorials

### Building a Patra Model Card

We start with essential metadata like name, version, short description, and so on.

Find the descriptions of the Model Card parameters in the [schema descriptions document](./docs/source/schema_description.md).

```python
from patra_toolkit import ModelCard

mc = ModelCard(
  name="UCI_Adult_Model",
  version="1.0",
  short_description="UCI Adult Data analysis using Tensorflow for demonstration of Patra Model Cards.",
  full_description="We have trained a ML model using the tensorflow framework to predict income for the UCI Adult Dataset. We leverage this data to run the Patra model cards to capture metadata about the model as well as fairness and explainability metrics.",
  keywords="uci adult, tensorflow, explainability, fairness, patra",
  author="0009-0009-9817-7042",
  input_type="Tabular",
  category="classification",
  foundational_model="None",
  citation="Becker, B. & Kohavi, R. (1996). Adult [Dataset]. UCI."
)

# Add Model Metadata
mc.input_data = 'https://archive.ics.uci.edu/dataset/2/adult'
mc.output_data = 'https://huggingface.co/patra-iu/neelk-uci_adult_model-1.0'
```

### Initialize an AI/ML Model
Here we describe the model's ownership, license, performance metrics, etc.

```python
from patra_toolkit import AIModel

ai_model = AIModel(
  name="Random Forest",
  version="0.1",
  description="Census classification problem using Random Forest",
  owner="neelk",
  location="https://github.iu.edu/swithana/mcwork/randomforest/adult_model.pkl",
  license="BSD-3 Clause",
  framework="sklearn",
  model_type="random_forest",
  test_accuracy=accuracy
)

# Populate Model Structure
ai_model.populate_model_structure(trained_model)
mc.ai_model = ai_model

# Add Custom Metrics
ai_model.add_metric("Test loss", loss)
ai_model.add_metric("Epochs", 100)
ai_model.add_metric("Batch Size", 32)
ai_model.add_metric("Optimizer", "Adam")
ai_model.add_metric("Learning Rate", 0.0001)
ai_model.add_metric("Input Shape", "(26048, 100)")
```

### Run Fairness and Explainability Scanners

Patra provides the `demographic_parity_difference` (the difference in the probability of a positive outcome between two groups) and `equalized_odds_difference` (the difference in true positive rates between two groups) using the `fairlearn` library. The explainability metrics are computed using the `shap` library.

```python
# To assess fairness, provide the sensitive feature, test data, labels, and predictions
mc.populate_bias(X_test, y_test, predictions, "gender", X_test['sex'], clf)

# To generate explainability metrics, specify the dataset, column names, model, and number of features
mc.populate_xai(X_test, x_columns, model, top_n=10)
```

The Model Card is validated against the schema to ensure it meets the required structure and content. After validation, you can save the Model Card to a file in JSON format. Only the `name` field is required — every other field is optional.

```python
# Verify the model card content against the schema
mc.validate()
mc.save(<file_path>)
```

### Submit

The `submit()` method submits the Model Card's metadata to a [Patra server](https://github.com/Plale-Lab/patra-knowledge-base).

```python
result = mc.submit(patra_server_url=<patra_server_url>)
print(mc.uuid)  # the server-assigned identifier, also available as result["asset_uuid"]
```

`submit()` raises `PatraSubmissionError` on validation failure or a server/network error, and `PatraModelExistsError` if an equivalent model card (same name, version, author, and short description) already exists on the server.

#### Hosted Patra servers (Tapis Pods)

Unless you are running Patra locally, point `patra_server_url` at the hosted deployment in the
ICICLE Tapis tenant:

| Service | URL |
| ------- | --- |
| REST API (stable) | `https://patrabackend.pods.icicleai.tapis.io` |
| REST API (dev) | `https://patrabackend-dev.pods.icicleai.tapis.io` |
| Patra UI | `https://patra.pods.icicleai.tapis.io` |
| Tapis tenant | `https://icicleai.tapis.io` |

```python
PATRA_URL = "https://patrabackend.pods.icicleai.tapis.io"

result = mc.submit(patra_server_url=PATRA_URL, token=tapis_token)
ModelCard.list_model_cards(server_url=PATRA_URL)
```

Submitted cards appear in the UI at `https://patra.pods.icicleai.tapis.io`. The stable and dev
backends share one database, so a submission to either is a submission to production.

### [Optional] TAPIS Authentication

Patra servers hosted as TAPIS pods require authentication using a JWT (JSON Web Token) for secure access. To generate this token, you must authenticate with your TACC credentials. If you do not already have a TACC account, you can create one at [https://accounts.tacc.utexas.edu/begin](https://accounts.tacc.utexas.edu/begin). Use the Patra `authenticate()` method to obtain an access token for TAPIS-hosted Patra servers:

```python
from patra_toolkit import ModelCard
mc = ModelCard(...)
tapis_token = mc.authenticate(username="<your_tacc_username>", password="<your_tacc_password>")

mc.submit(
    patra_server_url="https://patrabackend.pods.icicleai.tapis.io",
    token=tapis_token
)
```

`authenticate()` requests the token from the ICICLE tenant's OAuth2 endpoint
(`https://icicleai.tapis.io/v3/oauth2/tokens`). Reads of public records work without a token;
writes and private records require one.

### Building a Datasheet

A `Datasheet` documents a dataset (title, creators, subjects, and other DataCite-style metadata) and submits the same way a Model Card does — an alternative to filling in the same fields through the Patra UI. Attach a datasheet's `uuid` to a Model Card's `training_datasheet_uuid` to record what a model was trained on.

```python
from patra_toolkit import Datasheet

ds = Datasheet(publication_year=2025, version="1.0")
ds.add_title("UCI Adult Dataset")
ds.add_creator("Becker, B.")
ds.add_creator("Kohavi, R.")
ds.add_description("Predict whether income exceeds $50K/yr based on census data.", "Abstract")

ds.submit(patra_server_url=<patra_server_url>)
print(ds.uuid)

mc = ModelCard(name="UCI_Adult_Model", training_datasheet_uuid=ds.uuid)
```

### Listing & Retrieving Model Cards and Datasheets

```python
from patra_toolkit import ModelCard, Datasheet

# List returns summaries (uuid, name/title, and other summary fields)
ModelCard.list_model_cards(server_url=<patra_server_url>)
Datasheet.list_datasheets(server_url=<patra_server_url>)

# Get returns the full record for a single uuid
ModelCard.get_model_card(server_url=<patra_server_url>, uuid=<model_card_uuid>)
Datasheet.get_datasheet(server_url=<patra_server_url>, uuid=<datasheet_uuid>)
```

Pass `token=<tapis_token>` to any of the above to include private records in list/get results.

---

# How-To Guides

### Installation

#### From Pip (Recommended)
```shell
pip install patra-toolkit
```

#### From GitHub (for the latest development version)
```shell
pip install git+https://github.com/Plale-Lab/patra-toolkit
```

---

# Explanation

The Patra Toolkit embeds transparency and governance directly into the training workflow. Integrated scanners collect essential metadata—data sources, fairness metrics, and explainability insights—during model training and then generate a machine‑actionable JSON model card. These cards plug into the Patra Knowledge Base for rich queries on provenance, version history, and auditing. Flexible back‑ends publish models and artifacts to repositories such as Hugging Face or GitHub, automatically recording lineage links to trace every model’s evolution.
