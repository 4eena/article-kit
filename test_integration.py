import unittest
from article_generator import generate
from evidence_audit import audit

class IntegrationTest(unittest.TestCase):
    def test_sample_monitor_evidence_pipeline(self):
        # Synthetic monitoring code for the evidence pipeline.
        src = "def read_sensor():\n    return \"online\"\n\ndef send_alert():\n    pass\n\ndef main():\n    current = read_sensor()\n"
        evidence = {'repository': 'https://github.com/example-owner/sample-monitor', 'branch': 'main', 'files': [{'path': 'monitor.py', 'url': 'https://github.com/example-owner/sample-monitor/blob/main/monitor.py', 'content': src}]}
        article = generate(evidence)
        report = audit(evidence, article)
        self.assertTrue(report['ok'], report)
        self.assertEqual(report['verified_files'], 1)
        for name in ('read_sensor', 'send_alert', 'main'):
            self.assertIn(name + '()', article)
        self.assertNotIn('<!--', article)
        self.assertIn('未検証', article)

if __name__ == '__main__': unittest.main()
