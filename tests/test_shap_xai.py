import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from patra_toolkit.shap_xai import ExplainabilityAnalyser


def _make_dataset_and_model():
    """A LogisticRegression with one clearly dominant feature, so shap.Explainer resolves to
    a deterministic linear/exact explainer and the importance ranking is stable across runs
    (no sampling-based explainer, no flakiness).
    """
    rng = np.random.RandomState(0)
    dataset = pd.DataFrame(
        {
            "strong feature": rng.randn(50) * 5,
            "weak_feature": rng.randn(50) * 0.01,
            "noise-col": rng.randn(50) * 0.01,
        }
    )
    labels = (dataset["strong feature"] > 0).astype(int)
    model = LogisticRegression().fit(dataset, labels)
    return dataset, model


class TestExplainabilityAnalyser(unittest.TestCase):
    """calculate_xai_features() had zero coverage before this -- these use a real
    shap.Explainer against a small, deterministic fixture rather than mocking shap itself.
    """

    def test_returns_at_most_n_features_sorted_by_importance(self):
        dataset, model = _make_dataset_and_model()
        analyzer = ExplainabilityAnalyser(dataset, list(dataset.columns), model)

        result = analyzer.calculate_xai_features(n_features=2)

        self.assertEqual(len(result), 2)
        # The dominant feature must be the top-ranked one.
        self.assertIn("strong_feature", result)
        self.assertGreater(result["strong_feature"], result["weak_feature"])

    def test_column_names_are_sanitized(self):
        dataset, model = _make_dataset_and_model()
        analyzer = ExplainabilityAnalyser(dataset, list(dataset.columns), model)

        result = analyzer.calculate_xai_features(n_features=10)

        # "strong feature" -> "strong_feature", "noise-col" -> "noise_col"
        self.assertIn("strong_feature", result)
        self.assertIn("noise_col", result)
        self.assertNotIn("strong feature", result)
        self.assertNotIn("noise-col", result)

    def test_values_are_floats(self):
        dataset, model = _make_dataset_and_model()
        analyzer = ExplainabilityAnalyser(dataset, list(dataset.columns), model)

        result = analyzer.calculate_xai_features(n_features=10)

        for value in result.values():
            self.assertIsInstance(value, float)

    def test_n_features_larger_than_columns_returns_all_columns(self):
        dataset, model = _make_dataset_and_model()
        analyzer = ExplainabilityAnalyser(dataset, list(dataset.columns), model)

        result = analyzer.calculate_xai_features(n_features=10)

        self.assertEqual(len(result), 3)

    def test_pytorch_true_uses_deep_explainer(self):
        # A real PyTorch + SHAP DeepExplainer integration test is disproportionate for this
        # pass -- mock DeepExplainer itself and just confirm the code path selects it.
        dataset, model = _make_dataset_and_model()
        analyzer = ExplainabilityAnalyser(dataset, list(dataset.columns), model)

        fake_explanation = MagicMock()
        fake_explanation.values = np.zeros((len(dataset), len(dataset.columns)))
        fake_explainer_instance = MagicMock(return_value=fake_explanation)

        with patch("patra_toolkit.shap_xai.shap.DeepExplainer", return_value=fake_explainer_instance) as mock_deep, \
             patch("patra_toolkit.shap_xai.shap.Explainer") as mock_default:
            analyzer.calculate_xai_features(n_features=3, pytorch=True)

        mock_deep.assert_called_once_with(model, dataset)
        mock_default.assert_not_called()


if __name__ == "__main__":
    unittest.main()
