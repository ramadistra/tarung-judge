from django.test import TestCase

from .models import Attempt
from . import judger

class JudgerTestCase(TestCase):
    def test_parse_response(self):
        # Parse normal output.
        output = "1.in\nHello\nWorld\n2.in\nWorld\n"
        self.assertEqual(judger.parse_stdout(output), ["Hello\nWorld", "World"])

        # Parse malicious output.
        output = "1.in\nHello\nWorld\n2.in\nWorld\n2.in\nWorld\n"
        self.assertEqual(judger.parse_stdout(output), ["Hello\nWorld", "World\n2.in\nWorld"])

    def test_match(self):
        # Correct output.
        correct = Attempt.ACCEPTED
        expected_out = ['Hello\nWorld', 'World\nHello']
        response = {
            'stdout': '1.in\nHello\nWorld\n2.in\nWorld\nHello\n',
            'status': 'OK'
        }
        self.assertEqual(judger.match(expected_out, response), ([correct, correct], True))

        # Wrong output.
        wrong = Attempt.WRONG_ANSWER
        expected_out = ['Hello\nWorld', 'World\nHello']
        response = {
            'stdout': '1.in\nHello\nWorld\n2.in\nWorld\n2.in\nWorld\n',
            'status': 'OK'
        }
        self.assertEqual(judger.match(expected_out, response), ([correct, wrong], False))
