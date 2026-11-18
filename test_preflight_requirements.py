import unittest
from preflight import node_major, MIN_NODE_MAJOR

class DependencyChecks(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(node_major('v22.16.0'), 22)
        self.assertEqual(node_major('26.13.1'), 26)
        self.assertIsNone(node_major('vunknown'))
        self.assertIsNone(node_major('v22.16.0-extra'))
    def test_required_major(self):
        self.assertEqual(MIN_NODE_MAJOR, 22)
