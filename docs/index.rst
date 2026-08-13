==========================
Patra Model Card Toolkit
========================

The Patra Toolkit is a component of the Patra ModelCards framework designed to simplify
the process of creating and documenting AI/ML models. It provides a structured schema
that guides users in providing essential information about their models, including details
about the model's purpose, development process, and performance. The toolkit also includes
features for semi-automating the capture of key information, such as fairness and
explainability metrics, through integrated analysis tools. By reducing the manual effort
involved in creating model cards, the Patra Toolkit encourages researchers and developers
to adopt best practices for documenting their models, ultimately contributing to greater
transparency and accountability in AI/ML development.

Features
--------

1. **Encourages Accountability**
   Incorporate essential model information (metadata, dataset details, fairness,
   explainability) at training time, ensuring AI models remain transparent from
   development to deployment.

2. **Semi-Automated Capture**
   Automated *Fairness* and *Explainability* scanners compute demographic parity, equal
   odds, SHAP-based feature importances, etc., for easy integration into Model Cards.

3. **Machine-Actionable Model Cards**
   Produce a structured JSON representation for ingestion into the Patra Knowledge Base.
   Ideal for advanced queries on model selection, provenance, versioning, or auditing.

4. **Datasheets for Datasets**
   Document a dataset's DataCite-style metadata (titles, creators, subjects, and more)
   with a ``Datasheet`` and link it to a Model Card via ``training_datasheet_uuid``.

5. **Versioning & Model Relationship Tracking**
   Maintain multiple versions of a model with recognized edges (e.g., ``revisionOf``,
   ``alternateOf``) using embedding-based similarity. This ensures clear lineages and easy
   forward/backward provenance.

Getting Started
---------------

Installing Patra Model Card
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The latest version can be installed from PyPI:

.. code-block:: shell

   pip install patra-toolkit

For local installation, clone the repository and install using:

.. code-block:: shell

   pip install -e <local_git_dir>/patra_toolkit

Usage
-----

Create a Model Card
^^^^^^^^^^^^^^^^^^^

Find the descriptions of the Model Card parameters in the
``docs/schema_description.md``.

.. code-block:: python

   from patra_toolkit import ModelCard

   mc = ModelCard(
     name="UCI Adult Data Analysis model using Tensorflow",
     version="0.1",
     short_description="UCI Adult Data analysis using Tensorflow for demonstration of Patra Model Cards.",
     full_description="We have trained a ML model using the tensorflow framework to predict income for the UCI Adult Dataset. We leverage this data to run the Patra model cards to capture metadata about the model as well as fairness and explainability metrics.",
     keywords="uci adult, tensorflow, explainability, fairness, patra",
     author="Sachith Withana",
     input_type="Tabular",
     category="classification",
     foundational_model="None"
   )

   # Add Model Metadata
   mc.input_data = 'https://archive.ics.uci.edu/dataset/2/adult'
   mc.output_data = 'https://huggingface.co/Data-to-Insight-Center/UCI-Adult'

Initialize an AI/ML Model
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from patra_toolkit import AIModel

   ai_model = AIModel(
     name="UCI Adult Random Forest model",
     version="0.1",
     description="Census classification problem using Random Forest",
     owner="Sachith Withana",
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

Run Fairness and Explainability Scanners
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # To assess fairness, provide the sensitive feature, test data, labels, and predictions
   mc.populate_bias(X_test, y_test, predictions, "gender", X_test['sex'], clf)

   # To generate explainability metrics, specify the dataset, column names, model, and number of features
   mc.populate_xai(X_test, x_columns, model, top_n=10)

Validate and Save the Model Card
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Verify the model card content against the schema
   mc.validate()
   mc.save(<file_path>)

Submit
------

``submit()`` sends the Model Card's metadata to the Patra server's REST API:

- **patra_server_url (str, required)**
  Base URL of the Patra Server (e.g., ``"https://patra.example.org"``).

- **token (str, optional)**
  A valid TAPIS JWT (JSON Web Token), sent as the ``X-Tapis-Token`` header.
  - For a public Patra Server, omit this parameter.
  - For an authenticated server, supplying a valid `token` is mandatory.

.. code-block:: python

   result = mc.submit(patra_server_url=<patra_server_url>, token=<tapis_token>)
   print(mc.uuid)  # server-assigned identifier, also available as result["asset_uuid"]

``submit()`` raises ``PatraSubmissionError`` on validation failure or a server/network
error, and ``PatraModelExistsError`` if an equivalent model card (same name, version,
author, and short description) already exists on the server.

Building a Datasheet
---------------------

A ``Datasheet`` documents a dataset and submits the same way a Model Card does:

.. code-block:: python

   from patra_toolkit import Datasheet

   ds = Datasheet(publication_year=2025, version="1.0")
   ds.add_title("UCI Adult Dataset")
   ds.add_creator("Becker, B.")

   ds.submit(patra_server_url=<patra_server_url>, token=<tapis_token>)

   mc = ModelCard(name="UCI_Adult_Model", training_datasheet_uuid=ds.uuid)

Listing & Retrieving Model Cards and Datasheets
-------------------------------------------------

.. code-block:: python

   from patra_toolkit import ModelCard, Datasheet

   ModelCard.list_model_cards(server_url=<patra_server_url>)
   ModelCard.get_model_card(server_url=<patra_server_url>, uuid=<model_card_uuid>)

   Datasheet.list_datasheets(server_url=<patra_server_url>)
   Datasheet.get_datasheet(server_url=<patra_server_url>, uuid=<datasheet_uuid>)

Pass ``token=<tapis_token>`` to include private records in list/get results.

Examples
--------

Explore the following example notebooks and model cards to learn more about how to use
the Patra Model Card Toolkit:
`Notebook Example <./examples/notebooks/GettingStarted.ipynb>`_,
`Model Card Example <./examples/model_cards/tesorflow_adult_nn_MC.json>`_

License
-------

The Patra Model Card toolkit is developed by Plale Lab at The University of Oregon and
distributed under the BSD 3-Clause License. See ``LICENSE`` for more details.

Acknowledgements
----------------

This research is funded in part through the National Science Foundation under award
``#2112606``, AI Institute for Intelligent CyberInfrastructure with Computational
Learning in the Environment (ICICLE), and in part through Plale Lab at The University
of Oregon.

Reference
---------

S. Withana and B. Plale, "Patra ModelCards: AI/ML Accountability in the Edge-Cloud
Continuum," 2024 IEEE 20th International Conference on e-Science (e-Science), Osaka,
Japan, 2024, pp. 1-10, doi: 10.1109/e-Science62913.2024.10678710.