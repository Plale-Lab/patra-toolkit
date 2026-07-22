
class PatraSubmissionError(Exception):
    """Exception raised when submitting a ModelCard or Datasheet to the Patra server fails."""
    def __init__(self, message):
        super().__init__(message)

class PatraModelExistsError(Exception):
    """Exception raised when an equivalent model card already exists on the Patra server."""
    def __init__(self, message):
        super().__init__(message)

class PatraDatasheetExistsError(Exception):
    """Exception raised when an equivalent datasheet already exists on the Patra server."""
    def __init__(self, message):
        super().__init__(message)
