import unittest
import os
from stateful_data_processor.file_rw import JsonFileRW

class TestJsonFileRW(unittest.TestCase):
    def setUp(self):
        self.file_name = "test.json"
        self.file_rw = JsonFileRW(self.file_name)

    def test_read(self):
        data = self.file_rw.read()
        self.assertEqual(data, {})

    def test_write(self):
        data = {"key": "value"}
        self.file_rw.write(data)
        read_data = self.file_rw.read()
        self.assertEqual(data, read_data)

    def tearDown(self):
        if os.path.exists(self.file_name):
            os.remove(self.file_name)
