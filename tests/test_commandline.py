import unittest
from i17on.__main__ import execute

class CommandlineTest(unittest.TestCase):

    def test_basic_use(self):
        output = execute('{foo:hello} world', ['foo'])
        self.assertEqual(output, 'hello world')
        output = execute('{foo:hello} world')
        self.assertEqual(output, 'world')