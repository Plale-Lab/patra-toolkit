import builtins
import unittest
import unittest.mock

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from patra_toolkit import ModelCard


def _make_dataset_and_model():
    rng = np.random.RandomState(0)
    dataset = pd.DataFrame(
        {
            "strong feature": rng.randn(50) * 5,
            "weak_feature": rng.randn(50) * 0.01,
        }
    )
    labels = (dataset["strong feature"] > 0).astype(int)
    model = LogisticRegression().fit(dataset, labels)
    predictions = model.predict(dataset)
    return dataset, labels, predictions, model


class TestPopulateBiasXaiIntegration(unittest.TestCase):

    def test_populate_bias_end_to_end(self):
        dataset, labels, predictions, model = _make_dataset_and_model()
        mc = ModelCard(name="TestModel")

        mc.populate_bias(
            dataset=dataset,
            true_labels=labels,
            predicted_labels=predictions,
            sensitive_feature_name="weak_feature",
            sensitive_feature_data=dataset["weak_feature"],
            model=model,
        )

        self.assertIsNotNone(mc.bias_analysis)
        self.assertEqual(
            set(mc.bias_analysis.keys()), {"demographic_parity_diff", "equal_odds_difference"}
        )

    def test_populate_xai_end_to_end(self):
        dataset, _labels, _predictions, model = _make_dataset_and_model()
        mc = ModelCard(name="TestModel")

        mc.populate_xai(dataset, list(dataset.columns), model, n_features=2)

        self.assertIsNotNone(mc.xai_analysis)
        self.assertIn("strong_feature", mc.xai_analysis)

    def test_populate_bias_import_error_raises_actionable_message(self):
        mc = ModelCard(name="TestModel")
        real_import = builtins.__import__

        def blocking_import(name, globals=None, locals=None, fromlist=(), level=0):
            # `from .fairlearn_bias import BiasAnalyzer` calls __import__ with the bare
            # relative name "fairlearn_bias" (level=1), not a dotted "patra_toolkit.fairlearn_bias"
            # -- verified empirically, since assuming the dotted form silently never matches.
            if name == "fairlearn_bias" and level == 1:
                raise ImportError("simulated: fairlearn not installed")
            return real_import(name, globals, locals, fromlist, level)

        with unittest.mock.patch("builtins.__import__", side_effect=blocking_import):
            with self.assertRaises(ImportError) as ctx:
                mc.populate_bias(
                    dataset=None,
                    true_labels=[1, 0],
                    predicted_labels=[1, 0],
                    sensitive_feature_name="x",
                    sensitive_feature_data=[0, 1],
                    model=None,
                )
        self.assertIn("pip install patra-toolkit[fairness]", str(ctx.exception))

    def test_populate_xai_import_error_raises_actionable_message(self):
        mc = ModelCard(name="TestModel")
        real_import = builtins.__import__

        def blocking_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "shap_xai" and level == 1:
                raise ImportError("simulated: shap not installed")
            return real_import(name, globals, locals, fromlist, level)

        with unittest.mock.patch("builtins.__import__", side_effect=blocking_import):
            with self.assertRaises(ImportError) as ctx:
                mc.populate_xai(None, [], None)
        self.assertIn("pip install patra-toolkit[xai]", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
