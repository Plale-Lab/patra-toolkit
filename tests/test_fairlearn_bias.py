import unittest

from patra_toolkit.fairlearn_bias import BiasAnalyzer


class TestBiasAnalyzer(unittest.TestCase):
    """These use real fairlearn calls against small, hand-verified fixed arrays -- zero
    coverage before this meant the actual math had never been checked.
    """

    def test_fair_predictions_yield_near_zero_metrics(self):
        # Identical prediction pattern in both groups: same per-group TPR/FPR and same
        # positive-prediction rate, so both metrics should be exactly 0.
        true_labels = [1, 0, 1, 0, 1, 0, 1, 0]
        predicted_labels = [1, 0, 1, 0, 1, 0, 1, 0]
        sensitive = ["A", "A", "A", "A", "B", "B", "B", "B"]

        analyzer = BiasAnalyzer(
            dataset=None,
            true_labels=true_labels,
            predicted_labels=predicted_labels,
            sensitive_feature_name="group",
            sensitive_feature_data=sensitive,
            model=None,
        )
        result = analyzer.calculate_bias_metrics()

        self.assertEqual(set(result.keys()), {"demographic_parity_diff", "equal_odds_difference"})
        self.assertAlmostEqual(result["demographic_parity_diff"], 0.0)
        self.assertAlmostEqual(result["equal_odds_difference"], 0.0)

    def test_biased_predictions_yield_nonzero_metrics(self):
        # Group A predicts perfectly; group B always predicts positive regardless of the
        # true label, so both demographic parity and equalized odds should be maximally
        # unfair -- worked out by hand and confirmed against a real fairlearn run.
        true_labels = [1, 0, 1, 0, 1, 0, 1, 0]
        predicted_labels = [1, 0, 1, 0, 1, 1, 1, 1]
        sensitive = ["A", "A", "A", "A", "B", "B", "B", "B"]

        analyzer = BiasAnalyzer(
            dataset=None,
            true_labels=true_labels,
            predicted_labels=predicted_labels,
            sensitive_feature_name="group",
            sensitive_feature_data=sensitive,
            model=None,
        )
        result = analyzer.calculate_bias_metrics()

        self.assertAlmostEqual(result["demographic_parity_diff"], 0.5)
        self.assertAlmostEqual(result["equal_odds_difference"], 1.0)


if __name__ == "__main__":
    unittest.main()
