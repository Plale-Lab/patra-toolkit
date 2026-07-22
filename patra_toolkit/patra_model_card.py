import json
import logging
import os.path
from dataclasses import dataclass, field
from json import JSONEncoder
import dataclasses
from typing import List, Optional, Dict, Union

import jsonschema
import requests

from . import client
from .exceptions import PatraModelExistsError, PatraSubmissionError
# BiasAnalyzer and ExplainabilityAnalyser are imported lazily when needed

SCHEMA_JSON = os.path.join(os.path.dirname(__file__), 'schema', 'schema.json')
logging.basicConfig(level=logging.INFO)


@dataclass
class Metric:
    """
    Data class for storing metric key-value pairs.

    Args:
        key (str): The name of the metric.
        value (str): The value of the metric.
    """
    key: str
    value: str


@dataclass
class AIModel:
    """
    Represents and stores AI model metadata and its performance metrics.

    Args:
        name (str): The name of the model.
        version (str): The version identifier of the model.
        description (str): A detailed description of the model.
        owner (str): The owner of the model.
        location (str): The file path or URL where the model is stored.
        license (str): The license under which the model is distributed.
        framework (str): The framework used to build the model (e.g., TensorFlow, PyTorch).
        model_type (str): The type of model (e.g., classifier, regressor).
        test_accuracy (float): The accuracy of the model on a test dataset.
        inference_labels (List[str]): Inference labels for the AI model.
        model_structure (object): The structure of the model as a dictionary (optional).
        model_metrics (dict): A dictionary storing performance metrics for the model.

    Example:
        .. code-block:: python

            ai_model = AIModel(
                name="Model Name",
                version="1.0",
                description="Model description",
                owner="Model owner",
                location="Model location",
                license="Model license",
                framework="tensorflow",
                model_type="dnn",
                test_accuracy=0.95,
                model_structure={},
                model_metrics={"accuracy": 0.95}
            )
    """
    name: str
    version: Optional[str] = ""
    description: Optional[str] = ""
    owner: Optional[str] = ""
    location: Optional[str] = ""
    license: Optional[str] = ""
    framework: Optional[str] = None
    model_type: Optional[str] = None
    test_accuracy: Optional[float] = 0.0
    inference_labels: List[str] = field(default_factory=list)
    model_structure: Optional[object] = field(default_factory=dict)
    model_metrics: Dict[str, Union[str, int, float, bool, None]] = field(default_factory=dict)

    def add_metric(self, key: str, value) -> None:
        """
        Adds a performance metric to the model's metrics.

        Args:
            key (str): The name of the metric.
            value: The value of the metric.

        Returns:
            None
        """
        self.model_metrics[key] = value

    def remove_nulls(self, model_structure):
        """
        Recursively removes null values from the model structure.

        Args:
            model_structure (object): The model structure as a dictionary or list.

        Returns:
            object: Model structure with null values removed.
        """
        if isinstance(model_structure, dict):
            return {k: self.remove_nulls(v) for k, v in model_structure.items() if v is not None}
        elif isinstance(model_structure, list):
            return [self.remove_nulls(v) for v in model_structure if v is not None]
        return model_structure

    def populate_model_structure(self, trained_model):
        """
        Populates the `model_structure` attribute from a trained model object.

        Args:
            trained_model (object): A trained machine learning model object.

        Returns:
            None
        """
        if self.framework == 'tensorflow':
            json_structure = json.loads(trained_model.to_json())
            self.model_structure = self.remove_nulls(json_structure)
        else:
            self.model_structure = {}


@dataclass
class BiasAnalysis:
    """
    Class to store results from bias analysis.

    Args:
        demographic_parity_difference (float): The difference in demographic parity between groups.
        equal_odds_difference (float): The difference in equal odds between groups.
    """
    demographic_parity_difference: float
    equal_odds_difference: float


@dataclass
class ExplainabilityAnalysis:
    """
    Class to store explainability metrics.

    Args:
        name (str): Name of the explainability method used.
        metrics (List[Metric]): List of metrics related to explainability analysis.
    """
    name: str
    metrics: List[Metric] = field(default_factory=list)


@dataclass
class ModelCard:
    """
    Represents a documented model card containing metadata and analyses for an AI model.

    Args:
        name (str): The name of the model card.
        version (Optional[str]): The model card's version.
        short_description (Optional[str]): A brief description of the model card.
        full_description (Optional[str]): A comprehensive description of the model card.
        keywords (Optional[str]): Comma-separated keywords for searchability.
        author (Optional[str]): The model's creator or owner.
        input_type (Optional[str]): Type of input data (e.g., "Image", "Text").
        category (Optional[str]): The category of the model (e.g., "classification", "regression").
        citation (Optional[str]): Citation information for the model card.
        input_data (Optional[str]): Description of the model's input data.
        output_data (Optional[str]): Description of the model's output data.
        foundational_model (Optional[str]): Reference to any foundational model used.
        documentation (Optional[str]): URL for documentation if available.
        training_datasheet_uuid (Optional[str]): UUID of a Datasheet used to train the model.
        is_private (bool): Whether the model card is private.
        is_gated (bool): Whether the model card is gated.
        ai_model (Optional[AIModel]): Reference to an `AIModel` instance containing model details.
        bias_analysis (Optional[object]): Reference to a `BiasAnalysis` instance containing bias metrics.
        xai_analysis (Optional[object]): Reference to an `ExplainabilityAnalysis` instance with interpretability metrics.
        uuid (Optional[str]): Unique identifier for the model card, assigned upon submission.

    Example:
        .. code-block:: python

            model_card = ModelCard(
                name="Model Name",
                version="1.0",
                short_description="A brief description",
                full_description="A detailed description of the model's purpose and usage.",
                keywords="classification, AI, image processing",
                author="Author Name",
                input_type="Image",
                category="classification",
                input_data="Images of size 28x28.",
                output_data="Prediction probabilities for classes.",
                foundational_model="Base Model Reference",
                ai_model=AIModel(
                    name="Model Name",
                    version="1.0",
                    description="Detailed model description",
                    owner="Model owner",
                    location="Storage location",
                    license="MIT",
                    framework="tensorflow",
                    model_type="dnn",
                    test_accuracy=0.95,
                    model_structure={},
                    model_metrics={"accuracy": 0.95}
                )
            )
    """
    name: str
    version: Optional[str] = ""
    short_description: Optional[str] = ""
    full_description: Optional[str] = ""
    keywords: Optional[str] = ""
    author: Optional[str] = ""
    input_type: Optional[str] = ""
    category: Optional[str] = None
    citation: Optional[str] = ""
    input_data: Optional[str] = ""
    output_data: Optional[str] = ""
    foundational_model: Optional[str] = ""
    documentation: Optional[str] = ""
    training_datasheet_uuid: Optional[str] = None
    is_private: bool = False
    is_gated: bool = False
    ai_model: Optional[AIModel] = None
    bias_analysis: Optional[object] = None
    xai_analysis: Optional[object] = None
    uuid: Optional[str] = None

    def __str__(self) -> str:
        """
        Returns:
            str: A JSON-formatted string representation of the model card.
        """
        return json.dumps(self.__dict__, cls=ModelCardJSONEncoder, indent=4, separators=(',', ': '))

    def populate_bias(self,
                      dataset,
                      true_labels,
                      predicted_labels,
                      sensitive_feature_name,
                      sensitive_feature_data,
                      model) -> None:
        """
        Calculates and stores fairness metrics for the model.

        Args:
            dataset (object): The dataset used for bias analysis.
            true_labels (list): The ground truth labels.
            predicted_labels (list): The model's predictions.
            sensitive_feature_name (str): The name of the sensitive attribute.
            sensitive_feature_data (list): Values for the sensitive feature.
            model (object): The model being analyzed.
        """
        # Lazy import of fairlearn
        try:
            from .fairlearn_bias import BiasAnalyzer
        except ImportError:
            raise ImportError(
                "Fairlearn is not installed. Install it with: pip install patra-toolkit[fairness]"
            )

        bias_analyzer = BiasAnalyzer(dataset, true_labels, predicted_labels, sensitive_feature_name,
                                     sensitive_feature_data, model)
        self.bias_analysis = bias_analyzer.calculate_bias_metrics()

    def populate_xai(self,
                     train_dataset,
                     column_names,
                     model,
                     n_features: int = 10) -> None:
        """
        Computes and stores feature importance metrics for explainability.

        Args:
            train_dataset (object): Training dataset used in the analysis.
            column_names (list): Names of the features in the dataset.
            model (object): The model being explained.
            n_features (int): Number of features to analyze. Default is 10.
        """
        # Lazy import of shap
        try:
            from .shap_xai import ExplainabilityAnalyser
        except ImportError:
            raise ImportError(
                "SHAP is not installed. Install it with: pip install patra-toolkit[xai]"
            )

        xai_analyzer = ExplainabilityAnalyser(train_dataset, column_names, model)
        self.xai_analysis = xai_analyzer.calculate_xai_features(n_features)

    def validate(self) -> bool:
        """
        Validates the model card against a predefined JSON schema.

        Returns:
            bool: True if the model card is valid according to the schema, False otherwise.
        """
        mc_json_str = str(self)
        try:
            with open(SCHEMA_JSON, 'r', encoding='utf-8') as schema_file:
                schema = json.load(schema_file)
            jsonschema.validate(instance=json.loads(mc_json_str), schema=schema)
            logging.info("Model card validation successful.")
            return True
        except jsonschema.ValidationError as val_err:
            logging.error(f"Model card validation error: {val_err.message}")
            return False
        except Exception as exc:
            logging.error(f"Unexpected error during validation: {exc}")
            return False

    def authenticate(self, username: str, password: str) -> str:
        """
        Authenticates the user using TACC credentials and returns a Tapis access token.

        Args:
            username (str): TACC username.
            password (str): TACC password.

        Returns:
            str: Access token string if authentication is successful.

        Raises:
            Exception: If authentication fails.
        """
        payload = {
            "username": username,
            "password": password,
            "grant_type": "password"
        }

        response = requests.post("https://icicleai.tapis.io/v3/oauth2/tokens",
                                 headers={"Content-Type": "application/json"},
                                 data=json.dumps(payload))
        response.raise_for_status()
        token_data = response.json()

        jwt_token = token_data["result"]["access_token"]["access_token"]
        print("Authentication successful.")
        print("X-Tapis-Token:", jwt_token)
        return jwt_token

    def save(self, file_location: str) -> None:
        """
        Saves the model card as a JSON file to the specified location.

        Args:
            file_location (str): Path where the model card JSON file will be saved.
        """
        try:
            with open(file_location, 'w', encoding='utf-8') as json_file:
                json_file.write(str(self))
            logging.info(f"Model card created.")
        except IOError as io_err:
            logging.error(f"Failed to save model card: {io_err}")

    def submit(self, patra_server_url: str, token: Optional[str] = None) -> dict:
        """
        Submits the model card to the Patra server.

        Args:
            patra_server_url (str): The URL of the Patra server.
            token (Optional[str]): The X-Tapis-Token access token for authentication.

        Returns:
            dict: The server's ingest result (asset_type, asset_id, asset_uuid, organization,
            created, duplicate).

        Raises:
            PatraSubmissionError: If validation fails, the server is unreachable, or the
                server returns an error other than a duplicate.
            PatraModelExistsError: If an equivalent model card already exists on the server.

        Example:
            .. code-block:: python

                model_card.submit(
                    patra_server_url="http://localhost:8000",
                    token="access_token"
                )
        """
        if not self.validate():
            raise PatraSubmissionError("ModelCard validation failed; see log for details.")

        payload = json.loads(str(self))
        # bias_analysis/xai_analysis are kept locally for populate_bias()/populate_xai()
        # but the backend's schema doesn't persist them, so they must not be sent.
        payload.pop("bias_analysis", None)
        payload.pop("xai_analysis", None)

        result = client.submit_model_card(patra_server_url, payload, token=token)
        self.uuid = result.get("asset_uuid")
        return result

    @classmethod
    def list_model_cards(cls, server_url: str, token: Optional[str] = None, q: Optional[str] = None,
                          skip: int = 0, limit: int = 50) -> List[dict]:
        """
        Lists model cards on the Patra server.

        Args:
            server_url (str): The URL of the Patra server.
            token (Optional[str]): The X-Tapis-Token access token (includes private records if provided).
            q (Optional[str]): Optional substring search on name/author/short_description.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return (server max: 100).

        Returns:
            List[dict]: Summaries shaped like {id, uuid, name, categories, author, version,
            short_description, is_gated, is_private, updated_at}.
        """
        return client.list_model_cards(server_url, token=token, q=q, skip=skip, limit=limit)

    @classmethod
    def get_model_card(cls, server_url: str, uuid: str, token: Optional[str] = None) -> dict:
        """
        Retrieves a single model card by uuid from the Patra server.

        Args:
            server_url (str): The URL of the Patra server.
            uuid (str): The model card's uuid.
            token (Optional[str]): The X-Tapis-Token access token (required for private model cards).

        Returns:
            dict: The full model card detail, including a nested `ai_model` dict.
        """
        return client.get_model_card(server_url, uuid, token=token)


class ModelCardJSONEncoder(JSONEncoder):
    """
    Custom JSON Encoder for ModelCard-family dataclasses (ModelCard, AIModel, BiasAnalysis,
    ExplainabilityAnalysis, Metric, Datasheet, and its nested dataclasses).

    Methods:
        default: Serializes non-serializable fields.
    """

    def default(self, obj):
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return obj.__dict__
        return super().default(obj)
