import unittest

from getgauge.python import data_store
from unittest.mock import Mock

from gauge_api_steps.api_steps import opener_key, beforescenario


class TestApiSteps(unittest.TestCase):

    def setUp(self):
        data_store.scenario.clear()
        self.app_context = Mock()

    def test_beforescenario(self):
        beforescenario(self.app_context)
        self.assertIsNotNone(data_store.scenario[opener_key])
