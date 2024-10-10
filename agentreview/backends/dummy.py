from agentreview.config import Configurable


class Dummy(Configurable):
    """A dummy backend does not make any API calls. We use it for extracting paper contents in PaperExtractor
    and also for testing."""
    stateful = False
    type_name = "dummy"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def reset(self):
        pass