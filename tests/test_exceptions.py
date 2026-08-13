import unittest

from patra_toolkit.exceptions import (
    PatraDatasheetExistsError,
    PatraModelExistsError,
    PatraSubmissionError,
)


class TestExceptions(unittest.TestCase):

    def test_patra_submission_error_message(self):
        exc = PatraSubmissionError("submission failed")
        self.assertEqual(str(exc), "submission failed")
        self.assertIsInstance(exc, Exception)

    def test_patra_model_exists_error_message(self):
        exc = PatraModelExistsError("model already exists")
        self.assertEqual(str(exc), "model already exists")
        self.assertIsInstance(exc, Exception)

    def test_patra_datasheet_exists_error_message(self):
        exc = PatraDatasheetExistsError("datasheet already exists")
        self.assertEqual(str(exc), "datasheet already exists")
        self.assertIsInstance(exc, Exception)

    def test_exceptions_are_distinct_types(self):
        self.assertFalse(issubclass(PatraModelExistsError, PatraDatasheetExistsError))
        self.assertFalse(issubclass(PatraDatasheetExistsError, PatraModelExistsError))
        self.assertFalse(issubclass(PatraSubmissionError, PatraModelExistsError))
        self.assertFalse(issubclass(PatraSubmissionError, PatraDatasheetExistsError))

    def test_model_exists_error_not_caught_by_datasheet_exists_except(self):
        with self.assertRaises(PatraModelExistsError):
            try:
                raise PatraModelExistsError("model exists")
            except PatraDatasheetExistsError:
                self.fail("PatraModelExistsError should not be caught as PatraDatasheetExistsError")

    def test_datasheet_exists_error_not_caught_by_model_exists_except(self):
        with self.assertRaises(PatraDatasheetExistsError):
            try:
                raise PatraDatasheetExistsError("datasheet exists")
            except PatraModelExistsError:
                self.fail("PatraDatasheetExistsError should not be caught as PatraModelExistsError")


if __name__ == "__main__":
    unittest.main()
